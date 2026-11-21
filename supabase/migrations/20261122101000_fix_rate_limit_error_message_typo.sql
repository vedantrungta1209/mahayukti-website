-- Found while live-testing the rate limiter (confirmed it correctly blocks a 21st post
-- within the 10-minute window on public.posts): its own error message has a format-string
-- bug. Postgres RAISE EXCEPTION uses a bare `%` as its placeholder, not sprintf-style
-- `%s` -- the function's first placeholder was written as `%s`, which RAISE interprets
-- as the `%` placeholder (filled with TG_TABLE_NAME) immediately followed by a literal
-- "s" character, producing "too many recent inserts to postss" instead of "...to posts".
-- Purely cosmetic (the actual rate-limiting logic was never affected), but a real,
-- visible bug in the one piece of text anyone debugging a rate-limit rejection would see.

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
    raise exception 'Rate limit: too many recent inserts to % (max % per % seconds)', TG_TABLE_NAME, max_count, window_secs;
  end if;
  return new;
end;
$$;
