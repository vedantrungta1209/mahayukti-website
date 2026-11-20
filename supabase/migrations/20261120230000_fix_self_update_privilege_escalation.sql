-- Real, serious, PRE-EXISTING privilege-escalation gap (predates this
-- session's own work): users_update_own (20261113235900) only checks
-- auth_id = auth.uid() -- a row-level check, not a column-level one. RLS in
-- Postgres has no concept of "you can update this row but only these
-- columns" on its own, so nothing has ever stopped an ordinary member from
-- PATCHing their OWN row's role to 'admin', status to whatever they like,
-- founding_member/founding_approved to true, or admin_notes/approved_at to
-- anything -- a full self-service admin-takeover via one API call.
--
-- 20261114200000 already solved this exact class of problem for INSERT
-- (enforce_self_signup_defaults, a BEFORE INSERT trigger) but never
-- extended the same protection to UPDATE. This is that trigger's sibling.

begin;

-- deactivateAccount() (built earlier this session) self-PATCHes status to
-- 'deactivated', and requestAccountDeletion() self-PATCHes admin_notes with
-- a deletion request string -- both would be silently clamped back to their
-- old value by the trigger below, breaking two features this session
-- already shipped. admin_notes is also the wrong place for that regardless:
-- it's meant to hold an ADMIN's notes about a member, and letting a member
-- write to it at all means they could overwrite or erase a legitimate
-- existing note about themselves (e.g. one flagging suspicious activity).
-- Giving deletion requests their own column fixes both problems at once.
alter table public.users add column if not exists deletion_requested_at timestamptz;

create or replace function public.enforce_self_update_restrictions()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  -- Only clamp when a normal authenticated member is updating THEIR OWN row
  -- (old.auth_id = auth.uid()) and isn't themselves an admin. An admin
  -- updating someone else's row never has old.auth_id = auth.uid(), so this
  -- never interferes with the real approve/reject flow in
  -- users_update_admin_all; an admin editing their own row keeps full
  -- access too, consistent with the blanket rights that policy already
  -- gives them.
  if auth.role() = 'authenticated' and old.auth_id = auth.uid() and not public.is_platform_admin() then
    new.role := old.role;
    -- The one self-service status change allowed is active -> deactivated
    -- (Settings -> Deactivate account). Anything else -- reactivating
    -- yourself, self-approving out of 'pending', or setting any other
    -- value -- is clamped back.
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

drop trigger if exists trg_enforce_self_update_restrictions on public.users;
create trigger trg_enforce_self_update_restrictions
  before update on public.users
  for each row
  execute function public.enforce_self_update_restrictions();

commit;
