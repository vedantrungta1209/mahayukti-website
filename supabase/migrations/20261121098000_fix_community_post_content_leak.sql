-- CRITICAL finding: posts_insert_own already correctly requires an active
-- community_members row to POST into a community (especially institution-verified
-- ones, which require admin approval to join) -- but posts_select_active_members never
-- checked community membership at all, only that the viewer is some active member of
-- the platform. Confirmed live: created a real verification-required institution
-- community, posted into it as admin, then simulated a real, completely uninvolved
-- active member's exact session (zero community_members rows for them) reading it
-- directly -- the post's full content came back. The entire point of
-- institution-verification gating (only approved members of that institution should
-- see its content) was illusory for reading, even though writing was correctly gated.
--
-- The same gap existed one level deeper: post_comments_select_all, post_likes_select_all
-- and post_hashtags_select_all were all `USING (true)` -- open to literally anyone
-- authenticated, not even requiring active status, let alone community membership. And
-- post_comments_insert_own never checked community membership either, so even writing
-- a comment into a private community's post was unrestricted.
--
-- Fixed with one reusable SECURITY DEFINER helper (can_access_post) mirroring the
-- membership check posts_insert_own already used, applied consistently to every table
-- that exposes a community-scoped post's content or activity.

create or replace function public.can_access_post(p_post_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select
    public.is_platform_admin()
    or exists (
      select 1
      from public.posts p
      join public.users u on u.auth_id = auth.uid() and u.status = 'active'
      where p.id = p_post_id
        and (
          p.community_id is null
          or exists (
            select 1 from public.community_members cm
            where cm.community_id = p.community_id
              and cm.user_id = u.id
              and cm.status = 'active'
          )
        )
    );
$$;

drop policy if exists posts_select_active_members on public.posts;
create policy posts_select_active_members on public.posts
for select
using (public.can_access_post(id));

drop policy if exists post_comments_select_all on public.post_comments;
create policy post_comments_select_all on public.post_comments
for select
using (public.can_access_post(post_id));

drop policy if exists post_comments_insert_own on public.post_comments;
create policy post_comments_insert_own on public.post_comments
for insert
with check (
  author_id in (select users.id from public.users where users.auth_id = auth.uid())
  and public.can_access_post(post_id)
);

drop policy if exists post_likes_select_all on public.post_likes;
create policy post_likes_select_all on public.post_likes
for select
using (public.can_access_post(post_id));

drop policy if exists post_likes_insert_own on public.post_likes;
create policy post_likes_insert_own on public.post_likes
for insert
with check (
  user_id in (select users.id from public.users where users.auth_id = auth.uid())
  and public.can_access_post(post_id)
);

drop policy if exists post_hashtags_select_all on public.post_hashtags;
create policy post_hashtags_select_all on public.post_hashtags
for select
using (public.can_access_post(post_id));
