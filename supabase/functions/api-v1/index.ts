// supabase/functions/api-v1/index.ts
//
// MahaYukti's public API, v1. Key issuance (supabase/functions precede this
// comment: api_keys table, hashing, scopes, revocation -- see
// generateApiKey()/loadDeveloperSettings() in app.html) already existed;
// nothing was ever actually serving requests against a key. This is that
// server.
//
// Scope for this first version: READ-ONLY. api_keys already names a 'post'
// scope (clearly meant for a future write endpoint -- creating a post
// through the API as the key's owner), but actually building that is a
// separate trust-boundary decision (letting third-party tools post AS a
// member needs its own careful review of what guardrails apply) and is
// deliberately NOT built here. This version only ever reads already-public
// data (posts_public, organizations) or the key owner's own profile.
//
// Auth: `Authorization: Bearer mhy_live_...`. The key is hashed the same
// way generateApiKey() hashes it client-side (SHA-256) and looked up by
// that hash -- the raw key itself is never stored, matching how it was
// already designed.
//
// Endpoints:
//   GET /api-v1/posts                 -- public posts, paginated
//   GET /api-v1/posts/:id              -- one public post
//   GET /api-v1/organizations          -- public org directory, paginated
//   GET /api-v1/organizations/:slug    -- one org + its public posts
//   GET /api-v1/me                     -- the key owner's own profile (needs 'read_profile' scope)
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const RATE_LIMIT_PER_MINUTE = 60;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });
}

async function sha256Hex(input: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function authenticate(req: Request, admin: ReturnType<typeof createClient>) {
  const auth = req.headers.get("Authorization") || "";
  const raw = auth.startsWith("Bearer ") ? auth.slice(7) : null;
  if (!raw) return { error: json({ error: "Missing Authorization: Bearer <key>" }, 401) };

  const hash = await sha256Hex(raw);
  const { data: key } = await admin
    .from("api_keys")
    .select("id, user_id, scopes, revoked_at")
    .eq("key_hash", hash)
    .maybeSingle();
  if (!key || key.revoked_at) return { error: json({ error: "Invalid or revoked API key" }, 401) };

  // Fixed one-minute buckets -- simple, no external dependency, good enough
  // for a first version of real rate limiting (none existed before this).
  const windowStart = new Date(Math.floor(Date.now() / 60000) * 60000).toISOString();
  const { data: usage } = await admin
    .from("api_key_usage")
    .select("request_count")
    .eq("key_id", key.id)
    .eq("window_start", windowStart)
    .maybeSingle();
  const count = (usage?.request_count ?? 0) + 1;
  if (count > RATE_LIMIT_PER_MINUTE) {
    return { error: json({ error: `Rate limit exceeded: ${RATE_LIMIT_PER_MINUTE} requests/minute` }, 429) };
  }
  await admin.from("api_key_usage").upsert(
    { key_id: key.id, window_start: windowStart, request_count: count },
    { onConflict: "key_id,window_start" },
  );
  await admin.from("api_keys").update({ last_used_at: new Date().toISOString() }).eq("id", key.id);

  return { key };
}

function paginationParams(url: URL) {
  const limit = Math.min(parseInt(url.searchParams.get("limit") || "20", 10) || 20, 100);
  const before = url.searchParams.get("before"); // an ISO created_at cursor
  return { limit, before };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "authorization, content-type",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
      },
    });
  }
  if (req.method !== "GET") return json({ error: "This version of the API is read-only (GET only)" }, 405);

  const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);
  const { key, error } = await authenticate(req, admin);
  if (error) return error;

  const url = new URL(req.url);
  // Strip the function's own mount path so routing below only ever sees
  // "/posts", "/organizations/:slug", "/me", etc. regardless of whether
  // Supabase fronts this at /functions/v1/api-v1/... or just /api-v1/....
  const path = url.pathname.replace(/^.*\/api-v1/, "") || "/";
  const segments = path.split("/").filter(Boolean);

  if (segments[0] === "me") {
    if (!key.scopes?.includes("read_profile")) {
      return json({ error: "This key does not have the read_profile scope" }, 403);
    }
    const { data } = await admin
      .from("member_directory")
      .select("id, username, real_name, show_real_name, real_name_approved, city, domain, domain_group, role, organisation, about")
      .eq("id", key.user_id)
      .maybeSingle();
    return json({ data });
  }

  if (segments[0] === "posts" && !segments[1]) {
    const { limit, before } = paginationParams(url);
    let q = admin.from("posts_public").select("*").order("created_at", { ascending: false }).limit(limit);
    if (before) q = q.lt("created_at", before);
    const { data, error: qErr } = await q;
    if (qErr) return json({ error: qErr.message }, 500);
    return json({ data, next_cursor: data?.length === limit ? data[data.length - 1].created_at : null });
  }

  if (segments[0] === "posts" && segments[1]) {
    const { data } = await admin.from("posts_public").select("*").eq("id", segments[1]).maybeSingle();
    if (!data) return json({ error: "Not found (post may not be public, or doesn't exist)" }, 404);
    return json({ data });
  }

  if (segments[0] === "organizations" && !segments[1]) {
    const { limit, before } = paginationParams(url);
    let q = admin.from("organizations").select("id, name, slug, kind, description, logo_url, verified, created_at").order("created_at", { ascending: false }).limit(limit);
    if (before) q = q.lt("created_at", before);
    const { data, error: qErr } = await q;
    if (qErr) return json({ error: qErr.message }, 500);
    return json({ data, next_cursor: data?.length === limit ? data[data.length - 1].created_at : null });
  }

  if (segments[0] === "organizations" && segments[1]) {
    const { data: org } = await admin
      .from("organizations")
      .select("id, name, slug, kind, description, logo_url, verified, created_at")
      .eq("slug", segments[1])
      .maybeSingle();
    if (!org) return json({ error: "Organization not found" }, 404);
    const { data: posts } = await admin
      .from("posts_public")
      .select("*")
      .eq("posted_as_org_id", org.id)
      .order("created_at", { ascending: false })
      .limit(20);
    return json({ data: { ...org, posts: posts || [] } });
  }

  return json({
    error: "Unknown endpoint",
    available: ["GET /posts", "GET /posts/:id", "GET /organizations", "GET /organizations/:slug", "GET /me"],
  }, 404);
});
