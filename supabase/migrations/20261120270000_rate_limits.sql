-- The Terms & Conditions this session wrote explicitly prohibit attempting
-- to "bypass verification, rate limits, or access controls" -- but no rate
-- limit of any kind existed anywhere in this database. Nothing stopped a
-- member (or a compromised/scripted account) from posting, commenting, or
-- messaging hundreds of times a second. One generic trigger function,
-- reused across the three highest-abuse-potential tables, closes the gap
-- the legal document already claimed was closed.

begin;

create or replace function public.enforce_rate_limit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  max_count int := TG_ARGV[0]::int;
  window_secs int := TG_ARGV[1]::int;
  actor_col text := TG_ARGV[2];
  actor_val uuid;
  recent_count int;
begin
  if public.is_platform_admin() then
    return new;
  end if;
  execute format('select ($1).%I', actor_col) into actor_val using new;
  execute format(
    'select count(*) from %I where %I = $1 and created_at > now() - interval ''%s seconds''',
    TG_TABLE_NAME, actor_col, window_secs
  ) into recent_count using actor_val;
  if recent_count >= max_count then
    raise exception 'Rate limit: too many recent inserts to %s (max % per % seconds)', TG_TABLE_NAME, max_count, window_secs;
  end if;
  return new;
end;
$$;

-- 20 posts / 10 minutes -- generous for genuine use, blocks flooding.
drop trigger if exists trg_rate_limit_posts on public.posts;
create trigger trg_rate_limit_posts
  before insert on public.posts
  for each row
  execute function public.enforce_rate_limit(20, 600, 'author_id');

-- 30 comments / 10 minutes.
drop trigger if exists trg_rate_limit_post_comments on public.post_comments;
create trigger trg_rate_limit_post_comments
  before insert on public.post_comments
  for each row
  execute function public.enforce_rate_limit(30, 600, 'author_id');

-- 60 DMs / 10 minutes -- higher ceiling since a real conversation can be
-- fast-moving, but still a real ceiling against bulk-messaging the
-- directory, which the Community Guidelines also explicitly prohibit.
drop trigger if exists trg_rate_limit_messages on public.messages;
create trigger trg_rate_limit_messages
  before insert on public.messages
  for each row
  execute function public.enforce_rate_limit(60, 600, 'from_id');

commit;
