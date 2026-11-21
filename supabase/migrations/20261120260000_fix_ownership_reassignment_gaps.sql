-- Same audit, same pattern, three more tables: marketplace_listings_update_
-- own, exchange_briefs_update_own, and events_update_host_or_admin
-- (20261120170000) all had a USING clause but no WITH CHECK, so an owner
-- could update their own row and reassign seller_id/author_id/host_user_id
-- to a DIFFERENT member's id -- framing someone else as the seller of a
-- listing, the author of a brief, or the host of an event they never
-- actually posted. events already got this fix on INSERT earlier this
-- session; this closes the same door on UPDATE for all three tables.

begin;

drop policy if exists marketplace_listings_update_own on public.marketplace_listings;
create policy marketplace_listings_update_own on public.marketplace_listings for update using (
  seller_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
) with check (
  public.is_platform_admin()
  or seller_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists exchange_briefs_update_own on public.exchange_briefs;
create policy exchange_briefs_update_own on public.exchange_briefs for update using (
  author_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
) with check (
  public.is_platform_admin()
  or author_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists events_update_host_or_admin on public.events;
create policy events_update_host_or_admin on public.events for update using (
  host_user_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
) with check (
  public.is_platform_admin()
  or host_user_id is null
  or host_user_id in (select id from public.users where auth_id = auth.uid())
);

commit;
