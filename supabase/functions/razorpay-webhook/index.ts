// supabase/functions/razorpay-webhook/index.ts
//
// This is the ONLY place a seller_package_subscriptions row is ever
// activated after real payment. Razorpay calls this server-to-server, with
// a signature over the exact raw request body -- verifying that signature
// is what actually proves the event came from Razorpay and wasn't forged by
// a client claiming "I paid." Never activate on a client-side signal alone.
//
// Configure in the Razorpay dashboard (Settings -> Webhooks): URL
// https://npyoyylrqprawyavnfvv.supabase.co/functions/v1/razorpay-webhook,
// event payment.captured, and set the same secret as RAZORPAY_WEBHOOK_SECRET
// below via `supabase secrets set`.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RAZORPAY_WEBHOOK_SECRET = Deno.env.get("RAZORPAY_WEBHOOK_SECRET");
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

async function verifySignature(rawBody: string, signature: string, secret: string): Promise<boolean> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(rawBody));
  const expected = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  // Lengths are fixed (both hex SHA-256), so a plain loop is a safe
  // constant-time-enough comparison without pulling in a timingSafeEqual dependency.
  if (expected.length !== signature.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected.charCodeAt(i) ^ signature.charCodeAt(i);
  return diff === 0;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  if (!RAZORPAY_WEBHOOK_SECRET) return json({ error: "RAZORPAY_WEBHOOK_SECRET is not set on this Supabase project." }, 500);

  const signature = req.headers.get("X-Razorpay-Signature");
  if (!signature) return json({ error: "Missing signature" }, 400);

  const rawBody = await req.text();
  const valid = await verifySignature(rawBody, signature, RAZORPAY_WEBHOOK_SECRET);
  if (!valid) return json({ error: "Invalid signature" }, 401);

  const event = JSON.parse(rawBody);
  if (event.event !== "payment.captured") return json({ ok: true, skipped: event.event });

  const payment = event.payload?.payment?.entity;
  const orderId = payment?.order_id;
  const paymentId = payment?.id;
  if (!orderId || !paymentId) return json({ error: "Malformed payload" }, 400);

  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  const { data: sub, error: subErr } = await admin
    .from("seller_package_subscriptions")
    .select("id, status, package_id")
    .eq("razorpay_order_id", orderId)
    .maybeSingle();
  if (subErr) return json({ error: subErr.message }, 500);
  if (!sub) return json({ ok: true, note: "No matching subscription for this order" });

  // Idempotent: Razorpay can and does retry webhook delivery. Only act the
  // first time -- a second payment.captured for an already-active row is a
  // no-op, not a second activation.
  if (sub.status !== "pending_payment") return json({ ok: true, already: sub.status });

  const { data: pkg } = await admin
    .from("marketplace_packages")
    .select("duration_days")
    .eq("id", sub.package_id)
    .single();
  const durationDays = pkg?.duration_days ?? 90;
  const expiresAt = new Date(Date.now() + durationDays * 86400000).toISOString();

  const { error: updateErr } = await admin
    .from("seller_package_subscriptions")
    .update({
      status: "active",
      activated_at: new Date().toISOString(),
      expires_at: expiresAt,
      razorpay_payment_id: paymentId,
    })
    .eq("id", sub.id)
    .eq("status", "pending_payment");
  if (updateErr) return json({ error: updateErr.message }, 500);

  return json({ ok: true, activated: sub.id });
});
