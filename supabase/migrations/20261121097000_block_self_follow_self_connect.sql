-- Defense-in-depth only, not a live UI gap: unlike the marketplace/exchange
-- self-interaction bugs, the "Connect"/"Follow" buttons were already correctly hidden on
-- your own profile (loadMemberProfile()'s isSelf check, line ~2114-2115 of app.html) --
-- nobody can reach this through the app's own UI. Found while sweeping for the same
-- missing-self-check pattern after finding it twice elsewhere this session: neither
-- follows_insert_own nor member_connections_insert_own's RLS actually blocked
-- follower_id = followee_id or requester_id = addressee_id at the database level, so a
-- deliberate direct API call could still create a self-follow/self-connection row.
-- Closing it anyway for consistency with the rest of this session's "don't rely on the
-- client alone" approach.

drop policy if exists follows_insert_own on public.follows;

create policy follows_insert_own on public.follows
for insert
with check (
  follower_id in (select users.id from public.users where users.auth_id = auth.uid())
  and follower_id <> followee_id
  and not exists (
    select 1 from public.blocked_users bu
    where (bu.blocker_id = follows.followee_id and bu.blocked_id = follows.follower_id)
       or (bu.blocker_id = follows.follower_id and bu.blocked_id = follows.followee_id)
  )
);

drop policy if exists member_connections_insert_own on public.member_connections;

create policy member_connections_insert_own on public.member_connections
for insert
with check (
  requester_id in (select users.id from public.users where users.auth_id = auth.uid())
  and requester_id <> addressee_id
  and not exists (
    select 1 from public.blocked_users bu
    where (bu.blocker_id = member_connections.addressee_id and bu.blocked_id = member_connections.requester_id)
       or (bu.blocker_id = member_connections.requester_id and bu.blocked_id = member_connections.addressee_id)
  )
);
