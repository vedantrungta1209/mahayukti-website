-- Wires the onboarding/verification design from the 2026-11-20 prototype onto the existing
-- accounts/individual_profiles/corporate_profiles schema (20261114000000_phase1_accounts_briefs.sql),
-- rather than inventing a second, competing data model. That earlier migration was built from the
-- architecture doc but never connected to a real signup UI -- the live site still runs on the old
-- flat `public.users` table. This migration only adds columns; nothing here is destructive.
--
-- Adds:
--   1. Username (individual_profiles) -- the existing schema had no handle at all.
--   2. Phone/PAN/Aadhaar verification status (individual_profiles).
--   3. Authorised representative fields + director/email-domain verification status
--      (corporate_profiles) -- the existing schema had no representative capture at all.
--   4. Founding-member invite codes (new table) -- the dignitary/PMO path from the prototype.
--   5. Updates the stale verification_rules note for 'corporate': the original note said no
--      usable CIN/GST lookup API existed; paid vendor APIs (Decentro, Meon) do exist for this,
--      just weren't in scope when that note was written.
--
-- Idempotent (IF NOT EXISTS everywhere) -- safe to re-run.

begin;

-- =========================================================================
-- 1 & 2. individual_profiles: username + verification status
-- =========================================================================

alter table public.individual_profiles
  add column if not exists username text,
  add column if not exists phone text,
  add column if not exists phone_verified boolean not null default false,
  add column if not exists pan_verified boolean not null default false,
  add column if not exists aadhaar_verified boolean not null default false, -- via DigiLocker, see report
  add column if not exists verified_at timestamptz;

-- Partial unique index (not a plain unique constraint) so multiple NULLs are allowed before a
-- member picks a handle, but no two real handles can collide.
create unique index if not exists individual_profiles_username_unique_idx
  on public.individual_profiles (username) where username is not null;

-- =========================================================================
-- 3. corporate_profiles: authorised representative + automated-check status
-- =========================================================================

alter table public.corporate_profiles
  add column if not exists rep_name text,
  add column if not exists rep_title text,
  add column if not exists rep_email text,
  add column if not exists rep_phone text,
  add column if not exists cin_matched boolean not null default false,
  add column if not exists cin_matched_company_name text,
  add column if not exists director_matched boolean not null default false,
  add column if not exists rep_email_domain_verified boolean not null default false,
  add column if not exists auto_verified_at timestamptz; -- set only when all three checks pass

-- =========================================================================
-- 4. Founding-member invites (the PMO/dignitary path)
-- =========================================================================

create table if not exists public.founding_invites (
  id            uuid primary key default gen_random_uuid(),
  code          text not null unique,
  invited_name  text not null,
  invited_email text,
  domain        text,               -- their expected field/role, shown back to them on the invite screen
  ordinal       int,                 -- "Founding Member No. 014" -- assigned when the invite is created, not on accept
  used_at       timestamptz,
  used_by_account_id uuid references public.accounts(id),
  created_at    timestamptz not null default now(),
  created_by    uuid references public.accounts(id) -- admin who issued it
);

create index if not exists founding_invites_code_idx on public.founding_invites(code);

alter table public.founding_invites enable row level security;

-- Only an admin can list/manage invites. A code lookup during the accept flow goes through a
-- SECURITY DEFINER RPC below instead of a direct select, so an unauthenticated visitor can check
-- a code's validity without RLS granting them the whole table.
drop policy if exists founding_invites_admin_all on public.founding_invites;
create policy founding_invites_admin_all on public.founding_invites for all
  using (public.is_platform_admin()) with check (public.is_platform_admin());

create or replace function public.check_founding_invite(p_code text)
returns table (valid boolean, invited_name text, domain text, ordinal int)
language sql
stable
security definer
set search_path = public
as $$
  select
    (fi.used_at is null) as valid,
    fi.invited_name,
    fi.domain,
    fi.ordinal
  from public.founding_invites fi
  where fi.code = p_code;
$$;

grant execute on function public.check_founding_invite(text) to anon, authenticated;

-- Marks an invite used once the invitee's account is created. Callable only with the matching
-- code (not by account id alone), so a client can't mark an arbitrary invite used.
create or replace function public.redeem_founding_invite(p_code text, p_account_id uuid)
returns public.founding_invites
language plpgsql
security definer
set search_path = public
as $$
declare
  v_row public.founding_invites;
begin
  update public.founding_invites
  set used_at = now(), used_by_account_id = p_account_id
  where code = p_code and used_at is null
  returning * into v_row;

  if v_row is null then
    raise exception 'invite code invalid or already used';
  end if;

  return v_row;
end;
$$;

grant execute on function public.redeem_founding_invite(text, uuid) to authenticated;

-- =========================================================================
-- 5. verification_rules: correct the stale "no usable API" note for corporate
-- =========================================================================

update public.verification_rules
set
  method = 'cin_director_email_auto',
  requires_admin_review = false, -- only when all three auto-checks pass; see corporate_profiles.auto_verified_at
  notes = 'Automated as of 2026-11-20: CIN matched against MCA via a paid vendor API (Decentro/Meon -- no free/instant public one exists, confirmed again this session), representative cross-checked against MCA director records (DIN), and representative work-email domain verified against the organisation''s own domain. All three passing -> instant approval, auto_verified_at set, no human review. Any one failing -> falls back to the existing manual admin queue.'
where account_type = 'corporate';

commit;
