-- Profile picture support. Column is nullable -- the client falls back to an
-- initials circle (already the existing design) whenever it's not set, so
-- this is purely additive and doesn't change behaviour for anyone who never
-- uploads a photo.
alter table public.users add column if not exists avatar_url text;

-- Self-update already goes through enforce_self_update_restrictions, which
-- clamps a fixed list of sensitive columns and otherwise allows anything --
-- avatar_url needs no special-casing there, it's an ordinary profile field
-- like city/about.

-- member_directory needs the column republished too, since it's the only
-- thing non-admin client code is allowed to read other members' rows
-- through (see the 2026-11-21 PII-leak fix this view was created for).
drop view if exists public.member_directory;
create view public.member_directory as
select
  id, username, real_name, show_real_name, real_name_approved,
  city, state, domain, domain_group, role, founding_member, founding_approved,
  experience, organisation, show_organisation, about, qualification, linkedin,
  status, approved_at, created_at, bucket_id, avatar_url
from public.users
where status = 'active';

-- Recreating the view resets its grants to Postgres defaults, which would
-- silently re-open the anon PII leak the 20261123112000 migration closed
-- (anon gets SELECT on every new view by default). Must always be repeated
-- whenever this view is dropped and recreated.
revoke select on public.member_directory from anon;
