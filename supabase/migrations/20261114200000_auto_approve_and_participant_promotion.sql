-- Three things, in order:
-- 1. Close a real privilege-escalation gap: users_insert_own only checked
--    auth_id = auth.uid(), so a signed-up member could POST role:'admin',
--    status:'active' on their own insert and it would have been accepted.
-- 2. Make "everyone applies as Member, auto-approved" a server-enforced fact,
--    not just a client-side UI choice -- the trigger overrides whatever the
--    client sends for role/status on a self-service insert, full stop.
-- 3. Add the Participant auto-promotion function: criteria-based, automatic,
--    no admin review (Participant is not a trust-critical tier -- only
--    Bucket Head/Council promotion needs a human, and that flow doesn't
--    exist yet -- this migration does not touch that).

create or replace function public.enforce_self_signup_defaults()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  -- Only clamp values for a normal end-user signup (authenticated role calling
  -- through PostgREST with their own JWT). A service_role insert (e.g. the
  -- admin account created directly via the Admin API) bypasses this entirely,
  -- since auth.role() is not 'authenticated' in that context.
  if auth.role() = 'authenticated' then
    new.role := 'member';
    new.status := 'active';          -- auto-approved: no pending gate for Member
    new.founding_member := coalesce(new.founding_member, false);
    new.founding_approved := false;
    new.approved_at := now();
    new.admin_notes := null;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_enforce_self_signup_defaults on public.users;
create trigger trg_enforce_self_signup_defaults
  before insert on public.users
  for each row
  execute function public.enforce_self_signup_defaults();

-- Participant auto-promotion: callable by the signed-in member themselves
-- (e.g. on login/profile load), evaluates ONLY their own row, promotes if
-- eligible. Criteria, first pass -- simple and honest about what's actually
-- checkable today, not a fake "activity score":
--   - still a Member (role = 'member'), status active
--   - account is at least 7 days old
--   - has filled in their "about" field (a real signal of a completed,
--     intentional profile -- not just a day-one accident)
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
     and rec.created_at <= now() - interval '7 days'
     and coalesce(trim(rec.about), '') <> '' then
    update public.users
      set role = 'participant'
      where id = rec.id
      returning * into rec;
  end if;
  return rec;
end;
$$;

grant execute on function public.maybe_promote_to_participant() to authenticated;
