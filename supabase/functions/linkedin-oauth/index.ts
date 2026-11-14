// supabase/functions/linkedin-oauth/index.ts
//
// Server-side half of "Connect LinkedIn" (individual member posting only — w_member_social).
// This is NOT the organization/brand-page feature; that needs w_organization_social, which is
// still pending a separate LinkedIn API review and must not be requested here.
//
// Why this has to be an Edge Function and not client-side JS: the authorization-code -> access
// token exchange requires the LinkedIn app's Client Secret. app.html/network.html talk to
// Supabase directly from the browser, which is fine for Supabase's anon-key + RLS model, but the
// LinkedIn Client Secret must never reach the browser. This function is the only place that holds
// it (as the LINKEDIN_CLIENT_SECRET env var, set on the Supabase project, never committed here).
//
// Two actions, both POST, both require the caller's own Supabase session JWT in the
// Authorization header (so we know which Mahayukti member this is for):
//
//   { action: "exchange", code, redirect_uri }
//     Exchanges a LinkedIn authorization code for an access token (server-side, using
//     LINKEDIN_CLIENT_SECRET), fetches the member's LinkedIn id via /v2/userinfo, and upserts
//     one row into public.linkedin_connections for this member. `redirect_uri` must exactly
//     match what was sent to LinkedIn's /authorization endpoint and what's registered on the
//     LinkedIn app (LinkedIn checks this during the exchange).
//
//   { action: "share", text }
//     Loads this member's stored access token and posts `text` to LinkedIn on their behalf via
//     the Posts API (POST https://api.linkedin.com/rest/posts), author = urn:li:person:{sub}.
//
// CSRF `state` verification for the OAuth redirect happens client-side (the callback page checks
// the `state` LinkedIn sends back against the value it stashed in sessionStorage before
// redirecting) — this function trusts that it is only ever called by that already-verified flow,
// gated by requiring a valid Mahayukti session JWT on every call.

import { createClient } from "npm:@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY")!;

const LINKEDIN_CLIENT_ID = Deno.env.get("LINKEDIN_CLIENT_ID") ?? "86dpuqc5ufkfhp";
const LINKEDIN_CLIENT_SECRET = Deno.env.get("LINKEDIN_CLIENT_SECRET"); // must be set as a Supabase project secret, never hardcoded here
const LINKEDIN_API_VERSION = Deno.env.get("LINKEDIN_API_VERSION") ?? "202505"; // Posts API Linkedin-Version header, YYYYMM — bump periodically

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

// Service-role client: used only for the DB write (upsert/read of linkedin_connections) and
// never to bypass who the caller is — that's established separately via getUser() below.
const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

async function requireUser(req: Request) {
  const authHeader = req.headers.get("Authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");
  if (!token) return null;
  // Verify the JWT against Supabase Auth using the anon key + the caller's own token — this is
  // the same check RLS would do, so we know exactly which Mahayukti member is calling.
  const userClient = createClient(SUPABASE_URL, ANON_KEY, {
    global: { headers: { Authorization: `Bearer ${token}` } },
  });
  const { data, error } = await userClient.auth.getUser();
  if (error || !data?.user) return null;
  return data.user;
}

async function handleExchange(authUserId: string, body: { code?: string; redirect_uri?: string }) {
  if (!LINKEDIN_CLIENT_SECRET) {
    return json({ error: "LINKEDIN_CLIENT_SECRET is not set on this Supabase project. Set it with: supabase secrets set LINKEDIN_CLIENT_SECRET=<rotated secret>" }, 500);
  }
  const { code, redirect_uri } = body;
  if (!code || !redirect_uri) return json({ error: "code and redirect_uri are required" }, 400);

  // 1) Exchange the authorization code for an access token.
  const tokenRes = await fetch("https://www.linkedin.com/oauth/v2/accessToken", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code,
      redirect_uri,
      client_id: LINKEDIN_CLIENT_ID,
      client_secret: LINKEDIN_CLIENT_SECRET,
    }),
  });
  const tokenData = await tokenRes.json();
  if (!tokenRes.ok || !tokenData.access_token) {
    return json({ error: "LinkedIn token exchange failed", detail: tokenData }, 400);
  }
  const { access_token, expires_in, scope } = tokenData;

  // 2) Fetch the member's LinkedIn id (sub) via OpenID userinfo, needed to build the
  //    urn:li:person:{sub} author URN the Posts API requires.
  const userinfoRes = await fetch("https://api.linkedin.com/v2/userinfo", {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  const userinfo = await userinfoRes.json();
  if (!userinfoRes.ok || !userinfo.sub) {
    return json({ error: "Could not fetch LinkedIn profile after connecting", detail: userinfo }, 400);
  }

  // 3) Store it. Service role write — RLS has no insert policy for this table on purpose; only
  // this function (holding the service role key) ever writes it.
  const tokenExpiresAt = new Date(Date.now() + (expires_in ?? 0) * 1000).toISOString();
  const { error: dbError } = await admin.from("linkedin_connections").upsert({
    auth_user_id: authUserId,
    linkedin_sub: userinfo.sub,
    access_token,
    token_expires_at: tokenExpiresAt,
    scope: scope ?? null,
    updated_at: new Date().toISOString(),
  });
  if (dbError) return json({ error: "Could not save LinkedIn connection", detail: dbError.message }, 500);

  return json({ connected: true, name: userinfo.name ?? null });
}

async function handleShare(authUserId: string, body: { text?: string }) {
  const text = (body.text || "").trim();
  if (!text) return json({ error: "text is required" }, 400);

  const { data: conn, error } = await admin
    .from("linkedin_connections")
    .select("access_token, linkedin_sub, token_expires_at")
    .eq("auth_user_id", authUserId)
    .maybeSingle();

  if (error) return json({ error: "Could not load LinkedIn connection", detail: error.message }, 500);
  if (!conn) return json({ error: "Not connected to LinkedIn. Use Connect LinkedIn first." }, 409);
  if (new Date(conn.token_expires_at).getTime() < Date.now()) {
    return json({ error: "Your LinkedIn connection has expired. Please reconnect." }, 409);
  }

  const postRes = await fetch("https://api.linkedin.com/rest/posts", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${conn.access_token}`,
      "Content-Type": "application/json",
      "X-Restli-Protocol-Version": "2.0.0",
      "Linkedin-Version": LINKEDIN_API_VERSION,
    },
    body: JSON.stringify({
      author: `urn:li:person:${conn.linkedin_sub}`,
      commentary: text,
      visibility: "PUBLIC",
      distribution: {
        feedDistribution: "MAIN_FEED",
        targetEntities: [],
        thirdPartyDistributionChannels: [],
      },
      lifecycleState: "PUBLISHED",
      isReshareDisabledByAuthor: false,
    }),
  });

  if (postRes.status !== 201) {
    const detail = await postRes.json().catch(() => ({}));
    return json({ error: "LinkedIn post failed", detail }, 400);
  }
  const postId = postRes.headers.get("x-restli-id");
  return json({ posted: true, postId });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS_HEADERS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  const user = await requireUser(req);
  if (!user) return json({ error: "Not authenticated" }, 401);

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  try {
    if (body.action === "exchange") return await handleExchange(user.id, body as { code?: string; redirect_uri?: string });
    if (body.action === "share") return await handleShare(user.id, body as { text?: string });
    return json({ error: "Unknown action. Use 'exchange' or 'share'." }, 400);
  } catch (e) {
    return json({ error: "Unhandled error", detail: String(e) }, 500);
  }
});
