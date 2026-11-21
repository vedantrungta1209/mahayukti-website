-- Found live: a seller could click "Message seller" on their own marketplace listing --
-- loadMarketplace() always rendered the button regardless of seller_id, and
-- marketplace_inquiries_insert_own only ever checked buyer_id = the querying user, never
-- that the listing's seller_id differs. Not a security issue (nothing sensitive leaks),
-- just a real data-quality/UX gap: a self-inquiry row would show up in the seller's own
-- "My listings & inquiries received" view attributed to themselves as the buyer.
--
-- Client-side fix: the button is now hidden when seller_id === the viewer's own id.
-- This migration closes it at the database level too, consistent with this session's
-- practice of not relying on the client alone to enforce a rule a direct API call could
-- still bypass.

drop policy if exists marketplace_inquiries_insert_own on public.marketplace_inquiries;

create policy marketplace_inquiries_insert_own on public.marketplace_inquiries
for insert
with check (
  buyer_id in (select users.id from public.users where users.auth_id = auth.uid())
  and not exists (
    select 1 from public.marketplace_listings l
    where l.id = marketplace_inquiries.listing_id
      and l.seller_id = marketplace_inquiries.buyer_id
  )
);
