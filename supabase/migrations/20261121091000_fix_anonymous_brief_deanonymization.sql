-- Fix a real privacy gap found in the same sweep as the member_directory fix: "Post
-- anonymously" on an Exchange brief only ever hid the author in the UI --
-- exchange_briefs_select_all (USING true) meant the real author_id was still readable by
-- any authenticated member via a direct REST call
-- (GET /rest/v1/exchange_briefs?select=author_id,anonymous), which combined with
-- member_directory completely de-anonymizes an "anonymous" brief. The client's own query
-- already fetched author_id regardless of the anonymous flag and only chose not to render
-- it -- the data was never actually hidden at the source.
--
-- Fix: a view that nulls out author_id for anonymous briefs unless the querying member is
-- the author themselves or an admin. auth.uid() reads the request-scoped JWT claim (set by
-- PostgREST per request), not the view owner's identity, so this correctly reflects the
-- real querying member even though the view itself runs as its owner (security_invoker =
-- false) to see past the base table's otherwise-unrestricted-by-column RLS.

create view public.exchange_briefs_public
with (security_invoker = false)
as
select
  id,
  brief_type,
  description,
  bucket_id,
  anonymous,
  case
    when anonymous
      and author_id not in (select id from public.users where auth_id = auth.uid())
      and not is_platform_admin()
    then null
    else author_id
  end as author_id,
  status,
  created_at
from public.exchange_briefs;

grant select on public.exchange_briefs_public to authenticated;
