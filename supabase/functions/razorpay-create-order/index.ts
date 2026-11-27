// supabase/functions/razorpay-create-order/index.ts
//
// Server-side half of real seller-package payment. The client never talks to
// Razorpay's Orders API directly -- that would need the key_secret in
// client-side code, which must never leave the server. This function:
//   1. Verifies the caller's own JWT and that the subscription row really
//      belongs to them and is still pending_payment (never trust a
//      client-supplied user id or subscription id at face value).
//   2. Creates a real Razorpay order for the package's price.
//   3. Stores the order id on the subscription row using the SERVICE ROLE
//      key, not the caller's own token -- every write that touches payment
//      state in this feature goes through the service role, never through
//      seller_package_subscriptions' own self-update RLS policy, so nothing
//      about activation ever depends on trusting the client.
// Activation itself does NOT happen here -- only razorpay-webhook (driven by
// Razorpay's own server-to-server callback, signature-verified) ever sets
// status='active'. A client-side "payment succeeded" signal is never
// sufficient by itself to grant access.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RAZORPAY_KEY_ID = Deno.env.get("RAZORPAY_KEY_ID");
const RAZORPAY_KEY_SECRET = Deno.env.get("RAZORPAY_KEY_SECRET");
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

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

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS_HEADERS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  if (!RAZORPAY_KEY_ID || !RAZORPAY_KEY_SECRET) {
    return json({ error: "Razorpay is not configured on this Supabase project. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET with: supabase secrets set" }, 500);
  }

  const authHeader = req.headers.get("Authorization");
  if (!authHeader) return json({ error: "Missing Authorization header" }, 401);

  let body: { subscription_id?: string };
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }
  const { subscription_id } = body;
  if (!subscription_id) return json({ error: "subscription_id is required" }, 400);

  // The caller's own token -- RLS (seller_subs_select_own_or_admin) is what
  // actually proves this subscription belongs to them; this client is
  // deliberately NOT the service role.
  const asCaller = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    global: { headers: { Authorization: authHeader } },
  });

  const { data: sub, error: subErr } = await asCaller
    .from("seller_package_subscriptions")
    .select("id, status, package_id, user_id")
    .eq("id", subscription_id)
    .single();

  if (subErr || !sub) return json({ error: "Subscription not found or not yours" }, 404);
  if (sub.status !== "pending_payment") {
    return json({ error: `This subscription is '${sub.status}', not awaiting payment.` }, 400);
  }

  const { data: pkg, error: pkgErr } = await asCaller
    .from("marketplace_packages")
    .select("id, name, price")
    .eq("id", sub.package_id)
    .single();
  if (pkgErr || !pkg) return json({ error: "Package not found" }, 404);

  const amountPaise = Math.round(Number(pkg.price) * 100);
  if (!(amountPaise > 0)) return json({ error: "Invalid package price" }, 400);

  const orderRes = await fetch("https://api.razorpay.com/v1/orders", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Basic " + btoa(`${RAZORPAY_KEY_ID}:${RAZORPAY_KEY_SECRET}`),
    },
    body: JSON.stringify({
      amount: amountPaise,
      currency: "INR",
      receipt: subscription_id,
      notes: { subscription_id, package_name: pkg.name, user_id: sub.user_id },
    }),
  });
  const order = await orderRes.json();
  if (!orderRes.ok || !order.id) {
    return json({ error: "Could not create the payment order", detail: order }, 502);
  }

  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);
  const { error: updateErr } = await admin
    .from("seller_package_subscriptions")
    .update({ razorpay_order_id: order.id })
    .eq("id", subscription_id)
    .eq("status", "pending_payment"); // still guards against a race with an already-activated row
  if (updateErr) return json({ error: "Could not save the order reference", detail: updateErr.message }, 500);

  return json({
    order_id: order.id,
    amount: amountPaise,
    currency: "INR",
    key_id: RAZORPAY_KEY_ID, // the key_id is meant to be public/client-facing, unlike key_secret
    package_name: pkg.name,
  });
});
