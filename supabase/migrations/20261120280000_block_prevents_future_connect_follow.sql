-- The Block confirmation dialog in app.html says "They won't be able to
-- message or connect with you, and any existing connection or follow
-- between you is removed" -- blockCurrentMember() does clean up any
-- EXISTING relationship, and messages_insert_own (20261120190000) does
-- check blocked_users. But member_connections_insert_own and
-- follows_insert_own (both 20261120150000, before blocked_users existed as
-- a table) never checked it at all -- a blocked member could send a brand
-- new connection request or re-follow the very next moment, which is
-- exactly what the dialog promises can't happen.

begin;

drop policy if exists member_connections_insert_own on public.member_connections;
create policy member_connections_insert_own on public.member_connections for insert with check (
  requester_id in (select id from public.users where auth_id = auth.uid())
  and not exists (
    select 1 from public.blocked_users bu
    where (bu.blocker_id = member_connections.addressee_id and bu.blocked_id = member_connections.requester_id)
       or (bu.blocker_id = member_connections.requester_id and bu.blocked_id = member_connections.addressee_id)
  )
);

drop policy if exists follows_insert_own on public.follows;
create policy follows_insert_own on public.follows for insert with check (
  follower_id in (select id from public.users where auth_id = auth.uid())
  and not exists (
    select 1 from public.blocked_users bu
    where (bu.blocker_id = follows.followee_id and bu.blocked_id = follows.follower_id)
       or (bu.blocker_id = follows.follower_id and bu.blocked_id = follows.followee_id)
  )
);

commit;
