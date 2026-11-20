-- Marketplace monetization gate, per Vedant: without this, "everyone will
-- start selling everything there" -- a member needs an active package
-- before they can create a listing, not free-for-all posting.
--
-- No payment gateway is wired into this repo yet (no Razorpay/Stripe
-- integration found anywhere), so this does NOT fabricate a checkout flow.
-- A member requests a package (status 'pending_payment'); an admin marks it
-- active once payment is confirmed out-of-band, same manual-review pattern
-- already used for account verification and ad approval throughout this
-- app. Swapping in a real payment gateway later only changes who flips
-- pending_payment -> active -- the gate itself doesn't need to change.

begin;

create table if not exists public.marketplace_packages (
  id             uuid primary key default gen_random_uuid(),
  name           text not null,
  listing_quota  int,     -- null = unlimited
  price          numeric not null,
  duration_days  int not null,
  sort_order     int not null default 0,
  active         boolean not null default true
);

insert into public.marketplace_packages (name, listing_quota, price, duration_days, sort_order) values
  ('Starter',    3,    499,  90, 1),
  ('Pro',        15,   1999, 90, 2),
  ('Unlimited',  null, 4999, 90, 3)
on conflict do nothing;

create table if not exists public.seller_package_subscriptions (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references public.users(id) on delete cascade,
  package_id    uuid not null references public.marketplace_packages(id),
  listings_used int not null default 0,
  status        text not null default 'pending_payment' check (status in ('pending_payment','active','expired','rejected')),
  requested_at  timestamptz not null default now(),
  activated_at  timestamptz,
  expires_at    timestamptz
);

create index if not exists seller_package_subscriptions_user_idx on public.seller_package_subscriptions(user_id);
create index if not exists seller_package_subscriptions_status_idx on public.seller_package_subscriptions(status);

alter table public.marketplace_packages        enable row level security;
alter table public.seller_package_subscriptions enable row level security;

drop policy if exists marketplace_packages_select_all on public.marketplace_packages;
create policy marketplace_packages_select_all on public.marketplace_packages for select using (active or public.is_platform_admin());
drop policy if exists marketplace_packages_write_admin on public.marketplace_packages;
create policy marketplace_packages_write_admin on public.marketplace_packages for all using (public.is_platform_admin()) with check (public.is_platform_admin());

drop policy if exists seller_subs_select_own_or_admin on public.seller_package_subscriptions;
create policy seller_subs_select_own_or_admin on public.seller_package_subscriptions for select using (
  user_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
);
drop policy if exists seller_subs_insert_own on public.seller_package_subscriptions;
create policy seller_subs_insert_own on public.seller_package_subscriptions for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists seller_subs_update_own_or_admin on public.seller_package_subscriptions;
create policy seller_subs_update_own_or_admin on public.seller_package_subscriptions for update using (
  user_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
);

-- marketplace_listings_insert_own (20261120170000) only ever checked who
-- the seller claimed to be -- it had no concept of needing an active
-- package, which would make this whole gate client-side-only and trivially
-- bypassable via a direct API call. Require a real, unexpired, unused-up
-- subscription at the database level.
drop policy if exists marketplace_listings_insert_own on public.marketplace_listings;
create policy marketplace_listings_insert_own on public.marketplace_listings for insert with check (
  seller_id in (select id from public.users where auth_id = auth.uid())
  and exists (
    select 1 from public.seller_package_subscriptions s
    join public.marketplace_packages p on p.id = s.package_id
    where s.user_id = marketplace_listings.seller_id
      and s.status = 'active'
      and (s.expires_at is null or s.expires_at > now())
      and (p.listing_quota is null or s.listings_used < p.listing_quota)
  )
);

commit;
