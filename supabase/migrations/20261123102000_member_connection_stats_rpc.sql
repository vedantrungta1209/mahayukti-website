-- Per the build spec's PublicProfile.dc.html: "184 connections · 6 mutual" on the member
-- profile screen. member_connections' own RLS (member_connections_select_participant,
-- 20261120150000) deliberately only lets a caller see rows where they themselves are a
-- party -- a regular member genuinely cannot read someone else's connection list raw, and
-- that restriction stays correct. A security definer function that returns only the two
-- COUNTS (never the raw rows) gives the profile screen real numbers without weakening that
-- privacy boundary at all -- a count reveals far less than a list of who's connected to whom.
--
-- Explicitly NOT building the canvas's "Referrals given" stat alongside this: there is no
-- real schema or process anywhere in this app that tracks a "referral" as a distinct,
-- countable event. Showing a number for a concept nothing actually measures would be a
-- fabricated trust signal, the same category of risk as the verification-detail strip this
-- session already declined to build -- flagged to the user rather than guessed at.

create or replace function public.get_connection_stats(p_target_id uuid)
returns table(total_connections int, mutual_connections int)
language sql
security definer
set search_path = public
stable
as $$
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
  select
    (select count(*)::int from target_conns),
    (select count(*)::int from target_conns where other_id in (select other_id from caller_conns));
$$;

grant execute on function public.get_connection_stats(uuid) to authenticated;
