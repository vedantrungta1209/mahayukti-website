-- Same class of gap as community_members' pending-request leak, found in the final
-- sweep of every remaining SELECT policy: event_rsvps_select_all was `USING (true)`,
-- open to literally any authenticated session -- not even requiring active status.
-- The client never requests another member's RSVP identity anywhere (loadEventsList()
-- only ever reads its own user_id-filtered rows, or aggregate per-event_id counts with
-- no user_id in the select at all) -- there is no "see who's going" feature in this
-- app. But the raw table allowed a direct query to list exactly who RSVP'd to which
-- event, which the UI's own design never intended to expose.
--
-- Restricted to the same "own row or admin" pattern already used by messages,
-- blocked_users, muted_users, saved_posts, api_keys, etc. This means the existing
-- aggregate "X going" count query (which reads other people's rows by event_id, not
-- just the viewer's own) would otherwise undercount to zero for non-admins, so it's
-- repointed at a new view instead: anyone can see THAT N people RSVP'd to an event
-- (needed for the existing counts, same as community member counts), but not WHO,
-- which this app's own UI never shows anywhere.

create view public.event_rsvp_counts
with (security_invoker = false)
as
select event_id, count(*) as rsvp_count
from public.event_rsvps
group by event_id;

grant select on public.event_rsvp_counts to authenticated;

drop policy if exists event_rsvps_select_all on public.event_rsvps;

create policy event_rsvps_select_all on public.event_rsvps
for select
using (
  user_id in (select users.id from public.users where users.auth_id = auth.uid())
  or is_platform_admin()
);
