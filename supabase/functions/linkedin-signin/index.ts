// supabase/functions/linkedin-signin/index.ts
//
// Server-side half of "Login with LinkedIn" -- plain LinkedIn Sign-In (OIDC: openid + profile +
// email), used as a real, passwordless authentication bridge for BOTH returning members and
// brand-new ones (see handleLogin below). The client-side completion modal then collects the
// few things LinkedIn's OIDC scope can't provide (phone, city, vertical) for a brand-new member.
//
// This is a SEPARATE concern from supabase/functions/linkedin-oauth/index.ts (the member-level
// "Connect LinkedIn" / "Share to LinkedIn" posting feature, which uses w_member_social and
// writes to the linkedin_connections table). The two share the same LinkedIn Developer app and
// Client ID (86dpuqc5ufkfhp) because that's the one app Mahayukti has registered, but they use
// different registered redirect URIs and different scopes.
//
// Two actions, POST only:
//   { action: "login", code, redirect_uri }
//     The real flow (see handleLogin below): verifies LinkedIn's email_verified claim, then
//     mints a Supabase magic-link token for that email via the Admin API -- creating the
//     auth.users identity if none exists yet, or reusing the existing one.
//   { action: "userinfo", code, redirect_uri }
//     Legacy/unused by the current client -- exchanges a code for just the display profile
//     fields, no session. Left in place in case a prefill-only use ever comes back, but nothing
//     calls it right now.
//
// `redirect_uri` must exactly match what was sent to LinkedIn's /authorization endpoint
// (https://mahayukti.com/auth/linkedin-signin/callback/) and what's registered as an additional
// "Authorized redirect URL" on the LinkedIn app.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const LINKEDIN_CLIENT_ID = Deno.env.get("LINKEDIN_CLIENT_ID") ?? "86dpuqc5ufkfhp";
const LINKEDIN_CLIENT_SECRET = Deno.env.get("LINKEDIN_CLIENT_SECRET"); // same Supabase project secret as linkedin-oauth; must be set, never hardcoded here

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

// Shared by both actions below: exchange a LinkedIn authorization code for the OIDC userinfo
// claims. Factored out so the real-login path (which additionally needs email_verified) and the
// apply-prefill path (which doesn't care) don't duplicate the token exchange.
async function fetchLinkedinUserinfo(code: string, redirect_uri: string) {
  const tokenRes = await fetch("https://www.linkedin.com/oauth/v2/accessToken", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code,
      redirect_uri,
      client_id: LINKEDIN_CLIENT_ID,
      client_secret: LINKEDIN_CLIENT_SECRET!,
    }),
  });
  const tokenData = await tokenRes.json();
  if (!tokenRes.ok || !tokenData.access_token) {
    throw { status: 400, body: { error: "LinkedIn sign-in failed", detail: tokenData } };
  }
  const userinfoRes = await fetch("https://api.linkedin.com/v2/userinfo", {
    headers: { Authorization: `Bearer ${tokenData.access_token}` },
  });
  const userinfo = await userinfoRes.json();
  if (!userinfoRes.ok || !userinfo.sub) {
    throw { status: 400, body: { error: "Could not read your LinkedIn profile", detail: userinfo } };
  }
  return userinfo;
}

async function handleUserinfo(body: { code?: string; redirect_uri?: string }) {
  if (!LINKEDIN_CLIENT_SECRET) {
    return json({ error: "LINKEDIN_CLIENT_SECRET is not set on this Supabase project. Set it with: supabase secrets set LINKEDIN_CLIENT_SECRET=<rotated secret>" }, 500);
  }
  const { code, redirect_uri } = body;
  if (!code || !redirect_uri) return json({ error: "code and redirect_uri are required" }, 400);

  let userinfo;
  try {
    userinfo = await fetchLinkedinUserinfo(code, redirect_uri);
  } catch (e) {
    if (e && typeof e === "object" && "status" in e) return json((e as any).body, (e as any).status);
    throw e;
  }

  return json({
    profile: {
      name: userinfo.name ?? null,
      given_name: userinfo.given_name ?? null,
      family_name: userinfo.family_name ?? null,
      email: userinfo.email ?? null,
      headline: null, // see note at top of file — not available from the OIDC userinfo claims
      picture: userinfo.picture ?? null,
    },
  });
}

// "Login with LinkedIn" -- a real authentication bridge, not just prefill. LinkedIn (via OIDC)
// is only ever used here to PROVE the person owns a given, already-verified email address.
// Serves BOTH returning members and brand-new ones, exactly like googleAuth() on the client
// side: this always mints a Supabase magic-link token for the verified email -- Supabase's
// own generateLink creates the auth.users identity if one doesn't already exist for that email,
// or reuses the existing one if it does. Either way, no password is ever set, and the browser
// redeems the token via supabase.auth.verifyOtp({type:'magiclink'}); the client's handleSess()
// then decides what happens next (straight to the member's existing profile, or -- if no
// public.users row matches yet -- a short completion form for the missing details).
async function handleLogin(body: { code?: string; redirect_uri?: string }) {
  if (!LINKEDIN_CLIENT_SECRET) {
    return json({ error: "LINKEDIN_CLIENT_SECRET is not set on this Supabase project." }, 500);
  }
  const { code, redirect_uri } = body;
  if (!code || !redirect_uri) return json({ error: "code and redirect_uri are required" }, 400);

  let userinfo;
  try {
    userinfo = await fetchLinkedinUserinfo(code, redirect_uri);
  } catch (e) {
    if (e && typeof e === "object" && "status" in e) return json((e as any).body, (e as any).status);
    throw e;
  }

  // Trust the email only if LinkedIn itself has verified it -- a claimed-but-unverified email on
  // an OIDC identity is not proof of ownership, and this path can create a real account from it.
  if (!userinfo.email || userinfo.email_verified !== true) {
    return json({ error: "Your LinkedIn account's email isn't verified, so it can't be used to sign in. Please verify your email with LinkedIn, or use password/Google login instead." }, 400);
  }

  const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
  const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  // options.data seeds user_metadata the same way supabase.auth.signUp()'s options.data would --
  // only takes effect if this email is actually new, so it never overwrites an existing member's
  // metadata. This is what lets the client's OAuth-completion popup prefill "Full Name" for a
  // brand-new LinkedIn signup the same way it already does for Google.
  const { data: linkData, error: linkErr } = await admin.auth.admin.generateLink({
    type: "magiclink",
    email: userinfo.email,
    options: {
      data: {
        full_name: userinfo.name ?? null,
        given_name: userinfo.given_name ?? null,
        family_name: userinfo.family_name ?? null,
        picture: userinfo.picture ?? null,
      },
    },
  });
  if (linkErr || !linkData?.properties?.hashed_token) {
    return json({ error: "Could not sign you in", detail: linkErr?.message }, 500);
  }

  return json({ email: userinfo.email, token_hash: linkData.properties.hashed_token });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS_HEADERS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  try {
    if (body.action === "userinfo") return await handleUserinfo(body as { code?: string; redirect_uri?: string });
    if (body.action === "login") return await handleLogin(body as { code?: string; redirect_uri?: string });
    return json({ error: "Unknown action. Use 'userinfo' or 'login'." }, 400);
  } catch (e) {
    return json({ error: "Unhandled error", detail: String(e) }, 500);
  }
});
