-- Fix a real, live privacy violation found by actually testing as a non-admin member:
-- users_select_active_members granted every authenticated member full-row SELECT access
-- (via RLS, which is row-level only, never column-level) to every other active member's
-- row in public.users -- including email and phone. Confirmed exploitable directly via
-- the REST API (GET /rest/v1/users?select=email,phone), regardless of what the app's own
-- UI/queries ever asked for. This directly contradicts the Privacy Policy's explicit
-- promise: "We do not display your phone number or email to any other member, ever --
-- this is a platform-level rule, not a setting."
--
-- Fix: member-to-member visibility now goes through a column-restricted view instead of
-- the base table. Confirmed safe to drop the broad base-table policy: every other table's
-- RLS that references public.users does so only via `users.auth_id = auth.uid()` (the
-- querying member's own row, already covered by the untouched users_select_own policy) --
-- none of them depend on reading OTHER members' rows through users_select_active_members.

create view public.member_directory
with (security_invoker = false)
as
select
  id, username, real_name, show_real_name, real_name_approved,
  city, state, domain, domain_group, role,
  founding_member, founding_approved, experience,
  organisation, show_organisation, about, qualification,
  linkedin, status, approved_at, created_at, bucket_id
from public.users
where status = 'active';

grant select on public.member_directory to authenticated;

drop policy if exists users_select_active_members on public.users;
