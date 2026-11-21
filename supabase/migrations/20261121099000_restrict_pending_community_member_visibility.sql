-- Related, moderate-severity gap found in the same sweep as the post-content leak fix:
-- community_members_select_all was `USING (true)` -- open to anyone authenticated,
-- including 'pending' rows. loadPendingCommunityMembers() treats the list of who has
-- requested to join a verification-required community as admin-only in the UI (it's
-- only ever called when ST.profile.role==='admin'), but nothing at the database level
-- enforced that -- a direct API call (GET /rest/v1/community_members?status=eq.pending)
-- would reveal every pending join request across every institution community platform-
-- wide to any authenticated member, regardless of whether they belong to that
-- institution or even that community at all.
--
-- Active-membership rows are intentionally left broadly readable: loadForums()'s member
-- counts are read across every community, including ones the viewer hasn't joined, to
-- show "X members" before someone decides to join -- that's existing, legitimate
-- discoverability behaviour, not a bug. Only 'pending' rows (the sensitive "who is
-- applying" information) are newly restricted to the applicant themselves or an admin.

drop policy if exists community_members_select_all on public.community_members;

create policy community_members_select_all on public.community_members
for select
using (
  status <> 'pending'
  or user_id in (select users.id from public.users where users.auth_id = auth.uid())
  or is_platform_admin()
);
