-- Real push notification delivery. Until now `notifications` only ever
-- populated the in-app bell -- nothing anywhere sent an actual device push.
-- This wires every notification type (mentions, comments, DMs, connection
-- requests, new followers, etc. -- everything that already inserts into
-- notifications) through to a real push, generically, rather than bolting
-- push logic onto each individual notification trigger one at a time.

create extension if not exists pg_net with schema extensions;

-- One row per registered device (a member can have more than one -- phone
-- + tablet, or a reinstall before the old token naturally expires).
create table public.push_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  token text not null,
  platform text not null check (platform in ('ios','android')),
  created_at timestamptz not null default now(),
  unique (user_id, token)
);

alter table public.push_tokens enable row level security;

create policy push_tokens_insert_own on public.push_tokens
  for insert
  with check (user_id in (select id from public.users where auth_id = auth.uid()));

create policy push_tokens_select_own on public.push_tokens
  for select
  using (user_id in (select id from public.users where auth_id = auth.uid()) or is_platform_admin());

create policy push_tokens_delete_own on public.push_tokens
  for delete
  using (user_id in (select id from public.users where auth_id = auth.uid()) or is_platform_admin());

-- Fires on every new notification row, regardless of which feature created
-- it, and asynchronously calls the send-push Edge Function via pg_net (a
-- plain SQL trigger can't make an HTTP call itself). SECURITY DEFINER +
-- pg_net's own async queue means a slow/failed push send can never block
-- or roll back the insert that created the in-app notification -- the bell
-- always works even if a push fails or FCM is down.
-- send-push is deployed with JWT verification off (this call is a
-- server-to-server trigger, not a user request) and only ever reads the
-- already-inserted notification row by id -- nothing client-controlled
-- reaches it through this path.
create or replace function public.trigger_send_push()
returns trigger
language plpgsql
security definer
set search_path to 'public', 'extensions'
as $function$
begin
  perform net.http_post(
    url := 'https://npyoyylrqprawyavnfvv.supabase.co/functions/v1/send-push',
    headers := jsonb_build_object('Content-Type', 'application/json'),
    body := jsonb_build_object('notification_id', new.id)
  );
  return new;
end;
$function$;

create trigger trg_send_push after insert on public.notifications
  for each row execute function public.trigger_send_push();
