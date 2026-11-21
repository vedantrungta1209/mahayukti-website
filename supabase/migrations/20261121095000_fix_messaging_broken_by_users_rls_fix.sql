-- CRITICAL REGRESSION, found and fixed same-session: earlier today's
-- 20261121090000_fix_member_email_phone_exposure.sql correctly closed the member
-- email/phone exposure by dropping users_select_active_members (the broad "any
-- authenticated member can read any other active member's full row" policy) and
-- replacing member-to-member lookups with the member_directory view. That migration's
-- own safety note said "every other table's RLS that references public.users does so
-- only via users.auth_id = auth.uid() (the querying member's own row)" -- true for
-- every policy EXCEPT this one, which was missed: messages_insert_own's WITH CHECK
-- reads the RECIPIENT's row directly from public.users (not member_directory) to check
-- their allow_messages_from setting:
--
--   (select users.allow_messages_from from users where users.id = messages.to_id) = 'everyone'
--
-- With users_select_active_members gone, a non-admin sender's session can no longer
-- see ANY other member's row in public.users at all (only users_select_own and the
-- admin-only users_select_admin_all remain) -- so that subquery now always returns
-- NULL for a recipient who isn't an admin, which is never equal to 'everyone'. Confirmed
-- live: simulating a real non-admin session's exact JWT claims, a direct SELECT of the
-- recipient's row from public.users returns zero rows.
--
-- Net effect, live in production since that earlier fix went out: NO non-admin member
-- can message any other non-admin member they don't already have an accepted
-- connection with, even when the recipient's setting is the default "everyone". The
-- "connections only" and "blocked" paths happened to keep working (they don't depend
-- on reading the recipient's own users row), which is exactly why this session's
-- earlier "verify live" tests of those two paths both correctly returned 403 --
-- for the right reason in the blocked/connections-required case, but the "everyone"
-- default case was silently broken the whole time and was never tested in isolation
-- until building the new notification triggers surfaced it.
--
-- Fix: a SECURITY DEFINER helper (same pattern as is_platform_admin()) that checks the
-- recipient's allow_messages_from and the block status with elevated privileges,
-- avoiding the need for the policy to read another member's row through the querying
-- user's own (correctly restricted) RLS view of public.users.

create or replace function public.can_message(p_from_id uuid, p_to_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select
    not exists (
      select 1 from public.blocked_users bu
      where (bu.blocker_id = p_to_id and bu.blocked_id = p_from_id)
         or (bu.blocker_id = p_from_id and bu.blocked_id = p_to_id)
    )
    and (
      (select allow_messages_from from public.users where id = p_to_id) = 'everyone'
      or exists (
        select 1 from public.member_connections mc
        where mc.status = 'accepted'
          and ((mc.requester_id = p_from_id and mc.addressee_id = p_to_id)
            or (mc.requester_id = p_to_id and mc.addressee_id = p_from_id))
      )
    );
$$;

drop policy if exists messages_insert_own on public.messages;

create policy messages_insert_own on public.messages
for insert
with check (
  from_id in (select users.id from public.users where users.auth_id = auth.uid())
  and public.can_message(from_id, to_id)
);
