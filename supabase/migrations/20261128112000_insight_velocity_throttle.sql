-- Anti-LLM-farming velocity throttle on Flash Intelligence: the 500-char/
-- link-free CHECK constraint (20261128104000) stops growth-hacking spam
-- shape, but does nothing to stop a member running an LLM to generate many
-- generic "insights" per day to pump their own visibility in a sector hub.
-- "True Flash Intelligence is rare" -- enforcing scarcity (2 posts per
-- rolling 24h) is the actual anti-farming lever, not content filtering.
create or replace function public.enforce_insight_velocity_throttle()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_cap constant int := 2; -- max insights per rolling 24h
  v_recent_count int;
begin
  select count(*) into v_recent_count
  from public.member_insights
  where author_id = new.author_id
    and created_at > now() - interval '24 hours';

  if v_recent_count >= v_cap then
    raise exception 'insight_velocity_cap_reached';
  end if;

  return new;
end;
$$;

drop trigger if exists trg_enforce_insight_velocity_throttle on public.member_insights;
create trigger trg_enforce_insight_velocity_throttle
  before insert on public.member_insights
  for each row
  execute function public.enforce_insight_velocity_throttle();
