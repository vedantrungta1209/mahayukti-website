-- Removes the schema behind network.html, a completely separate legacy registration
-- app (different login/account model: accounts -> account_members -> {individual,
-- corporate, institution, government, ngo}_profiles, plus a briefs/brief_buckets/
-- brief_candidates matching flow) found still live and publicly reachable at
-- mahayukti.com/network.html during this session's audit, despite being linked from
-- nowhere in the real site (app.html, index.html) and absent from sitemap.xml.
--
-- It was never dead in the sense of being unreachable -- it was a fully functional,
-- independently deployed app writing to its own Supabase tables, completely
-- disconnected from the real member registry's admin review queue. Its own Admin tab
-- was already broken ("infinite recursion detected in policy for relation \"accounts\"")
-- before this cleanup. Confirmed before dropping: every one of these tables is empty
-- except verification_rules (5 seed rows, not real user data), and no live table (users,
-- posts, messages, etc.) has any foreign key into this schema.
--
-- User's explicit instruction: take it down.

drop table if exists public.account_members cascade;
drop table if exists public.individual_profiles cascade;
drop table if exists public.corporate_profiles cascade;
drop table if exists public.institution_profiles cascade;
drop table if exists public.government_profiles cascade;
drop table if exists public.ngo_profiles cascade;
drop table if exists public.introductions cascade;
drop table if exists public.brief_candidates cascade;
drop table if exists public.brief_buckets cascade;
drop table if exists public.briefs cascade;
drop table if exists public.accounts cascade;
drop table if exists public.verification_rules cascade;
