-- Mahayukti Phase 1 — multi-account-type signup + briefs/brief_candidates/introductions primitive
-- Built from: "Mahayukti: System Architecture" (Section 2, "Data model") and "Strategic Plan" docs.
--
-- Scope of this migration (deliberately limited to what's in this pass — see session report):
--   1. accounts / account_members / {individual,corporate,institution,ngo,government}_profiles
--   2. buckets (static reference, seeded with the 12 live on mahayukti.com) + verification_rules
--   3. briefs / brief_buckets / brief_candidates / introductions (the shared matching primitive)
--   4. RLS on every new table, plus two SECURITY DEFINER RPCs that implement "the system runs a
--      matching query" and "an introduction event fires" from the architecture doc (Section 4).
--
-- Explicitly NOT in this migration (deferred, see report): KYC vendor integration (verifications/
-- peer_vouches/promotion_reviews tables), feed/chat (posts/comments/conversations/messages),
-- Strategy Teams rosters, services marketplace listings/engagements, business-for-sale/VC listings.
-- These are additive later migrations against the same accounts/briefs primitive — nothing here
-- blocks them.
--
-- This file is idempotent (IF NOT EXISTS / ON CONFLICT everywhere) so it is safe to re-run.

begin;

create extension if not exists pgcrypto;

-- =========================================================================
-- 1. Buckets (static reference table — the 12 buckets live on mahayukti.com)
-- =========================================================================

create table if not exists public.buckets (
  id    uuid primary key default gen_random_uuid(),
  slug  text not null unique,
  name  text not null,
  sort_order int not null
);

insert into public.buckets (slug, name, sort_order) values
  ('legal',                 'Legal',                          1),
  ('accounting-audit',      'Accounting & Audit',              2),
  ('technology',            'Technology & Cybersecurity',      3),
  ('capital-funding',       'Capital & Funding',               4),
  ('business-industry',     'Business & Industry',             5),
  ('government-affairs',    'Government & Public Affairs',     6),
  ('defence-security',      'Defence & Security',               7),
  ('culture-influence',     'Culture & Public Influence',      8),
  ('trades-craft',          'Trades & Craft',                   9),
  ('science-deep-tech',     'Science & Deep-Tech',            10),
  ('healthcare-medicine',   'Healthcare & Medicine',           11),
  ('real-estate-infra',     'Real Estate & Infrastructure',    12)
on conflict (slug) do nothing;

-- =========================================================================
-- 2. Accounts / account_members / profile tables
-- =========================================================================

create table if not exists public.accounts (
  id                 uuid primary key default gen_random_uuid(),
  account_type       text not null check (account_type in ('individual','corporate','institution','ngo','government')),
  status             text not null default 'pending' check (status in ('pending','approved','rejected','suspended')),
  auth_user_id       uuid not null unique references auth.users(id) on delete cascade,
  profile_extensions jsonb not null default '{}'::jsonb,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index if not exists accounts_account_type_idx on public.accounts(account_type);
create index if not exists accounts_status_idx on public.accounts(status);

create table if not exists public.account_members (
  id           uuid primary key default gen_random_uuid(),
  account_id   uuid not null references public.accounts(id) on delete cascade,
  auth_user_id uuid not null references auth.users(id) on delete cascade,
  role         text not null default 'owner' check (role in ('owner','admin','member')),
  created_at   timestamptz not null default now(),
  unique (account_id, auth_user_id)
);

create table if not exists public.individual_profiles (
  account_id        uuid primary key references public.accounts(id) on delete cascade,
  name              text not null,
  headline          text,
  bucket_id         uuid references public.buckets(id),
  tier              text not null default 'member' check (tier in ('member','participant','bucket_head','council')),
  work_email_domain text,
  promoted_at       timestamptz,
  promoted_by       uuid references public.accounts(id)
);

create table if not exists public.corporate_profiles (
  account_id       uuid primary key references public.accounts(id) on delete cascade,
  legal_name       text not null,
  cin              text,
  gstin            text,
  sponsor_bucket_id uuid references public.buckets(id),
  verified_via     text check (verified_via in ('domain','cin_gst_lookup','manual_review'))
);

create table if not exists public.institution_profiles (
  account_id                 uuid primary key references public.accounts(id) on delete cascade,
  legal_name                 text not null,
  institution_type           text check (institution_type in ('chamber','bar_council','university','association','other')),
  authorized_signatory_name  text not null,
  attestation_ref            text,
  bulk_invite_consent_ref    text
);

create table if not exists public.ngo_profiles (
  account_id       uuid primary key references public.accounts(id) on delete cascade,
  legal_name       text not null,
  ngo_darpan_id    text,
  section_80g_ref  text
);

create table if not exists public.government_profiles (
  account_id              uuid primary key references public.accounts(id) on delete cascade,
  department_name         text not null,
  official_domain         text,
  authorized_officer_name text not null
);

-- Data-driven verification routing (architecture doc Section 2: "a new account type is mostly
-- configuration, not new code"). Not yet consumed by backend code in this pass — see report —
-- but the table exists so Phase 1 signup logic has one place to read routing rules from.
create table if not exists public.verification_rules (
  account_type          text primary key check (account_type in ('individual','corporate','institution','ngo','government')),
  method                text not null,
  requires_admin_review boolean not null default true,
  notes                 text
);

insert into public.verification_rules (account_type, method, requires_admin_review, notes) values
  ('individual',  'work_email_otp',   true,  'Baseline OTP today; admin approve/reject as already shipped.'),
  ('corporate',   'cin_gst_lookup',   true,  'No usable free/instant public CIN or GST verification API was found this session (MCA blocks automated access, GSTN search is captcha-gated with no public API). Field capture only; falls back to manual admin review, same pending/approve queue as individual.'),
  ('institution', 'attestation',      true,  'Authorized-signatory attestation read by a human admin.'),
  ('ngo',         'ngo_darpan_80g',   true,  'NGO Darpan / 80G reference read by a human admin — no automated lookup wired.'),
  ('government',  'official_domain',  true,  'Heavier manual bar; .gov.in/.nic.in domain + named officer read by a human admin.')
on conflict (account_type) do nothing;

-- =========================================================================
-- 3. The shared briefs -> brief_candidates -> introductions primitive
-- =========================================================================

create table if not exists public.briefs (
  id                uuid primary key default gen_random_uuid(),
  client_account_id uuid not null references public.accounts(id) on delete cascade,
  brief_type        text not null check (brief_type in ('strategy_team','service_request','business_sale_interest','vc_interest')),
  description       text not null,
  status            text not null default 'open' check (status in ('open','matched','closed')),
  created_at        timestamptz not null default now()
);

create index if not exists briefs_client_account_idx on public.briefs(client_account_id);
create index if not exists briefs_status_idx on public.briefs(status);

create table if not exists public.brief_buckets (
  brief_id  uuid not null references public.briefs(id) on delete cascade,
  bucket_id uuid not null references public.buckets(id) on delete cascade,
  primary key (brief_id, bucket_id)
);
create index if not exists brief_buckets_bucket_idx on public.brief_buckets(bucket_id);

create table if not exists public.brief_candidates (
  id                 uuid primary key default gen_random_uuid(),
  brief_id           uuid not null references public.briefs(id) on delete cascade,
  candidate_account_id uuid not null references public.accounts(id) on delete cascade,
  match_score        numeric,
  status             text not null default 'suggested' check (status in ('suggested','contacted','declined','engaged')),
  created_at         timestamptz not null default now(),
  unique (brief_id, candidate_account_id)
);
create index if not exists brief_candidates_brief_idx on public.brief_candidates(brief_id);
create index if not exists brief_candidates_candidate_idx on public.brief_candidates(candidate_account_id);

create table if not exists public.introductions (
  id                 uuid primary key default gen_random_uuid(),
  brief_id           uuid not null references public.briefs(id) on delete cascade,
  candidate_account_id uuid not null references public.accounts(id) on delete cascade,
  introduced_at      timestamptz not null default now(),
  introduced_by      uuid references public.accounts(id), -- null = system
  outcome            text not null default 'pending' check (outcome in ('pending','accepted','declined')),
  unique (brief_id, candidate_account_id)
);
create index if not exists introductions_brief_idx on public.introductions(brief_id);

-- =========================================================================
-- 4. Admin bridge: reuse the existing `users.role = 'admin'` concept
-- =========================================================================
-- The live app.html admin flow already treats a row in public.users with role='admin' and
-- status='active' as a platform admin. Rather than invent a second admin system for the new
-- tables, this function bridges to that existing concept so RLS below can use one check.
create or replace function public.is_platform_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.users u
    where u.auth_id = auth.uid() and u.role = 'admin' and u.status = 'active'
  );
$$;

-- =========================================================================
-- 5. Row Level Security
-- =========================================================================

alter table public.buckets enable row level security;
alter table public.verification_rules enable row level security;
alter table public.accounts enable row level security;
alter table public.account_members enable row level security;
alter table public.individual_profiles enable row level security;
alter table public.corporate_profiles enable row level security;
alter table public.institution_profiles enable row level security;
alter table public.ngo_profiles enable row level security;
alter table public.government_profiles enable row level security;
alter table public.briefs enable row level security;
alter table public.brief_buckets enable row level security;
alter table public.brief_candidates enable row level security;
alter table public.introductions enable row level security;

-- buckets / verification_rules: public read, admin write
drop policy if exists buckets_select_all on public.buckets;
create policy buckets_select_all on public.buckets for select using (true);
drop policy if exists buckets_admin_write on public.buckets;
create policy buckets_admin_write on public.buckets for all using (public.is_platform_admin()) with check (public.is_platform_admin());

drop policy if exists verification_rules_select_all on public.verification_rules;
create policy verification_rules_select_all on public.verification_rules for select using (true);
drop policy if exists verification_rules_admin_write on public.verification_rules;
create policy verification_rules_admin_write on public.verification_rules for all using (public.is_platform_admin()) with check (public.is_platform_admin());

-- accounts: owner (by auth_user_id or account_members) + admin can read; owner inserts own row;
-- only admin changes status (approve/reject)
drop policy if exists accounts_select_own_or_admin on public.accounts;
create policy accounts_select_own_or_admin on public.accounts for select using (
  auth_user_id = auth.uid()
  or exists (select 1 from public.account_members m where m.account_id = accounts.id and m.auth_user_id = auth.uid())
  or public.is_platform_admin()
);

drop policy if exists accounts_insert_self on public.accounts;
create policy accounts_insert_self on public.accounts for insert with check (auth_user_id = auth.uid());

drop policy if exists accounts_update_admin on public.accounts;
create policy accounts_update_admin on public.accounts for update using (public.is_platform_admin()) with check (public.is_platform_admin());

-- account_members: visible/insertable to members of the same account or admin
drop policy if exists account_members_select on public.account_members;
create policy account_members_select on public.account_members for select using (
  auth_user_id = auth.uid()
  or exists (select 1 from public.accounts a where a.id = account_members.account_id and a.auth_user_id = auth.uid())
  or public.is_platform_admin()
);
drop policy if exists account_members_insert on public.account_members;
create policy account_members_insert on public.account_members for insert with check (
  auth_user_id = auth.uid()
  and exists (select 1 from public.accounts a where a.id = account_members.account_id and a.auth_user_id = auth.uid())
);

-- Profile tables: a helper pattern repeated per table — owner (via accounts.auth_user_id) or
-- admin can read/write; everyone authenticated can read an *approved* individual_profiles row
-- (needed for the brief-matching UI to show candidates and for public member browsing).
drop policy if exists individual_profiles_select on public.individual_profiles;
create policy individual_profiles_select on public.individual_profiles for select using (
  exists (select 1 from public.accounts a where a.id = individual_profiles.account_id and (a.auth_user_id = auth.uid() or a.status = 'approved'))
  or public.is_platform_admin()
);
drop policy if exists individual_profiles_insert on public.individual_profiles;
create policy individual_profiles_insert on public.individual_profiles for insert with check (
  exists (select 1 from public.accounts a where a.id = individual_profiles.account_id and a.auth_user_id = auth.uid() and a.account_type = 'individual')
);
drop policy if exists individual_profiles_update on public.individual_profiles;
create policy individual_profiles_update on public.individual_profiles for update using (
  exists (select 1 from public.accounts a where a.id = individual_profiles.account_id and a.auth_user_id = auth.uid())
  or public.is_platform_admin()
);

do $$
declare
  t text;
begin
  for t in select unnest(array['corporate_profiles','institution_profiles','ngo_profiles','government_profiles'])
  loop
    execute format($f$
      drop policy if exists %1$I_select on public.%1$I;
      create policy %1$I_select on public.%1$I for select using (
        exists (select 1 from public.accounts a where a.id = %1$I.account_id and a.auth_user_id = auth.uid())
        or public.is_platform_admin()
      );
      drop policy if exists %1$I_insert on public.%1$I;
      create policy %1$I_insert on public.%1$I for insert with check (
        exists (select 1 from public.accounts a where a.id = %1$I.account_id and a.auth_user_id = auth.uid())
      );
      drop policy if exists %1$I_update on public.%1$I;
      create policy %1$I_update on public.%1$I for update using (
        exists (select 1 from public.accounts a where a.id = %1$I.account_id and a.auth_user_id = auth.uid())
        or public.is_platform_admin()
      );
    $f$, t);
  end loop;
end $$;

-- briefs: owner (client_account_id) or admin can see/manage; a suggested candidate can see the
-- brief they were matched against
drop policy if exists briefs_select on public.briefs;
create policy briefs_select on public.briefs for select using (
  exists (select 1 from public.accounts a where a.id = briefs.client_account_id and a.auth_user_id = auth.uid())
  or exists (
    select 1 from public.brief_candidates bc
    join public.accounts a on a.id = bc.candidate_account_id
    where bc.brief_id = briefs.id and a.auth_user_id = auth.uid()
  )
  or public.is_platform_admin()
);
drop policy if exists briefs_insert on public.briefs;
create policy briefs_insert on public.briefs for insert with check (
  exists (select 1 from public.accounts a where a.id = briefs.client_account_id and a.auth_user_id = auth.uid() and a.status = 'approved')
);
drop policy if exists briefs_update on public.briefs;
create policy briefs_update on public.briefs for update using (
  exists (select 1 from public.accounts a where a.id = briefs.client_account_id and a.auth_user_id = auth.uid())
  or public.is_platform_admin()
);

drop policy if exists brief_buckets_select on public.brief_buckets;
create policy brief_buckets_select on public.brief_buckets for select using (
  exists (select 1 from public.briefs b where b.id = brief_buckets.brief_id)
);
drop policy if exists brief_buckets_insert on public.brief_buckets;
create policy brief_buckets_insert on public.brief_buckets for insert with check (
  exists (
    select 1 from public.briefs b
    join public.accounts a on a.id = b.client_account_id
    where b.id = brief_buckets.brief_id and a.auth_user_id = auth.uid()
  )
);

-- brief_candidates / introductions are written only through the SECURITY DEFINER RPCs below,
-- not directly by client inserts (this is "the system runs a matching query", not the client
-- deciding its own matches) — so there is no insert policy for ordinary users here, only select.
drop policy if exists brief_candidates_select on public.brief_candidates;
create policy brief_candidates_select on public.brief_candidates for select using (
  exists (select 1 from public.accounts a where a.id = brief_candidates.candidate_account_id and a.auth_user_id = auth.uid())
  or exists (
    select 1 from public.briefs b join public.accounts a on a.id = b.client_account_id
    where b.id = brief_candidates.brief_id and a.auth_user_id = auth.uid()
  )
  or public.is_platform_admin()
);

drop policy if exists introductions_select on public.introductions;
create policy introductions_select on public.introductions for select using (
  exists (select 1 from public.accounts a where a.id = introductions.candidate_account_id and a.auth_user_id = auth.uid())
  or exists (
    select 1 from public.briefs b join public.accounts a on a.id = b.client_account_id
    where b.id = introductions.brief_id and a.auth_user_id = auth.uid()
  )
  or public.is_platform_admin()
);

-- =========================================================================
-- 6. RPCs: the matching query + introduction event (architecture doc Section 4)
-- =========================================================================

-- Runs the shared matching query: approved individual_profiles whose bucket matches one of the
-- brief's buckets, not already matched, inserted into brief_candidates. Callable only by the
-- brief's own client (or an admin), via supabase.rpc('match_brief_candidates', {p_brief_id: ...}).
create or replace function public.match_brief_candidates(p_brief_id uuid)
returns setof public.brief_candidates
language plpgsql
security definer
set search_path = public
as $$
declare
  v_ok boolean;
begin
  select exists (
    select 1 from public.briefs b
    join public.accounts a on a.id = b.client_account_id
    where b.id = p_brief_id and (a.auth_user_id = auth.uid() or public.is_platform_admin())
  ) into v_ok;

  if not v_ok then
    raise exception 'not authorized to match this brief';
  end if;

  return query
  insert into public.brief_candidates (brief_id, candidate_account_id, match_score, status)
  select
    p_brief_id,
    ip.account_id,
    1.0 as match_score, -- plain bucket match today; Section 4 names pgvector/full-text as the future upgrade, not needed at this scale
    'suggested'
  from public.individual_profiles ip
  join public.accounts a on a.id = ip.account_id
  where a.status = 'approved'
    and ip.bucket_id in (select bucket_id from public.brief_buckets where brief_id = p_brief_id)
    and ip.account_id <> (select client_account_id from public.briefs where id = p_brief_id)
  on conflict (brief_id, candidate_account_id) do nothing
  returning *;
end;
$$;

-- Fires the introduction event once a brief owner picks a candidate. Callable by the brief's own
-- client (or an admin) via supabase.rpc('create_introduction', {p_brief_id, p_candidate_account_id}).
create or replace function public.create_introduction(p_brief_id uuid, p_candidate_account_id uuid)
returns public.introductions
language plpgsql
security definer
set search_path = public
as $$
declare
  v_ok boolean;
  v_row public.introductions;
  v_introducer uuid;
begin
  select a.id into v_introducer
  from public.briefs b join public.accounts a on a.id = b.client_account_id
  where b.id = p_brief_id and a.auth_user_id = auth.uid();

  select (v_introducer is not null) or public.is_platform_admin() into v_ok;
  if not v_ok then
    raise exception 'not authorized to introduce on this brief';
  end if;

  insert into public.introductions (brief_id, candidate_account_id, introduced_by)
  values (p_brief_id, p_candidate_account_id, v_introducer)
  on conflict (brief_id, candidate_account_id) do update set introduced_at = public.introductions.introduced_at
  returning * into v_row;

  update public.brief_candidates set status = 'contacted'
  where brief_id = p_brief_id and candidate_account_id = p_candidate_account_id and status = 'suggested';

  return v_row;
end;
$$;

grant execute on function public.match_brief_candidates(uuid) to authenticated;
grant execute on function public.create_introduction(uuid, uuid) to authenticated;
grant execute on function public.is_platform_admin() to authenticated, anon;

commit;
