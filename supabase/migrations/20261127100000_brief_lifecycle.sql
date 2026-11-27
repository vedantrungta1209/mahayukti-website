-- Brief lifecycle: exchange_briefs already had a status check
-- (open/matched/closed) and a working own-or-admin UPDATE policy, but
-- nothing in the UI ever used either -- a brief could never leave "open"
-- once posted. awarded_response_id tracks which response was actually
-- chosen, mirroring help_posts.best_reply_id's exact pattern (same
-- with_check shape: only settable by the brief's own author/admin, and
-- only to a response that actually belongs to this same brief).
alter table public.exchange_briefs add column if not exists awarded_response_id uuid references public.exchange_brief_responses(id) on delete set null;

-- A plain inline EXISTS against exchange_brief_responses here causes
-- "infinite recursion detected in policy" at runtime: that table's own
-- SELECT policy (exchange_brief_responses_select_participant) queries back
-- into exchange_briefs, so the two tables' RLS would evaluate each other in
-- a cycle. Routing the check through a SECURITY DEFINER function (same fix
-- used for the identical recursion hit in community_members earlier this
-- session) breaks the cycle since the function's own internal query bypasses
-- RLS entirely.
create or replace function public.brief_response_belongs(p_response_id uuid, p_brief_id uuid)
returns boolean
language sql
stable security definer
set search_path to 'public'
as $$
  select exists (
    select 1 from public.exchange_brief_responses r
    where r.id = p_response_id and r.brief_id = p_brief_id
  );
$$;

drop policy if exists exchange_briefs_update_own on public.exchange_briefs;
create policy exchange_briefs_update_own on public.exchange_briefs
  for update
  using (author_id in (select id from public.users where auth_id = auth.uid()) or is_platform_admin())
  with check (
    (is_platform_admin() or author_id in (select id from public.users where auth_id = auth.uid()))
    and (awarded_response_id is null or brief_response_belongs(awarded_response_id, exchange_briefs.id))
  );
