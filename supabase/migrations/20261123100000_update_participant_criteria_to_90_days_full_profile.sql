-- Per the MahaYukti build spec (Phase 1, Account merge) and its canvas wireframe: the
-- Account screen's Membership tier checklist shows "Account age 90+ days" and "Profile
-- 100% complete" as the two live criteria (plus a third, "1 verified referral from another
-- member", explicitly shown as not yet built). Production had shipped a simpler first pass
-- (7+ days, non-empty "about") on 20261114200000. The founder confirmed, when asked rather
-- than guessed: redo the real criteria to match the wireframe, not just its copy.
--
-- "Profile 100% complete" is defined here as domain, domain_group, city, experience and
-- about all non-empty -- the same five fields the Account screen's own "Professional Info"
-- edit form lets a member fill in, so the checklist and the edit form agree on what
-- "complete" means.
--
-- Both maybe_promote_to_participant() (the RPC a member calls themselves) and
-- enforce_self_update_restrictions()'s re-verification clause (which stops a direct PATCH
-- from granting the same promotion without genuinely meeting it -- see
-- 20261122100000) must change together, or the trigger silently re-clamps a promotion the
-- RPC just granted, exactly the bug 20261122100000 fixed for the old criteria.

create or replace function public.maybe_promote_to_participant()
returns public.users
language plpgsql
security definer
set search_path = public
as $$
declare
  rec public.users;
begin
  select * into rec from public.users where auth_id = auth.uid();
  if rec.id is null then
    return rec;
  end if;
  if rec.role = 'member'
     and rec.status = 'active'
     and rec.created_at <= now() - interval '90 days'
     and coalesce(trim(rec.about), '') <> ''
     and coalesce(trim(rec.domain), '') <> ''
     and coalesce(trim(rec.domain_group), '') <> ''
     and coalesce(trim(rec.city), '') <> ''
     and coalesce(trim(rec.experience), '') <> '' then
    update public.users
      set role = 'participant'
      where id = rec.id
      returning * into rec;
  end if;
  return rec;
end;
$$;

create or replace function public.enforce_self_update_restrictions()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.role() = 'authenticated' and old.auth_id = auth.uid() and not public.is_platform_admin() then
    -- Re-verified here against the same five-field "100% complete" + 90-day criteria
    -- maybe_promote_to_participant() itself now checks (see migration header), not just
    -- trusted by transition shape.
    if not (
      old.role = 'member' and new.role = 'participant'
      and old.created_at <= now() - interval '90 days'
      and coalesce(trim(old.about), '') <> ''
      and coalesce(trim(old.domain), '') <> ''
      and coalesce(trim(old.domain_group), '') <> ''
      and coalesce(trim(old.city), '') <> ''
      and coalesce(trim(old.experience), '') <> ''
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
