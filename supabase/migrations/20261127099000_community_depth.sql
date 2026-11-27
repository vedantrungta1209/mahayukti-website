-- Per-community moderators. Today the only gate on approving/denying
-- pending members is the single global role==='admin' check -- this adds a
-- per-community role so a community's own creator/moderators can manage it
-- without needing platform-admin rights.
alter table public.community_members add column if not exists role text not null default 'member' check (role in ('member','moderator'));

-- The community's creator starts as its first moderator.
update public.community_members cm
set role = 'moderator'
from public.communities c
where cm.community_id = c.id and cm.user_id = c.created_by;

-- Replace the admin-only update policy with one that also lets a
-- community's own moderator update other members' status (approve/deny
-- pending, e.g.) -- but role itself (granting/revoking moderator) stays
-- platform-admin-only via the with_check, so a moderator can't self-escalate
-- or hand moderator to someone else.
drop policy if exists community_members_update_admin on public.community_members;
create policy community_members_update_admin_or_moderator on public.community_members
  for update
  using (
    is_platform_admin()
    or exists (
      select 1 from public.community_members mod
      where mod.community_id = community_members.community_id
        and mod.user_id in (select id from public.users where auth_id = auth.uid())
        and mod.role = 'moderator'
    )
  )
  with check (
    is_platform_admin()
    or (
      role = 'member'
      and exists (
        select 1 from public.community_members mod
        where mod.community_id = community_members.community_id
          and mod.user_id in (select id from public.users where auth_id = auth.uid())
          and mod.role = 'moderator'
      )
    )
  );

-- Deny-a-pending-member and remove-a-member both go through DELETE, which
-- was previously own-or-admin only -- a moderator couldn't deny/remove
-- anyone despite being able to approve them via the update policy above.
drop policy if exists community_members_delete_own on public.community_members;
create policy community_members_delete_own_or_moderator on public.community_members
  for delete
  using (
    user_id in (select id from public.users where auth_id = auth.uid())
    or is_platform_admin()
    or exists (
      select 1 from public.community_members mod
      where mod.community_id = community_members.community_id
        and mod.user_id in (select id from public.users where auth_id = auth.uid())
        and mod.role = 'moderator'
    )
  );
