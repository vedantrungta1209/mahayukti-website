-- can_access_post() only ever checked community membership. The audience
-- column (everyone / sector / connections) and audience_bucket_ids array
-- exist on posts and app.html's loadSocialFeed() already builds a query
-- filter around them -- but that filter is just a convenience the client
-- sends; nothing stopped a direct PostgREST call (GET /posts?select=* with
-- no audience clause, trivial from devtools) from reading every "Sector
-- only" or "Connections only" post from members you have no relationship
-- with, since RLS itself never looked at audience at all. This closes that
-- gap by mirroring the exact same rule set loadSocialFeed() already relies
-- on, so there's no longer a gap between what the UI shows and what the
-- database actually allows.
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
        and (
          p.author_id = u.id
          or p.audience = 'everyone'
          or p.audience is null
          or (p.audience = 'sector' and p.bucket_id is not null and p.bucket_id = u.bucket_id)
          or (p.audience_bucket_ids is not null and u.bucket_id = any(p.audience_bucket_ids))
          or (
            p.audience = 'connections'
            and exists (
              select 1 from public.member_connections mc
              where mc.status = 'accepted'
                and (
                  (mc.requester_id = p.author_id and mc.addressee_id = u.id)
                  or (mc.requester_id = u.id and mc.addressee_id = p.author_id)
                )
            )
          )
        )
    );
$$;
