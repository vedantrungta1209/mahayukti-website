-- CONFIRMED, SEVERE BUG: the entire self-service Participant auto-promotion feature
-- (maybe_promote_to_participant(), from 20261114200000) has been silently broken since
-- 20261120230000_fix_self_update_privilege_escalation.sql shipped. That migration
-- correctly closed a real self-role-escalation gap by having
-- enforce_self_update_restrictions unconditionally clamp `new.role := old.role` on any
-- update where the authenticated caller is updating their own row -- but it clamps
-- unconditionally, with no exception, even though maybe_promote_to_participant() is
-- itself a SECURITY DEFINER function performing a legitimate, criteria-checked
-- member -> participant promotion from inside that exact same "authenticated user
-- updating their own row" context. auth.role()/auth.uid() are request-level GUCs that
-- persist regardless of which function performs the UPDATE, so the trigger can't tell
-- the two cases apart as written, and silently undoes the promotion every time.
--
-- Confirmed live: created a real test member, backdated created_at by 8 days, gave it a
-- non-empty About, verified by hand that every single criterion the RPC checks
-- evaluates true -- then called the real RPC (both via the live REST endpoint and via a
-- simulated SQL session) and got back role:'member' unchanged both times, with no error
-- raised at all. A real member who genuinely qualifies would click "Apply to become a
-- Participant", see "Not eligible yet -- check the criteria above", and have no way to
-- know the real cause is a trigger bug, not their own eligibility.
--
-- Fixed with the same pattern status already uses for its one allowed self-service
-- transition (active -> deactivated) -- but naively exempting "member -> participant"
-- outright would reopen the exact self-escalation hole 20261120230000 closed: anyone
-- could then PATCH their own role straight to 'participant' the moment they sign up,
-- skipping the real criteria entirely. So the trigger re-checks the same two criteria
-- maybe_promote_to_participant() itself already checks (7+ days old, About filled in)
-- before allowing the transition through -- a direct PATCH attempt only succeeds if the
-- criteria are genuinely met, in which case it was never actually an escalation.

create or replace function public.enforce_self_update_restrictions()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.role() = 'authenticated' and old.auth_id = auth.uid() and not public.is_platform_admin() then
    -- The one self-service role change allowed is a genuinely-earned member ->
    -- participant promotion -- re-verified here, not just trusted by transition shape,
    -- so a direct PATCH attempt gets exactly the same scrutiny the real RPC applies.
    if not (
      old.role = 'member' and new.role = 'participant'
      and old.created_at <= now() - interval '7 days'
      and coalesce(trim(old.about), '') <> ''
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
