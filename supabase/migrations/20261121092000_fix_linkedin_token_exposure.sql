-- Fix the most severe finding of this audit pass: public.linkedin_connections.access_token
-- (a real, live LinkedIn OAuth access token used to post on a member's behalf) was fully
-- readable by the row owner AND by any platform admin via the ordinary REST API
-- (linkedin_connections_select_own: auth_user_id = auth.uid() OR is_platform_admin()) --
-- RLS is row-level only, it does not restrict which columns a permitted row exposes.
-- Confirmed the app's own client code never requests access_token (it only ever selects
-- connected_at/token_expires_at, see app.html's loadLiStatus()) -- all real LinkedIn API
-- calls happen server-side in supabase/functions/linkedin-oauth, via its own service-role
-- connection, which is unaffected by grants to the `authenticated` role. There is no
-- legitimate reason for ANY client-facing session (self or admin) to ever read this column
-- directly: a compromised member session could replay the token straight against LinkedIn's
-- API outside the app's own controls, and a compromised/rogue admin session could bulk-
-- harvest every connected member's LinkedIn access token.
--
-- Column-level privileges (not RLS) are the correct tool here, since RLS can't restrict
-- columns and there's no "let the owner see their own token" requirement to preserve.

revoke select on public.linkedin_connections from authenticated;
grant select (auth_user_id, connected_at, token_expires_at, scope) on public.linkedin_connections to authenticated;
