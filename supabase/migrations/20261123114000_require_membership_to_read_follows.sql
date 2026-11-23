-- follows_select_all was `USING (true)` -- unlike member_connections, which
-- is deliberately locked to the two participants (member_connections_select_
-- participant, 20261120150000) specifically so one member can't see another's
-- full relationship list, follows had no restriction at all: who-follows-whom
-- for every member was readable by anyone, including an unauthenticated
-- caller. Nothing in app.html ever surfaces this pre-login, so there's no
-- legitimate anonymous use for it. This only closes the "readable by the raw
-- internet with no account" gap -- it intentionally leaves the broader
-- "should one member see another's full follow list" question alone, since
-- that's a product call (unlike member_connections, there's no existing
-- design note saying follows was meant to be participant-only), and keeps
-- today's member-to-member visibility exactly as it was.
drop policy if exists follows_select_all on public.follows;

create policy follows_select_active_members on public.follows for select using (
  exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
  or public.is_platform_admin()
);
