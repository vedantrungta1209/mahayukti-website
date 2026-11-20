-- Ad campaigns (wrapping a sponsored post), member-level API keys, admin
-- platform-partner approvals, and post moderation reports.

begin;

-- ---- Ads -------------------------------------------------------------------
-- posts.is_sponsored / posts.sponsor_user_id already exist (social-core
-- migration) -- a sponsored post IS a post. ad_campaigns adds the
-- targeting/budget/review wrapper around one.

create table if not exists public.ad_campaigns (
  id               uuid primary key default gen_random_uuid(),
  post_id          uuid references public.posts(id) on delete cascade,
  advertiser_id    uuid not null references public.users(id) on delete cascade,
  target_bucket_ids uuid[],
  daily_budget     numeric,
  duration_days    int,
  status           text not null default 'pending_review' check (status in ('pending_review','active','paused','ended','rejected')),
  created_at       timestamptz not null default now()
);

create index if not exists ad_campaigns_advertiser_idx on public.ad_campaigns(advertiser_id);
create index if not exists ad_campaigns_status_idx on public.ad_campaigns(status);

-- ---- Member-level API keys --------------------------------------------------
-- Only a hash is ever stored -- the raw key is shown to the member once, at
-- creation, client-side, and never persisted in plaintext. Matches the
-- pattern used for every other secret in this app (no plaintext tokens in
-- a table that RLS alone protects).

create table if not exists public.api_keys (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.users(id) on delete cascade,
  label       text,
  key_hash    text not null,
  scopes      text[] not null default array[]::text[],
  last_used_at timestamptz,
  created_at  timestamptz not null default now(),
  revoked_at  timestamptz
);

create unique index if not exists api_keys_hash_idx on public.api_keys(key_hash);
create index if not exists api_keys_user_idx on public.api_keys(user_id);

-- ---- Admin: platform partner (third-party app) approvals -------------------

create table if not exists public.platform_partners (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  contact_email    text,
  requested_scopes text[],
  kind             text not null default 'publishing' check (kind in ('publishing','data_partner')),
  status           text not null default 'pending' check (status in ('pending','approved','denied')),
  notes            text,
  created_at       timestamptz not null default now(),
  decided_at       timestamptz
);

-- ---- Post moderation reports -------------------------------------------------

create table if not exists public.post_reports (
  id          uuid primary key default gen_random_uuid(),
  post_id     uuid not null references public.posts(id) on delete cascade,
  reporter_id uuid not null references public.users(id) on delete cascade,
  reason      text not null,
  detail      text,
  status      text not null default 'open' check (status in ('open','resolved_removed','resolved_dismissed','resolved_warned')),
  created_at  timestamptz not null default now(),
  resolved_at timestamptz,
  resolved_by uuid references public.users(id)
);

create index if not exists post_reports_status_idx on public.post_reports(status);
create index if not exists post_reports_post_idx on public.post_reports(post_id);

-- ---- RLS ---------------------------------------------------------------------

alter table public.ad_campaigns      enable row level security;
alter table public.api_keys          enable row level security;
alter table public.platform_partners enable row level security;
alter table public.post_reports      enable row level security;

drop policy if exists ad_campaigns_select_own_or_admin on public.ad_campaigns;
create policy ad_campaigns_select_own_or_admin on public.ad_campaigns for select using (
  advertiser_id in (select id from public.users where auth_id = auth.uid()) or public.is_platform_admin()
);
drop policy if exists ad_campaigns_insert_own on public.ad_campaigns;
create policy ad_campaigns_insert_own on public.ad_campaigns for insert with check (
  advertiser_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists ad_campaigns_update_admin on public.ad_campaigns;
create policy ad_campaigns_update_admin on public.ad_campaigns for update using (public.is_platform_admin());
-- Everyone needs to see an ACTIVE sponsored post's own row in the feed query,
-- but never another member's pending/rejected campaign details.
drop policy if exists ad_campaigns_select_active_public on public.ad_campaigns;
create policy ad_campaigns_select_active_public on public.ad_campaigns for select using (status = 'active');

drop policy if exists api_keys_select_own on public.api_keys;
create policy api_keys_select_own on public.api_keys for select using (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists api_keys_insert_own on public.api_keys;
create policy api_keys_insert_own on public.api_keys for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists api_keys_update_own on public.api_keys;
create policy api_keys_update_own on public.api_keys for update using (
  user_id in (select id from public.users where auth_id = auth.uid())
) with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists platform_partners_select_admin on public.platform_partners;
create policy platform_partners_select_admin on public.platform_partners for select using (public.is_platform_admin());
drop policy if exists platform_partners_write_admin on public.platform_partners;
create policy platform_partners_write_admin on public.platform_partners for all using (public.is_platform_admin()) with check (public.is_platform_admin());

drop policy if exists post_reports_insert_own on public.post_reports;
create policy post_reports_insert_own on public.post_reports for insert with check (
  reporter_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists post_reports_select_admin on public.post_reports;
create policy post_reports_select_admin on public.post_reports for select using (public.is_platform_admin());
drop policy if exists post_reports_update_admin on public.post_reports;
create policy post_reports_update_admin on public.post_reports for update using (public.is_platform_admin());

commit;
