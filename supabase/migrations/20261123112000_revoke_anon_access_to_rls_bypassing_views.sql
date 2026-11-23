-- member_directory, exchange_briefs_public, and event_rsvp_counts are all
-- owned by `postgres` (BYPASSRLS) with the default security_invoker=false,
-- so querying them runs with the owner's privileges, not the caller's --
-- RLS on the underlying users/exchange_briefs/event_rsvps tables never
-- applies to them at all. That's fine for a logged-in member (the views'
-- own WHERE/CASE logic is the real access control, same as every other
-- view in this schema), but Supabase's default schema grants give `anon`
-- SELECT on every public table and view the same as `authenticated` --
-- nobody had explicitly narrowed it for these three. The result: anyone on
-- the internet, with nothing but the public anon key already sitting in
-- app.html's source, could pull the full active member list (real names,
-- cities, domains, bios) straight off GET /rest/v1/member_directory with
-- zero login -- confirmed live before this fix. Every base table avoids
-- this because their RLS policies all key off auth.uid(), which is null
-- for anon and so returns nothing; these three views are the only places
-- that check was never reached at all.
revoke select on public.member_directory from anon;
revoke select on public.exchange_briefs_public from anon;
revoke select on public.event_rsvp_counts from anon;
