-- LinkedIn member-level connect + share-to-profile feature.
--
-- Stores only what's needed to post later on a member's own behalf: the OAuth access token,
-- its expiry, and the LinkedIn member id ("sub" from the OpenID userinfo response, used to build
-- the urn:li:person:{sub} author URN the Posts API requires). No refresh token is stored because
-- LinkedIn's member-level 3-legged OAuth for this app does not issue one by default; when the
-- token expires the member just reconnects via the same button.
--
-- This is NOT the organization/brand-page posting feature (w_organization_social) — that scope
-- is blocked on a separate pending LinkedIn API review. This table and the linkedin-oauth Edge
-- Function are individual member posting only (w_member_social), already an approved/active scope.
--
-- Written and read only by the linkedin-oauth Supabase Edge Function:
--   - writes use the service role key (the function verifies the caller's own Supabase session
--     JWT first, then upserts this table itself — it does not rely on RLS for the write path)
--   - the one client-side read (checking "am I connected") goes through the owner-only select
--     policy below using the member's own JWT, same pattern as every other table in this app.
--
-- Idempotent (IF NOT EXISTS / DROP POLICY IF EXISTS) so it is safe to re-run.

begin;

create table if not exists public.linkedin_connections (
  auth_user_id    uuid primary key references auth.users(id) on delete cascade,
  linkedin_sub    text not null,              -- LinkedIn member id from /v2/userinfo "sub" -> urn:li:person:{sub}
  access_token    text not null,
  token_expires_at timestamptz not null,
  scope           text,
  connected_at    timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

alter table public.linkedin_connections enable row level security;

-- Owner can see whether (and when) they're connected — but the access_token column is still only
-- ever read server-side by the Edge Function using the service role key, never fetched by the
-- client. The select policy exists so the client can show connection status without a token.
drop policy if exists linkedin_connections_select_own on public.linkedin_connections;
create policy linkedin_connections_select_own on public.linkedin_connections for select using (
  auth_user_id = auth.uid() or public.is_platform_admin()
);

-- No insert/update/delete policy for authenticated/anon: this table is written only by the
-- linkedin-oauth Edge Function using the service role key, which bypasses RLS entirely. This is
-- deliberate — a client should never be able to write its own access_token row directly.

-- Let a member disconnect (delete their own row) from the client without going through the
-- Edge Function, since that needs no secret and no LinkedIn call.
drop policy if exists linkedin_connections_delete_own on public.linkedin_connections;
create policy linkedin_connections_delete_own on public.linkedin_connections for delete using (
  auth_user_id = auth.uid()
);

commit;
