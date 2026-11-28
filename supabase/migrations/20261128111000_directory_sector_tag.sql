-- Expose sector_tag_id on member_directory so the Directory UI can filter by
-- the new cascading taxonomy (down to a Level 3 micro-domain), the same way
-- it already filters by the old flat domain_group. Appended at the end of
-- the select list, same constraint as every other view-column addition in
-- this app (a view column can only be appended, not inserted mid-list,
-- without a true drop/recreate).
drop view if exists public.member_directory;
create view public.member_directory as
select
  id, username, real_name, show_real_name, real_name_approved,
  city, state, domain, domain_group, role, founding_member, founding_approved,
  experience, organisation, show_organisation, about, qualification, linkedin,
  status, approved_at, created_at, bucket_id, avatar_url, skills, open_to,
  sector_tag_id
from public.users
where status = 'active';

-- Load-bearing, not decorative -- recreating this view resets its grants to
-- Postgres defaults (anon gets SELECT on every new view by default in this
-- project), and this exact view has held a real PII exposure bug before when
-- this re-apply was missed (20261121090000's whole point).
revoke select on public.member_directory from anon;
