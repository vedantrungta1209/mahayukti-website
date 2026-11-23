-- exchange_briefs_select_all had `USING (true)` -- any role, including an
-- unauthenticated one, could read every column of every brief directly from
-- the base table. exchange_briefs_public exists specifically to null out
-- author_id for anonymous briefs before members list them; reading the base
-- table instead gives the real author_id straight away, defeating that
-- anonymity entirely. app.html itself only ever reads the base table for
-- the caller's own briefs (loadMyBriefs) or to insert -- every cross-member
-- listing already goes through exchange_briefs_public -- so restricting the
-- base table's read policy to the brief's own author plus admins matches
-- real usage exactly and closes the de-anonymization hole.
drop policy if exists exchange_briefs_select_all on public.exchange_briefs;

create policy exchange_briefs_select_own_or_admin on public.exchange_briefs for select using (
  author_id in (select id from public.users where auth_id = auth.uid())
  or public.is_platform_admin()
);
