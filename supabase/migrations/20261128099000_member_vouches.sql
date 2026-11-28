-- "Verified referral" tier criterion has been shown in the UI since Phase 1
-- (renderUpgradeCard/renderHomeTierNudge in app.html) as "not yet built." This
-- builds it: a real peer-vouching system, modeled on the external strategic
-- review's "Vouched-By" proposal (give verified members a limited number of
-- vouches; a bad vouch costs the voucher something) but sized to this
-- platform's real current mechanics -- there is no ban/suspend action on an
-- active member yet (checked: only pending->active/rejected exists), so the
-- "vouch strikes" enforcement loop that proposal wants is deliberately NOT
-- built here. What's built: the vouch itself, a hard per-member cap so it
-- can't be spammed, and wiring it into the real promotion criteria so the
-- UI's long-promised third checklist item is no longer a lie.
create table public.member_vouches (
  id uuid primary key default gen_random_uuid(),
  voucher_id uuid not null references public.users(id) on delete cascade,
  vouchee_id uuid not null references public.users(id) on delete cascade,
  note text,
  created_at timestamptz not null default now(),
  unique (voucher_id, vouchee_id),
  constraint member_vouches_no_self_vouch check (voucher_id <> vouchee_id)
);

create index member_vouches_vouchee_idx on public.member_vouches(vouchee_id);
create index member_vouches_voucher_idx on public.member_vouches(voucher_id);

alter table public.member_vouches enable row level security;

-- Visible to any signed-in member -- "endorsed by" is a public trust signal
-- on a profile, same as LinkedIn endorsements, not a private admin record.
create policy member_vouches_select_all on public.member_vouches
  for select to authenticated using (true);

-- A member can only vouch as themselves, for someone else who is an active
-- member -- vouching for a not-yet-active or rejected row makes no sense
-- (there is no approval gate left to bypass; that bottleneck was already
-- removed by enforce_self_signup_defaults in 20261114200000).
create policy member_vouches_insert_own on public.member_vouches
  for insert to authenticated
  with check (
    voucher_id = (select id from public.users where auth_id = auth.uid())
    and exists (select 1 from public.users v where v.id = voucher_id and v.status = 'active')
    and exists (select 1 from public.users w where w.id = vouchee_id and w.status = 'active')
  );

-- Letting someone retract their own vouch is reasonable (e.g. they vouched
-- too hastily) -- not letting the vouchee delete it, obviously.
create policy member_vouches_delete_own on public.member_vouches
  for delete to authenticated
  using (voucher_id = (select id from public.users where auth_id = auth.uid()));

-- Hard cap so vouching can't be used as a spam/growth-hack lever -- 5 per
-- member, same order of magnitude as the external proposal's "3 keys" idea,
-- sized up slightly since this is an unlimited resource (not single-use
-- invite codes) and 3 felt too tight for a real professional network.
create or replace function public.enforce_vouch_limit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  existing_count int;
begin
  select count(*) into existing_count from public.member_vouches where voucher_id = new.voucher_id;
  if existing_count >= 5 then
    raise exception 'You have already given all 5 of your vouches.';
  end if;
  return new;
end;
$$;

create trigger trg_enforce_vouch_limit
  before insert on public.member_vouches
  for each row
  execute function public.enforce_vouch_limit();

-- Wire the real criterion into promotion -- same shape as the 90-day /
-- profile-complete criteria from 20261123100000, now a real fourth check
-- instead of permanently "not yet built."
create or replace function public.maybe_promote_to_participant()
returns public.users
language plpgsql
security definer
set search_path = public
as $$
declare
  rec public.users;
  has_vouch boolean;
begin
  select * into rec from public.users where auth_id = auth.uid();
  if rec.id is null then
    return rec;
  end if;
  select exists(select 1 from public.member_vouches where vouchee_id = rec.id) into has_vouch;
  if rec.role = 'member'
     and rec.status = 'active'
     and rec.created_at <= now() - interval '90 days'
     and coalesce(trim(rec.about), '') <> ''
     and coalesce(trim(rec.domain), '') <> ''
     and coalesce(trim(rec.domain_group), '') <> ''
     and coalesce(trim(rec.city), '') <> ''
     and coalesce(trim(rec.experience), '') <> ''
     and has_vouch then
    update public.users
      set role = 'participant'
      where id = rec.id
      returning * into rec;
  end if;
  return rec;
end;
$$;

-- enforce_self_update_restrictions (20261123100000) re-verifies the same
-- promotion criteria on any direct PATCH that flips role member->participant,
-- to stop a client bypassing the RPC. It must now also require a vouch, or a
-- member with 90 days + a complete profile but no vouch could self-grant the
-- promotion via a raw PATCH the same way the earlier bug let them skip the
-- 90-day/profile checks before 20261122100000 fixed it.
create or replace function public.enforce_self_update_restrictions()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.role() = 'authenticated' and old.auth_id = auth.uid() and not public.is_platform_admin() then
    if not (
      old.role = 'member' and new.role = 'participant'
      and old.created_at <= now() - interval '90 days'
      and coalesce(trim(old.about), '') <> ''
      and coalesce(trim(old.domain), '') <> ''
      and coalesce(trim(old.domain_group), '') <> ''
      and coalesce(trim(old.city), '') <> ''
      and coalesce(trim(old.experience), '') <> ''
      and exists(select 1 from public.member_vouches where vouchee_id = old.id)
    ) then
      new.role := old.role;
    end if;
    if not (old.status = 'active' and new.status = 'deactivated') then
      new.status := old.status;
    end if;
    new.founding_member := old.founding_member;
    new.founding_approved := old.founding_approved;
    new.real_name_approved := old.real_name_approved;
    new.admin_notes := old.admin_notes;
    new.approved_at := old.approved_at;
    new.auth_id := old.auth_id;
  end if;
  return new;
end;
$$;
