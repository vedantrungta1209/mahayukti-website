-- Wires the onboarding/verification design from the 2026-11-20 prototype onto the LIVE
-- `public.users` table -- the one app.html's apply/login/admin flow actually reads and writes.
--
-- Correction from the first version of this migration: it originally targeted
-- accounts/individual_profiles/corporate_profiles (20261114000000_phase1_accounts_briefs.sql).
-- That schema was built from the architecture doc for a future multi-account-type model, but was
-- NEVER connected to any real UI, and flipping the whole live app onto it (directory, profiles,
-- messaging, admin review all currently query `users`) is a much bigger, separate undertaking --
-- not something to fold into this feature. This migration never reached production, so rewriting
-- it in place is safe; no live data is affected either way.
--
-- `public.users` already has `username` (unique), `founding_member`, and `founding_approved`
-- columns (20261113235900_users_bootstrap.sql) -- reused here, not duplicated.
--
-- Adds:
--   1. Phone/PAN/Aadhaar verification status on `users`.
--   2. An `account_kind` discriminator ('individual' | 'organisation') plus organisation-specific
--      fields (CIN, authorised representative, automated-check status) on the SAME table, rather
--      than a second table -- consistent with how the rest of the live app already treats
--      `organisation` as a field on one flat row, not a distinct entity.
--   3. Founding-member invite codes (new table), referencing `public.users` instead of the
--      unused `public.accounts`.
--
-- Idempotent (IF NOT EXISTS everywhere) -- safe to re-run.

begin;

-- =========================================================================
-- 1. Individual verification status
-- =========================================================================

alter table public.users
  add column if not exists phone_verified boolean not null default false,
  add column if not exists pan_verified boolean not null default false,
  add column if not exists aadhaar_verified boolean not null default false, -- via DigiLocker, see report
  add column if not exists verified_at timestamptz;

-- =========================================================================
-- 2. Organisation accounts, on the same table
-- =========================================================================

alter table public.users
  add column if not exists account_kind text not null default 'individual'
    check (account_kind in ('individual', 'organisation')),
  add column if not exists cin text,
  add column if not exists cin_matched boolean not null default false,
  add column if not exists cin_matched_company_name text,
  add column if not exists rep_name text,
  add column if not exists rep_title text,
  add column if not exists rep_email text,
  add column if not exists rep_phone text,
  add column if not exists director_matched boolean not null default false,
  add column if not exists rep_email_domain_verified boolean not null default false,
  add column if not exists auto_verified_at timestamptz; -- set only when cin+director+email all pass

create index if not exists users_account_kind_idx on public.users(account_kind);

-- =========================================================================
-- 3. Founding-member invites (the PMO/dignitary path)
-- =========================================================================

create table if not exists public.founding_invites (
  id            uuid primary key default gen_random_uuid(),
  code          text not null unique,
  invited_name  text not null,
  invited_email text,
  domain        text,               -- their expected field/role, shown back to them on the invite screen
  ordinal       int,                 -- "Founding Member No. 014" -- assigned when the invite is created, not on accept
  used_at       timestamptz,
  used_by_user_id uuid references public.users(id),
  created_at    timestamptz not null default now(),
  created_by    uuid references public.users(id) -- admin who issued it
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

-- Marks an invite used once the invitee's own `users` row is created. Callable only with the
-- matching code (not by user id alone), so a client can't mark an arbitrary invite used. Also
-- flips founding_member/founding_approved on that user, so the existing (already-live) columns
-- drive the UI, nothing new to read elsewhere.
create or replace function public.redeem_founding_invite(p_code text, p_user_id uuid)
returns public.founding_invites
language plpgsql
security definer
set search_path = public
as $$
declare
  v_row public.founding_invites;
begin
  update public.founding_invites
  set used_at = now(), used_by_user_id = p_user_id
  where code = p_code and used_at is null
  returning * into v_row;

  if v_row is null then
    raise exception 'invite code invalid or already used';
  end if;

  update public.users
  set founding_member = true, founding_approved = true, status = 'active'
  where id = p_user_id;

  return v_row;
end;
$$;

grant execute on function public.redeem_founding_invite(text, uuid) to authenticated;

commit;
