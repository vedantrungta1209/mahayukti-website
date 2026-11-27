-- Notification preference center: until now every notification type fired
-- unconditionally, in-app bell and push alike, with no way to turn any of
-- them off. Adds a category to every notification-producing trigger and a
-- per-user preferences row gating whether that category's row (and
-- therefore its push) ever gets created at all -- gated at the trigger,
-- not just hidden client-side, so a disabled category also means no push
-- fires for it.
alter table public.notifications add column if not exists category text;

create table public.notification_preferences (
  user_id uuid primary key references public.users(id) on delete cascade,
  disabled_categories text[] not null default '{}',
  updated_at timestamptz not null default now()
);

alter table public.notification_preferences enable row level security;

create policy notification_preferences_select_own on public.notification_preferences
  for select using (user_id in (select id from public.users where auth_id = auth.uid()));
create policy notification_preferences_insert_own on public.notification_preferences
  for insert with check (user_id in (select id from public.users where auth_id = auth.uid()));
create policy notification_preferences_update_own on public.notification_preferences
  for update using (user_id in (select id from public.users where auth_id = auth.uid()));

-- Shared by every notify_* trigger below instead of each one repeating the
-- same "has this user muted this category" subquery.
create or replace function public.notifications_category_enabled(p_user_id uuid, p_category text)
returns boolean
language sql
stable security definer
set search_path to 'public'
as $$
  select not coalesce(
    (select p_category = any(disabled_categories) from public.notification_preferences where user_id = p_user_id),
    false
  );
$$;

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
  if post_author_id is not null and post_author_id <> new.author_id
     and notifications_category_enabled(post_author_id, 'comment') then
    select username into commenter_username from public.users where id = new.author_id;
    insert into public.notifications (user_id, title, body, link_type, link_id, category)
    values (
      post_author_id,
      'New comment on your post',
      '@' || coalesce(commenter_username, 'A member') || ' commented: ' || left(new.body, 140),
      'post', new.post_id, 'comment'
    );
  end if;
  return new;
end;
$function$;

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
    if mentioned_user_id is not null and mentioned_user_id <> mentioning_user_id
       and notifications_category_enabled(mentioned_user_id, 'mention') then
      insert into public.notifications (user_id, title, body, link_type, link_id, category)
      values (
        mentioned_user_id,
        'You were mentioned',
        '@' || coalesce(actor_username, 'A member') || ' mentioned you ' || context_label || ': ' || left(body_text, 140),
        p_link_type, p_link_id, 'mention'
      );
    end if;
  end loop;
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
  if new.status = 'accepted' and (old.status is distinct from 'accepted')
     and notifications_category_enabled(new.requester_id, 'connection') then
    select username into addressee_username from public.users where id = new.addressee_id;
    insert into public.notifications (user_id, title, body, link_type, link_id, category)
    values (
      new.requester_id,
      'Connection accepted',
      '@' || coalesce(addressee_username, 'A member') || ' accepted your connection request.',
      'member', new.addressee_id, 'connection'
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
  if new.status = 'pending' and notifications_category_enabled(new.addressee_id, 'connection') then
    select username into requester_username from public.users where id = new.requester_id;
    insert into public.notifications (user_id, title, body, link_type, link_id, category)
    values (
      new.addressee_id,
      'New connection request',
      '@' || coalesce(requester_username, 'A member') || ' wants to connect with you.',
      'member', new.requester_id, 'connection'
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
  if notifications_category_enabled(new.followee_id, 'follower') then
    select username into follower_username from public.users where id = new.follower_id;
    insert into public.notifications (user_id, title, body, link_type, link_id, category)
    values (
      new.followee_id,
      'New follower',
      '@' || coalesce(follower_username, 'A member') || ' started following you.',
      'member', new.follower_id, 'follower'
    );
  end if;
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
  if notifications_category_enabled(new.to_id, 'message') then
    select username into sender_username from public.users where id = new.from_id;
    insert into public.notifications (user_id, title, body, link_type, link_id, category)
    values (
      new.to_id,
      'New message from @' || coalesce(sender_username, 'a member'),
      left(new.content, 140),
      'chat', new.from_id, 'message'
    );
  end if;
  return new;
end;
$function$;
