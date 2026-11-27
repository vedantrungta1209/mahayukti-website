-- Member card depth: skills/open-to tags, and real mutual-connection names
-- (not just the count get_connection_stats already returns).

alter table public.users add column if not exists skills text[];
alter table public.users add column if not exists open_to text[];

-- member_directory needs both republished, same as every other profile
-- field added to it this session.
drop view if exists public.member_directory;
create view public.member_directory as
select
  id, username, real_name, show_real_name, real_name_approved,
  city, state, domain, domain_group, role, founding_member, founding_approved,
  experience, organisation, show_organisation, about, qualification, linkedin,
  status, approved_at, created_at, bucket_id, avatar_url, skills, open_to
from public.users
where status = 'active';

revoke select on public.member_directory from anon;

-- Mirrors get_connection_stats' own caller/target CTE shape exactly, but
-- returns the actual mutual members (capped at 12) instead of just a count.
-- Security definer for the same reason get_connection_stats already is:
-- member_connections' RLS deliberately keeps a member from reading anyone
-- else's connection list directly, so this has to look it up on their
-- behalf rather than ask the client to.
create or replace function public.get_mutual_connections(p_target_id uuid)
returns table(id uuid, username text, real_name text, show_real_name boolean, real_name_approved boolean, avatar_url text)
language sql
stable security definer
set search_path to 'public'
as $function$
  with target_conns as (
    select case when requester_id = p_target_id then addressee_id else requester_id end as other_id
    from public.member_connections
    where status = 'accepted' and (requester_id = p_target_id or addressee_id = p_target_id)
  ),
  caller_id as (
    select id from public.users where auth_id = auth.uid()
  ),
  caller_conns as (
    select case when requester_id = (select id from caller_id) then addressee_id else requester_id end as other_id
    from public.member_connections
    where status = 'accepted'
      and (select id from caller_id) is not null
      and (requester_id = (select id from caller_id) or addressee_id = (select id from caller_id))
  )
  select u.id, u.username, u.real_name, u.show_real_name, u.real_name_approved, u.avatar_url
  from public.users u
  where u.id in (select other_id from target_conns where other_id in (select other_id from caller_conns))
  limit 12;
$function$;
