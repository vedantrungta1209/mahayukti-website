// supabase/functions/send-push/index.ts
//
// Called by trigger_send_push() (a Postgres trigger, via pg_net) for every
// new row inserted into public.notifications, regardless of which feature
// created it -- mentions, comments, DMs, connection requests, new
// followers, best-answer, etc. This is the ONE place that actually sends
// push notifications, so every notification type gets real delivery for
// free instead of each feature's own trigger needing to know about push.
//
// Android tokens go through FCM's HTTP v1 API (the legacy server-key API
// was shut down in 2024 -- this needs a short-lived OAuth2 access token
// minted from a Firebase service account instead).
//
// iOS tokens do NOT go through FCM at all: Capacitor's push-notifications
// plugin returns the raw APNs device token on iOS, and nothing in this
// native project integrates the Firebase iOS SDK to convert that into an
// FCM-format token (confirmed live: FCM's v1 API rejected a real registered
// iOS token with "not a valid FCM registration token"). iOS tokens are sent
// directly to Apple's APNs HTTP/2 API instead, authenticated with a
// provider JWT signed by the Apple-issued APNs Auth Key (ES256), which is
// what most of the iOS-specific code below is doing.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const FCM_SERVICE_ACCOUNT_JSON = Deno.env.get("FCM_SERVICE_ACCOUNT_JSON");
const APNS_AUTH_KEY = Deno.env.get("APNS_AUTH_KEY");
const APNS_KEY_ID = Deno.env.get("APNS_KEY_ID");
const APNS_TEAM_ID = Deno.env.get("APNS_TEAM_ID");
const APNS_BUNDLE_ID = Deno.env.get("APNS_BUNDLE_ID") ?? "com.mahayukti.app";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function base64url(bytes: ArrayBuffer | Uint8Array): string {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let bin = "";
  for (const b of arr) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function pemToArrayBuffer(pem: string, label: string): ArrayBuffer {
  const b64 = pem.replace(new RegExp(`-----BEGIN ${label}-----`), "").replace(new RegExp(`-----END ${label}-----`), "").replace(/\s/g, "");
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

// Service accounts don't get a ready-made OAuth2 access token -- this signs
// a short-lived JWT asserting "I am this service account, asking for the
// firebase.messaging scope" and trades it with Google for one.
async function getFcmAccessToken(serviceAccount: { client_email: string; private_key: string }): Promise<string> {
  const header = { alg: "RS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const claims = {
    iss: serviceAccount.client_email,
    scope: "https://www.googleapis.com/auth/firebase.messaging",
    aud: "https://oauth2.googleapis.com/token",
    iat: now,
    exp: now + 3600,
  };
  const encHeader = base64url(new TextEncoder().encode(JSON.stringify(header)));
  const encClaims = base64url(new TextEncoder().encode(JSON.stringify(claims)));
  const signingInput = `${encHeader}.${encClaims}`;

  const key = await crypto.subtle.importKey(
    "pkcs8",
    pemToArrayBuffer(serviceAccount.private_key, "PRIVATE KEY"),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(signingInput));
  const jwt = `${signingInput}.${base64url(signature)}`;

  const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: jwt,
    }),
  });
  const tokenData = await tokenRes.json();
  if (!tokenRes.ok || !tokenData.access_token) {
    throw new Error("Could not get an FCM access token: " + JSON.stringify(tokenData));
  }
  return tokenData.access_token;
}

// APNs provider tokens are valid up to an hour -- cached per cold-start
// instance instead of re-signed on every single device in the loop below.
let cachedApnsJwt: { jwt: string; exp: number } | null = null;
async function getApnsProviderJwt(): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  if (cachedApnsJwt && cachedApnsJwt.exp - now > 60) return cachedApnsJwt.jwt;

  const header = { alg: "ES256", kid: APNS_KEY_ID };
  const claims = { iss: APNS_TEAM_ID, iat: now };
  const encHeader = base64url(new TextEncoder().encode(JSON.stringify(header)));
  const encClaims = base64url(new TextEncoder().encode(JSON.stringify(claims)));
  const signingInput = `${encHeader}.${encClaims}`;

  const key = await crypto.subtle.importKey(
    "pkcs8",
    pemToArrayBuffer(APNS_AUTH_KEY!, "PRIVATE KEY"),
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"],
  );
  // Web Crypto's ECDSA signatures are already raw (r||s) IEEE P1363 format --
  // exactly what a JWT's ES256 signature needs, unlike most server-side
  // crypto libraries which default to DER and need manual re-encoding.
  const signature = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, new TextEncoder().encode(signingInput));
  const jwt = `${signingInput}.${base64url(signature)}`;
  cachedApnsJwt = { jwt, exp: now + 3600 };
  return jwt;
}

async function sendViaApns(token: string, title: string, body: string, data: Record<string, string>) {
  const jwt = await getApnsProviderJwt();
  // TestFlight and App Store builds both use the production APNs gateway,
  // not sandbox -- confirmed live against a real TestFlight-installed
  // device (the sandbox gateway rejects a production-environment token).
  const res = await fetch(`https://api.push.apple.com/3/device/${token}`, {
    method: "POST",
    headers: {
      authorization: `bearer ${jwt}`,
      "apns-topic": APNS_BUNDLE_ID,
      "apns-push-type": "alert",
    },
    body: JSON.stringify({ aps: { alert: { title, body }, sound: "default" }, ...data }),
  });
  let detail;
  try { detail = await res.json(); } catch { detail = null; }
  return { ok: res.ok, detail };
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let body: { notification_id?: string };
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }
  const { notification_id } = body;
  if (!notification_id) return json({ error: "notification_id is required" }, 400);

  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  const { data: notif, error: notifErr } = await admin
    .from("notifications")
    .select("id, user_id, title, body, link_type, link_id")
    .eq("id", notification_id)
    .single();
  if (notifErr || !notif) return json({ ok: true, note: "Notification not found (may have been deleted)" });

  const { data: tokens, error: tokErr } = await admin
    .from("push_tokens")
    .select("token, platform")
    .eq("user_id", notif.user_id);
  if (tokErr) return json({ error: tokErr.message }, 500);
  if (!tokens || !tokens.length) return json({ ok: true, note: "No registered devices for this user" });

  const data = notif.link_type && notif.link_id
    ? { link_type: notif.link_type, link_id: notif.link_id }
    : {};

  const androidTokens = tokens.filter((t) => t.platform === "android");
  const iosTokens = tokens.filter((t) => t.platform === "ios");
  const results: { platform: string; ok: boolean; detail?: unknown }[] = [];

  if (androidTokens.length) {
    if (!FCM_SERVICE_ACCOUNT_JSON) {
      results.push({ platform: "android", ok: false, detail: "FCM_SERVICE_ACCOUNT_JSON not set" });
    } else {
      try {
        const serviceAccount = JSON.parse(FCM_SERVICE_ACCOUNT_JSON);
        const accessToken = await getFcmAccessToken(serviceAccount);
        for (const t of androidTokens) {
          const sendRes = await fetch(
            `https://fcm.googleapis.com/v1/projects/${serviceAccount.project_id}/messages:send`,
            {
              method: "POST",
              headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
              body: JSON.stringify({
                message: {
                  token: t.token,
                  notification: { title: notif.title, body: notif.body },
                  data,
                  android: { priority: "high" },
                },
              }),
            },
          );
          const sendData = await sendRes.json();
          results.push({ platform: "android", ok: sendRes.ok, detail: sendRes.ok ? undefined : sendData });
          if (!sendRes.ok && (sendData?.error?.status === "UNREGISTERED" || sendData?.error?.status === "NOT_FOUND")) {
            await admin.from("push_tokens").delete().eq("token", t.token);
          }
        }
      } catch (e) {
        results.push({ platform: "android", ok: false, detail: String(e) });
      }
    }
  }

  if (iosTokens.length) {
    if (!APNS_AUTH_KEY || !APNS_KEY_ID || !APNS_TEAM_ID) {
      results.push({ platform: "ios", ok: false, detail: "APNS_AUTH_KEY/APNS_KEY_ID/APNS_TEAM_ID not set" });
    } else {
      for (const t of iosTokens) {
        try {
          const { ok, detail } = await sendViaApns(t.token, notif.title, notif.body, data);
          results.push({ platform: "ios", ok, detail });
          if (!ok && (detail?.reason === "Unregistered" || detail?.reason === "BadDeviceToken")) {
            await admin.from("push_tokens").delete().eq("token", t.token);
          }
        } catch (e) {
          results.push({ platform: "ios", ok: false, detail: String(e) });
        }
      }
    }
  }

  return json({ ok: true, sent_to: results.length, results });
});
