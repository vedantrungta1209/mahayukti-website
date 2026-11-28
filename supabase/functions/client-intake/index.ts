// supabase/functions/client-intake/index.ts
//
// The missing other half of the existing Admin > Client Briefs screen.
// client_briefs (20261120200000) already had admin-only read/triage
// (Pending -> Reviewing -> Assigned -> Done) fully built, but its own
// migration comment said plainly there was no insert path anywhere in the
// repo -- rows had to arrive from some unspecified external process. This
// is a public, unauthenticated intake endpoint for the homepage's "Get
// expert help" form (index.html#get-help): a client describes an urgent
// problem without ever becoming a verified professional member, and it
// lands directly in the same admin triage queue.
//
// No JWT required (this is deployed with --no-verify-jwt) -- the only
// auth concept that applies here is "nothing writes to client_briefs
// except through this function," enforced by RLS already being admin-only
// for every other path. Basic anti-abuse: a honeypot field, field-length
// caps, and a same-email rate limit, all checked before the insert.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

const VALID_URGENCY = ["normal", "urgent", "critical"];

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400);
  }

  // Honeypot -- a real visitor never sees or fills this field (hidden via
  // CSS + aria-hidden on the form), a form-filling bot often does. Silently
  // succeed rather than tell a bot its submission was rejected.
  if (typeof body.website === "string" && body.website.trim() !== "") {
    return json({ ok: true });
  }

  const contactName = String(body.contact_name || "").trim().slice(0, 200);
  const contactEmail = String(body.contact_email || "").trim().slice(0, 200);
  const contactPhone = String(body.contact_phone || "").trim().slice(0, 40);
  const company = String(body.company || "").trim().slice(0, 200);
  const domainNeeded = String(body.domain_needed || "").trim().slice(0, 100);
  const urgency = VALID_URGENCY.includes(String(body.urgency)) ? String(body.urgency) : "normal";
  const description = String(body.description || "").trim().slice(0, 4000);
  const confidentiality = String(body.confidentiality || "").trim().slice(0, 500);

  if (!contactName || !contactEmail || !domainNeeded || !description) {
    return json({ error: "Missing required fields" }, 400);
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactEmail)) {
    return json({ error: "Invalid email" }, 400);
  }

  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  // Same-email rate limit: 3 submissions per hour is generous for a real
  // client (who would normally only ever submit once) and blocks a script
  // hammering the endpoint with one address.
  const windowStart = new Date(Date.now() - 60 * 60 * 1000).toISOString();
  const { count } = await admin
    .from("client_briefs")
    .select("id", { count: "exact", head: true })
    .eq("contact_email", contactEmail)
    .gte("created_at", windowStart);
  if ((count ?? 0) >= 3) {
    return json({ error: "Too many requests from this email recently. Please email help@mahayukti.com directly." }, 429);
  }

  const { error } = await admin.from("client_briefs").insert({
    contact_name: contactName,
    contact_email: contactEmail,
    contact_phone: contactPhone || null,
    company: company || null,
    domain_needed: domainNeeded,
    urgency,
    description,
    confidentiality: confidentiality || null,
    status: "pending",
  });
  if (error) return json({ error: "Could not submit request" }, 500);

  return json({ ok: true });
});
