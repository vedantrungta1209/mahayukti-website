-- Tapping a notification (in the bell list, or a push) only ever marked it
-- read -- never actually took you to the post/profile/chat it was about.
-- Adds link_type/link_id to every existing notification-producing function
-- so both the in-app bell and a push tap can navigate to the right place.
alter table public.notifications add column if not exists link_type text check (link_type in ('post','member','chat'));
alter table public.notifications add column if not exists link_id uuid;

create or replace function public.notify_post_comment()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  post_author_id uuid;
  commenter_username text;
begin
  select author_id into post_author_id from public.posts where id = new.post_id;
  if post_author_id is not null and post_author_id <> new.author_id then
    select username into commenter_username from public.users where id = new.author_id;
    insert into public.notifications (user_id, title, body, link_type, link_id)
    values (
      post_author_id,
      'New comment on your post',
      '@' || coalesce(commenter_username, 'A member') || ' commented: ' || left(new.body, 140),
      'post', new.post_id
    );
  end if;
  return new;
end;
$function$;

-- Replacing a function with a different parameter list creates a new
-- overload rather than actually replacing the old one -- drop the old
-- 3-arg signature explicitly so it doesn't linger as dead, unused code.
drop function if exists public.notify_mentions(uuid, text, text);

create or replace function public.notify_mentions(mentioning_user_id uuid, body_text text, context_label text, p_link_type text, p_link_id uuid)
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
      insert into public.notifications (user_id, title, body, link_type, link_id)
      values (
        mentioned_user_id,
        'You were mentioned',
        '@' || coalesce(actor_username, 'A member') || ' mentioned you ' || context_label || ': ' || left(body_text, 140),
        p_link_type, p_link_id
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
  perform public.notify_mentions(new.author_id, coalesce(new.body, ''), 'in a post', 'post', new.id);
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
  -- Mentions inside a comment open the post thread (the comment itself has
  -- no standalone screen) -- same link_type as a post mention.
  perform public.notify_mentions(new.author_id, coalesce(new.body, ''), 'in a comment', 'post', new.post_id);
  return new;
end;
$function$;

create or replace function public.notify_connection_accepted()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  addressee_username text;
begin
  if new.status = 'accepted' and (old.status is distinct from 'accepted') then
    select username into addressee_username from public.users where id = new.addressee_id;
    insert into public.notifications (user_id, title, body, link_type, link_id)
    values (
      new.requester_id,
      'Connection accepted',
      '@' || coalesce(addressee_username, 'A member') || ' accepted your connection request.',
      'member', new.addressee_id
    );
  end if;
  return new;
end;
$function$;

create or replace function public.notify_connection_requested()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  requester_username text;
begin
  if new.status = 'pending' then
    select username into requester_username from public.users where id = new.requester_id;
    insert into public.notifications (user_id, title, body, link_type, link_id)
    values (
      new.addressee_id,
      'New connection request',
      '@' || coalesce(requester_username, 'A member') || ' wants to connect with you.',
      'member', new.requester_id
    );
  end if;
  return new;
end;
$function$;

create or replace function public.notify_new_follower()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  follower_username text;
begin
  select username into follower_username from public.users where id = new.follower_id;
  insert into public.notifications (user_id, title, body, link_type, link_id)
  values (
    new.followee_id,
    'New follower',
    '@' || coalesce(follower_username, 'A member') || ' started following you.',
    'member', new.follower_id
  );
  return new;
end;
$function$;

create or replace function public.notify_new_message()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  sender_username text;
begin
  select username into sender_username from public.users where id = new.from_id;
  insert into public.notifications (user_id, title, body, link_type, link_id)
  values (
    new.to_id,
    'New message from @' || coalesce(sender_username, 'a member'),
    left(new.content, 140),
    'chat', new.from_id
  );
  return new;
end;
$function$;
