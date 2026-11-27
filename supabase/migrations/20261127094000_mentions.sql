-- @mentions: notify a mentioned member, mirroring notify_post_comment's
-- shape exactly (SECURITY DEFINER so it can insert into notifications for
-- someone other than the actor, same trust boundary already accepted for
-- comment notifications).
create or replace function public.notify_mentions(mentioning_user_id uuid, body_text text, context_label text)
returns void
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  mentioned_username text;
  mentioned_user_id uuid;
  actor_username text;
begin
  select username into actor_username from public.users where id = mentioning_user_id;
  for mentioned_username in
    select distinct lower(m[1]) from regexp_matches(body_text, '@([a-zA-Z][a-zA-Z0-9_]{1,29})', 'g') as m
  loop
    select id into mentioned_user_id from public.users where lower(username) = mentioned_username and status = 'active';
    if mentioned_user_id is not null and mentioned_user_id <> mentioning_user_id then
      insert into public.notifications (user_id, title, body)
      values (
        mentioned_user_id,
        'You were mentioned',
        '@' || coalesce(actor_username, 'A member') || ' mentioned you ' || context_label || ': ' || left(body_text, 140)
      );
    end if;
  end loop;
end;
$function$;

create or replace function public.notify_post_mentions()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
begin
  perform public.notify_mentions(new.author_id, coalesce(new.body, ''), 'in a post');
  return new;
end;
$function$;

create or replace function public.notify_comment_mentions()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
begin
  perform public.notify_mentions(new.author_id, coalesce(new.body, ''), 'in a comment');
  return new;
end;
$function$;

create trigger trg_notify_post_mentions after insert on public.posts
  for each row execute function public.notify_post_mentions();

create trigger trg_notify_comment_mentions after insert on public.post_comments
  for each row execute function public.notify_comment_mentions();
