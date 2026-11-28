-- "My Sector Verticals" filtering on the new Flash Intelligence feed needs to know
-- each member's own primary sector in the new cascading sector_tags taxonomy --
-- the existing `users.bucket_id` only points at the old flat 12-bucket system.
-- Add a nullable FK mirroring it, backfilled from the matching sector_tags Level-1
-- row by name. 11 of the 12 original buckets have an exact-name match; the one
-- that was split (`Technology & Cybersecurity`) backfills to the broader
-- `Technology & AI` branch as the closer default -- the member can refine this to
-- `Cybersecurity & Infosec`, or any deeper L2/L3 leaf, from Profile settings.
alter table public.users add column if not exists sector_tag_id uuid references public.sector_tags(id) on delete set null;

update public.users u
set sector_tag_id = st.id
from public.buckets b
join public.sector_tags st on st.level = 1 and st.name = b.name
where u.bucket_id = b.id
  and u.sector_tag_id is null;

update public.users u
set sector_tag_id = st.id
from public.buckets b
join public.sector_tags st on st.level = 1 and st.name = 'Technology & AI'
where u.bucket_id = b.id
  and b.name = 'Technology & Cybersecurity'
  and u.sector_tag_id is null;
