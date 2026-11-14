-- The in-app messaging UI/JS (loadConvos, openChat, sendMsg, the realtime
-- subscription in app.html) was already fully written but pointed at a
-- `messages` table that never existed in any migration -- 100% non-functional
-- until now. Columns match exactly what app.html's api('messages', ...) calls
-- use: from_id, to_id, content, created_at, read -- both ids reference
-- public.users.id (ST.profile.id), not auth.users.

create table public.messages (
  id uuid primary key default gen_random_uuid(),
  from_id uuid not null references public.users(id) on delete cascade,
  to_id uuid not null references public.users(id) on delete cascade,
  content text not null,
  read boolean not null default false,
  created_at timestamptz not null default now()
);

create index messages_from_id_idx on public.messages(from_id);
create index messages_to_id_idx on public.messages(to_id);
create index messages_created_at_idx on public.messages(created_at);

alter table public.messages enable row level security;

-- A member can read a message only if they're the sender or the recipient --
-- both sides keyed off their own users.id, resolved from auth.uid() via the
-- users table (ST.profile.id is never the auth_id itself).
create policy messages_select_own
  on public.messages for select
  to authenticated
  using (
    from_id in (select id from public.users where auth_id = auth.uid())
    or to_id in (select id from public.users where auth_id = auth.uid())
  );

-- Can only ever send AS yourself -- from_id must resolve to the caller's own
-- users.id, same pattern as users_insert_own.
create policy messages_insert_own
  on public.messages for insert
  to authenticated
  with check (from_id in (select id from public.users where auth_id = auth.uid()));

-- Only the recipient can mark a message read (the only UPDATE app.html ever does).
create policy messages_update_recipient_read
  on public.messages for update
  to authenticated
  using (to_id in (select id from public.users where auth_id = auth.uid()))
  with check (to_id in (select id from public.users where auth_id = auth.uid()));

-- app.html subscribes to postgres_changes on this table (sb.channel('chat')...) --
-- that only fires if the table is in the realtime publication.
alter publication supabase_realtime add table public.messages;
