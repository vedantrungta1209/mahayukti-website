// supabase/functions/send-push/index.ts
//
// Called by trigger_send_push() (a Postgres trigger, via pg_net) for every
// new row inserted into public.notifications, regardless of which feature
// created it -- mentions, comments, DMs, connection requests, new
// followers, best-answer, etc. This is the ONE place that actually talks to
// FCM, so every notification type gets real push delivery for free instead
// of each feature's own trigger needing to know about push at all.
//
// FCM's legacy server-key API was shut down (June 2024) -- the only way to
// send now is the HTTP v1 API, which needs a short-lived OAuth2 access
// token minted from a Firebase service account, not a long-lived server
// key. That token-exchange dance (sign a JWT with the service account's
// RSA key, trade it for an access token, then call FCM) is what most of
// this file is doing.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const FCM_SERVICE_ACCOUNT_JSON = Deno.env.get("FCM_SERVICE_ACCOUNT_JSON");

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function base64url(bytes: ArrayBuffer | Uint8Array): string {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let bin = "";
  for (const b of arr) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function pemToArrayBuffer(pem: string): ArrayBuffer {
  const b64 = pem.replace(/-----BEGIN PRIVATE KEY-----/, "").replace(/-----END PRIVATE KEY-----/, "").replace(/\s/g, "");
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
    pemToArrayBuffer(serviceAccount.private_key),
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

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  if (!FCM_SERVICE_ACCOUNT_JSON) {
    // Not configured yet -- fail soft. The in-app notification row this was
    // triggered from already exists regardless; push is additive on top of
    // it, never a dependency for the notification itself to "work".
    return json({ ok: true, skipped: "FCM_SERVICE_ACCOUNT_JSON not set" });
  }

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
    .select("id, user_id, title, body")
    .eq("id", notification_id)
    .single();
  if (notifErr || !notif) return json({ ok: true, note: "Notification not found (may have been deleted)" });

  const { data: tokens, error: tokErr } = await admin
    .from("push_tokens")
    .select("token, platform")
    .eq("user_id", notif.user_id);
  if (tokErr) return json({ error: tokErr.message }, 500);
  if (!tokens || !tokens.length) return json({ ok: true, note: "No registered devices for this user" });

  let serviceAccount: { project_id: string; client_email: string; private_key: string };
  try {
    serviceAccount = JSON.parse(FCM_SERVICE_ACCOUNT_JSON);
  } catch {
    return json({ error: "FCM_SERVICE_ACCOUNT_JSON is not valid JSON" }, 500);
  }

  let accessToken: string;
  try {
    accessToken = await getFcmAccessToken(serviceAccount);
  } catch (e) {
    return json({ error: String(e) }, 500);
  }

  const results = [];
  for (const t of tokens) {
    const sendRes = await fetch(
      `https://fcm.googleapis.com/v1/projects/${serviceAccount.project_id}/messages:send`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          message: {
            token: t.token,
            notification: { title: notif.title, body: notif.body },
            // Both platforms read the plain notification block above for the
            // visible push; these per-platform blocks only add delivery
            // behavior (sound, priority), not duplicate content.
            apns: { payload: { aps: { sound: "default" } } },
            android: { priority: "high" },
          },
        }),
      },
    );
    const sendData = await sendRes.json();
    results.push({ platform: t.platform, ok: sendRes.ok, detail: sendRes.ok ? undefined : sendData });
    // A token FCM reports as unregistered/invalid is a dead device (app
    // reinstalled, uninstalled, etc.) -- worth clearing so this user stops
    // accumulating failed sends to it forever, not worth treating as an error.
    if (!sendRes.ok && (sendData?.error?.status === "UNREGISTERED" || sendData?.error?.status === "NOT_FOUND")) {
      await admin.from("push_tokens").delete().eq("token", t.token);
    }
  }

  return json({ ok: true, sent_to: results.length, results });
});
