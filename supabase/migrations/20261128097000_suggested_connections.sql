-- "People you may know" -- Directory/Home had no discovery mechanism at
-- all beyond manually browsing or searching. Ranks other active members by
-- how many connections they share with the caller (the standard,
-- unsurprising signal every comparable platform uses for this), excluding
-- the caller themselves and anyone already connected or already
-- pending/requested either direction.
create or replace function public.get_suggested_connections(p_limit int default 10)
returns table(id uuid, username text, real_name text, show_real_name boolean, real_name_approved boolean, avatar_url text, domain text, mutual_count int)
language sql
stable security definer
set search_path to 'public'
as $function$
  with caller_id as (
    select id from public.users where auth_id = auth.uid()
  ),
  caller_conns as (
    select case when requester_id = (select id from caller_id) then addressee_id else requester_id end as other_id
    from public.member_connections
    where status = 'accepted'
      and (select id from caller_id) is not null
      and (requester_id = (select id from caller_id) or addressee_id = (select id from caller_id))
  ),
  excluded as (
    -- anyone already connected OR with any pending request either direction --
    -- a suggestion that's already mid-flow with the caller isn't useful.
    select case when requester_id = (select id from caller_id) then addressee_id else requester_id end as other_id
    from public.member_connections
    where (select id from caller_id) is not null
      and (requester_id = (select id from caller_id) or addressee_id = (select id from caller_id))
  ),
  candidate_mutuals as (
    select
      case when cc2.requester_id = other_id then cc2.addressee_id else cc2.requester_id end as candidate_id,
      count(*) as mutual_count
    from caller_conns cc
    join public.member_connections cc2
      on cc2.status = 'accepted'
      and (cc2.requester_id = cc.other_id or cc2.addressee_id = cc.other_id)
    group by 1
  )
  select u.id, u.username, u.real_name, u.show_real_name, u.real_name_approved, u.avatar_url, u.domain,
    coalesce(cm.mutual_count, 0)::int as mutual_count
  from public.users u
  left join candidate_mutuals cm on cm.candidate_id = u.id
  where u.status = 'active'
    and u.role <> 'admin'
    and u.id <> (select id from caller_id)
    and u.id not in (select other_id from excluded)
    and (select id from caller_id) is not null
  order by mutual_count desc, u.created_at desc
  limit p_limit;
$function$;
