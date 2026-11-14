// supabase/functions/linkedin-signin/index.ts
//
// Server-side half of "Apply via LinkedIn" — plain LinkedIn Sign-In (OIDC: openid + profile +
// email), used ONLY to prefill a new applicant's name/email/headline on the apply form.
//
// This is a SEPARATE concern from supabase/functions/linkedin-oauth/index.ts (the member-level
// "Connect LinkedIn" / "Share to LinkedIn" posting feature, which uses w_member_social and
// writes to the linkedin_connections table). The two share the same LinkedIn Developer app and
// Client ID (86dpuqc5ufkfhp) because that's the one app Mahayukti has registered, but they use
// different registered redirect URIs, different scopes, and this function:
//   - requires NO Supabase session (an applicant filling out this form has no account yet)
//   - never writes to the database — it only reads LinkedIn's /v2/userinfo and hands back the
//     display fields the apply form needs
//   - never returns the LinkedIn access token to the browser, even though it never stores one
//     either — the token lives only for the duration of this request
//
// One action, POST only:
//   { action: "userinfo", code, redirect_uri }
//     Exchanges a LinkedIn authorization code for an access token (server-side, using
//     LINKEDIN_CLIENT_SECRET — the same Supabase project secret the posting feature uses), then
//     calls LinkedIn's OIDC userinfo endpoint and returns { profile: { name, given_name,
//     family_name, email, headline, picture } }. `redirect_uri` must exactly match what was
//     sent to LinkedIn's /authorization endpoint
//     (https://mahayukti.com/auth/linkedin-signin/callback/) and what's registered as an
//     additional "Authorized redirect URL" on the LinkedIn app.
//
// Note: LinkedIn's OIDC userinfo response does not include a headline/job-title field — that's
// only available via the older /v2/me profile API, which needs the r_liteprofile scope this app
// does not currently request. `headline` is included in the response shape for forward
// compatibility (e.g. if r_liteprofile is ever added) but will be null until then; the apply
// form falls back to asking the applicant for their domain/role directly, which it needs anyway.

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

async function handleUserinfo(body: { code?: string; redirect_uri?: string }) {
  if (!LINKEDIN_CLIENT_SECRET) {
    return json({ error: "LINKEDIN_CLIENT_SECRET is not set on this Supabase project. Set it with: supabase secrets set LINKEDIN_CLIENT_SECRET=<rotated secret>" }, 500);
  }
  const { code, redirect_uri } = body;
  if (!code || !redirect_uri) return json({ error: "code and redirect_uri are required" }, 400);

  // 1) Exchange the authorization code for an access token. Deliberately short-lived use: this
  // token is used once, below, and then discarded — it is never persisted anywhere.
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
    return json({ error: "LinkedIn sign-in failed", detail: tokenData }, 400);
  }

  // 2) Fetch the OIDC userinfo claims — this is the one and only thing this flow needs.
  const userinfoRes = await fetch("https://api.linkedin.com/v2/userinfo", {
    headers: { Authorization: `Bearer ${tokenData.access_token}` },
  });
  const userinfo = await userinfoRes.json();
  if (!userinfoRes.ok || !userinfo.sub) {
    return json({ error: "Could not read your LinkedIn profile", detail: userinfo }, 400);
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
    return json({ error: "Unknown action. Use 'userinfo'." }, 400);
  } catch (e) {
    return json({ error: "Unhandled error", detail: String(e) }, 500);
  }
});
