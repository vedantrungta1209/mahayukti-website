-- RBAC for "sector hub" topic communities. The read/write gating mechanism
-- already exists and already works correctly -- posts_insert_own (social_core)
-- requires an active community_members row to post, and can_access_post()
-- (20261121098000) requires the same active row to even READ a
-- community-scoped post. What's missing is control over who is ALLOWED to
-- become a member in the first place: community_members_insert_own today lets
-- any active member self-join any non-institution topic community freely, so
-- nothing currently keeps a topic community "unpolluted by external
-- generalists" the way an institution community is kept to verified alumni.
--
-- This adds an optional sector_tag_id on communities (null = today's
-- unrestricted topic community, unchanged behaviour) and, when set, requires
-- the joining member's own primary sector to be compatible with it --
-- compatible meaning equal, an ancestor, or a descendant in the sector_tags
-- tree, so a community pinned at a broad L1 ("Legal") still welcomes a
-- member tagged at a specific L3 leaf under it, and vice versa.

alter table public.communities add column if not exists sector_tag_id uuid references public.sector_tags(id) on delete set null;

create or replace function public.sector_tag_compatible(p_community_sector uuid, p_member_sector uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select
    p_community_sector is null
    or (
      p_member_sector is not null
      and (
        p_community_sector = p_member_sector
        or exists (
          with recursive anc(id, parent_id) as (
            select id, parent_id from public.sector_tags where id = p_community_sector
            union all
            select st.id, st.parent_id from public.sector_tags st join anc on st.id = anc.parent_id
          )
          select 1 from anc where anc.id = p_member_sector
        )
        or exists (
          with recursive anc(id, parent_id) as (
            select id, parent_id from public.sector_tags where id = p_member_sector
            union all
            select st.id, st.parent_id from public.sector_tags st join anc on st.id = anc.parent_id
          )
          select 1 from anc where anc.id = p_community_sector
        )
      )
    );
$$;

drop policy if exists community_members_insert_own on public.community_members;
create policy community_members_insert_own on public.community_members
  for insert
  with check (
    user_id in (select id from public.users where auth_id = auth.uid())
    and (
      is_platform_admin()
      or (not exists (select 1 from communities c where c.id = community_members.community_id and c.requires_verification))
      or (status = 'pending'::text)
    )
    and (
      role = 'member'
      or is_platform_admin()
      or exists (select 1 from communities c where c.id = community_members.community_id and c.created_by = community_members.user_id)
    )
    and (
      is_platform_admin()
      or public.sector_tag_compatible(
        (select c.sector_tag_id from communities c where c.id = community_members.community_id),
        (select u.sector_tag_id from users u where u.id = community_members.user_id)
      )
    )
  );
