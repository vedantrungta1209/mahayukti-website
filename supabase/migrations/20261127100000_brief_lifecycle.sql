-- Brief lifecycle: exchange_briefs already had a status check
-- (open/matched/closed) and a working own-or-admin UPDATE policy, but
-- nothing in the UI ever used either -- a brief could never leave "open"
-- once posted. awarded_response_id tracks which response was actually
-- chosen, mirroring help_posts.best_reply_id's exact pattern (same
-- with_check shape: only settable by the brief's own author/admin, and
-- only to a response that actually belongs to this same brief).
alter table public.exchange_briefs add column if not exists awarded_response_id uuid references public.exchange_brief_responses(id) on delete set null;

drop policy if exists exchange_briefs_update_own on public.exchange_briefs;
create policy exchange_briefs_update_own on public.exchange_briefs
  for update
  using (author_id in (select id from public.users where auth_id = auth.uid()) or is_platform_admin())
  with check (
    (is_platform_admin() or author_id in (select id from public.users where auth_id = auth.uid()))
    and (awarded_response_id is null or exists (
      select 1 from public.exchange_brief_responses r
      where r.id = awarded_response_id and r.brief_id = exchange_briefs.id
    ))
  );
