-- Marketplace (buy/sell goods), The Exchange (briefs: service requests, team
-- formation, business-for-sale, VC interest), and Events+RSVP.
--
-- Note on Exchange: the dormant public.briefs table from the phase1 migration
-- references accounts(id), the architecture-doc identity system that was
-- never wired to any live UI (confirmed earlier this lineage -- the onboarding
-- migration was deliberately corrected to target public.users directly instead
-- of accounts/individual_profiles). briefs inherits that same dependency, so
-- reusing it here would mean resurrecting the whole accounts/account_members
-- system just to post one brief. Keeping that precedent: exchange_briefs below
-- is a fresh, simple table keyed on public.users(id), same as posts/follows/
-- member_connections. public.briefs is left exactly as it was -- untouched,
-- still dormant, not deleted, in case the accounts system is adopted later.

begin;

-- ---- Marketplace ---------------------------------------------------------

create table if not exists public.marketplace_listings (
  id          uuid primary key default gen_random_uuid(),
  seller_id   uuid not null references public.users(id) on delete cascade,
  title       text not null,
  category    text,
  price_text  text,     -- free text ("₹1,20,000", "₹45/ream") -- goods pricing varies too much for one numeric column
  description text,
  location    text,
  photo_urls  text[],
  status      text not null default 'active' check (status in ('active','sold','removed')),
  created_at  timestamptz not null default now()
);

create index if not exists marketplace_listings_seller_idx on public.marketplace_listings(seller_id);
create index if not exists marketplace_listings_status_idx on public.marketplace_listings(status);

create table if not exists public.marketplace_inquiries (
  id          uuid primary key default gen_random_uuid(),
  listing_id  uuid not null references public.marketplace_listings(id) on delete cascade,
  buyer_id    uuid not null references public.users(id) on delete cascade,
  message     text not null,
  created_at  timestamptz not null default now()
);

create index if not exists marketplace_inquiries_listing_idx on public.marketplace_inquiries(listing_id);

-- ---- The Exchange ---------------------------------------------------------

create table if not exists public.exchange_briefs (
  id           uuid primary key default gen_random_uuid(),
  author_id    uuid not null references public.users(id) on delete cascade,
  brief_type   text not null check (brief_type in ('service_request','strategy_team','business_for_sale','vc_interest')),
  description  text not null,
  bucket_id    uuid references public.buckets(id),
  anonymous    boolean not null default false,
  status       text not null default 'open' check (status in ('open','matched','closed')),
  created_at   timestamptz not null default now()
);

create index if not exists exchange_briefs_author_idx on public.exchange_briefs(author_id);
create index if not exists exchange_briefs_status_idx on public.exchange_briefs(status);

create table if not exists public.exchange_brief_responses (
  id          uuid primary key default gen_random_uuid(),
  brief_id    uuid not null references public.exchange_briefs(id) on delete cascade,
  responder_id uuid not null references public.users(id) on delete cascade,
  message     text,
  created_at  timestamptz not null default now()
);

create index if not exists exchange_brief_responses_brief_idx on public.exchange_brief_responses(brief_id);

-- ---- Events ----------------------------------------------------------------

create table if not exists public.events (
  id                 uuid primary key default gen_random_uuid(),
  host_user_id       uuid references public.users(id) on delete set null,
  host_label         text,          -- display name when hosted "as" an org, e.g. "Mehta & Co Advocates"
  title              text not null,
  description        text,
  starts_at          timestamptz not null,
  ends_at            timestamptz,
  location           text,
  is_virtual         boolean not null default false,
  restricted_to_community_id uuid references public.communities(id),  -- null = open to all active members
  created_at         timestamptz not null default now()
);

create index if not exists events_starts_at_idx on public.events(starts_at);

create table if not exists public.event_rsvps (
  event_id   uuid not null references public.events(id) on delete cascade,
  user_id    uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (event_id, user_id)
);

-- ---- RLS -------------------------------------------------------------------

alter table public.marketplace_listings   enable row level security;
alter table public.marketplace_inquiries  enable row level security;
alter table public.exchange_briefs        enable row level security;
alter table public.exchange_brief_responses enable row level security;
alter table public.events                 enable row level security;
alter table public.event_rsvps            enable row level security;

drop policy if exists marketplace_listings_select_all on public.marketplace_listings;
create policy marketplace_listings_select_all on public.marketplace_listings for select using (true);
drop policy if exists marketplace_listings_insert_own on public.marketplace_listings;
create policy marketplace_listings_insert_own on public.marketplace_listings for insert with check (
  seller_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists marketplace_listings_update_own on public.marketplace_listings;
create policy marketplace_listings_update_own on public.marketplace_listings for update using (
  seller_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
);

drop policy if exists marketplace_inquiries_select_participant on public.marketplace_inquiries;
create policy marketplace_inquiries_select_participant on public.marketplace_inquiries for select using (
  buyer_id in (select id from public.users where auth_id = auth.uid())
  or exists (select 1 from public.marketplace_listings l where l.id = marketplace_inquiries.listing_id
             and l.seller_id in (select id from public.users where auth_id = auth.uid()))
);
drop policy if exists marketplace_inquiries_insert_own on public.marketplace_inquiries;
create policy marketplace_inquiries_insert_own on public.marketplace_inquiries for insert with check (
  buyer_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists exchange_briefs_select_all on public.exchange_briefs;
create policy exchange_briefs_select_all on public.exchange_briefs for select using (true);
drop policy if exists exchange_briefs_insert_own on public.exchange_briefs;
create policy exchange_briefs_insert_own on public.exchange_briefs for insert with check (
  author_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists exchange_briefs_update_own on public.exchange_briefs;
create policy exchange_briefs_update_own on public.exchange_briefs for update using (
  author_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
);

drop policy if exists exchange_brief_responses_select_participant on public.exchange_brief_responses;
create policy exchange_brief_responses_select_participant on public.exchange_brief_responses for select using (
  responder_id in (select id from public.users where auth_id = auth.uid())
  or exists (select 1 from public.exchange_briefs b where b.id = exchange_brief_responses.brief_id
             and b.author_id in (select id from public.users where auth_id = auth.uid()))
);
drop policy if exists exchange_brief_responses_insert_own on public.exchange_brief_responses;
create policy exchange_brief_responses_insert_own on public.exchange_brief_responses for insert with check (
  responder_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists events_select_all on public.events;
create policy events_select_all on public.events for select using (true);
-- Original version only checked auth.role() = 'authenticated' with no tie
-- to host_user_id at all -- any signed-in member could have created an
-- event crediting a DIFFERENT member as host. Require host_user_id be
-- either null (admin-posted, no personal host) or the caller themselves.
drop policy if exists events_insert_authenticated on public.events;
create policy events_insert_authenticated on public.events for insert with check (
  host_user_id is null
  or host_user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists events_update_host_or_admin on public.events;
create policy events_update_host_or_admin on public.events for update using (
  host_user_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
);

drop policy if exists event_rsvps_select_all on public.event_rsvps;
create policy event_rsvps_select_all on public.event_rsvps for select using (true);
drop policy if exists event_rsvps_insert_own on public.event_rsvps;
create policy event_rsvps_insert_own on public.event_rsvps for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists event_rsvps_delete_own on public.event_rsvps;
create policy event_rsvps_delete_own on public.event_rsvps for delete using (
  user_id in (select id from public.users where auth_id = auth.uid())
);

commit;
