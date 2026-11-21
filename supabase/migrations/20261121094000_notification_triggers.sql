-- Closes a real, significant gap found during this session's audit: the notifications
-- feature (bell, badge, mark-read, realtime subscription) was fully built on the read
-- side, but nothing anywhere -- not the client, not an edge function, not a trigger --
-- ever inserted a row into public.notifications. Confirmed via full-codebase search and
-- a 0-row count in production. Per the user's explicit choice: notify on new messages,
-- connection accepted, and post comments.
--
-- Implemented as triggers, not client-side inserts after each action, so every insert
-- path (the app's own UI, a future client, or a direct API call) reliably produces a
-- notification -- consistent with this session's general approach of enforcing things
-- server-side rather than trusting the client to remember to do it. Each function is
-- SECURITY DEFINER because there is intentionally no INSERT policy on notifications for
-- the `authenticated` role (nobody client-facing should be able to fabricate a
-- notification for another user) -- these triggers are the one legitimate writer.

create or replace function public.notify_new_message()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  sender_username text;
begin
  select username into sender_username from public.users where id = new.from_id;
  insert into public.notifications (user_id, title, body)
  values (
    new.to_id,
    'New message from @' || coalesce(sender_username, 'a member'),
    left(new.content, 140)
  );
  return new;
end;
$$;

drop trigger if exists trg_notify_new_message on public.messages;
create trigger trg_notify_new_message
after insert on public.messages
for each row execute function public.notify_new_message();

create or replace function public.notify_connection_accepted()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  addressee_username text;
begin
  if new.status = 'accepted' and (old.status is distinct from 'accepted') then
    select username into addressee_username from public.users where id = new.addressee_id;
    insert into public.notifications (user_id, title, body)
    values (
      new.requester_id,
      'Connection accepted',
      '@' || coalesce(addressee_username, 'A member') || ' accepted your connection request.'
    );
  end if;
  return new;
end;
$$;

drop trigger if exists trg_notify_connection_accepted on public.member_connections;
create trigger trg_notify_connection_accepted
after update on public.member_connections
for each row execute function public.notify_connection_accepted();

create or replace function public.notify_post_comment()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  post_author_id uuid;
  commenter_username text;
begin
  select author_id into post_author_id from public.posts where id = new.post_id;
  -- Don't notify someone for commenting on their own post.
  if post_author_id is not null and post_author_id <> new.author_id then
    select username into commenter_username from public.users where id = new.author_id;
    insert into public.notifications (user_id, title, body)
    values (
      post_author_id,
      'New comment on your post',
      '@' || coalesce(commenter_username, 'A member') || ' commented: ' || left(new.body, 140)
    );
  end if;
  return new;
end;
$$;

drop trigger if exists trg_notify_post_comment on public.post_comments;
create trigger trg_notify_post_comment
after insert on public.post_comments
for each row execute function public.notify_post_comment();
