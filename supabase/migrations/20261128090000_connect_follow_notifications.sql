-- Two real gaps found live: sending a connection REQUEST never notified the
-- recipient at all (only notify_connection_accepted existed, which fires
-- the other way -- telling the requester once the OTHER person accepts).
-- Following someone had no notification trigger whatsoever. Both mirror the
-- existing notify_post_comment/notify_connection_accepted SECURITY DEFINER
-- shape exactly.
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
    insert into public.notifications (user_id, title, body)
    values (
      new.addressee_id,
      'New connection request',
      '@' || coalesce(requester_username, 'A member') || ' wants to connect with you.'
    );
  end if;
  return new;
end;
$function$;

create trigger trg_notify_connection_requested after insert on public.member_connections
  for each row execute function public.notify_connection_requested();

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
  insert into public.notifications (user_id, title, body)
  values (
    new.followee_id,
    'New follower',
    '@' || coalesce(follower_username, 'A member') || ' started following you.'
  );
  return new;
end;
$function$;

create trigger trg_notify_new_follower after insert on public.follows
  for each row execute function public.notify_new_follower();
