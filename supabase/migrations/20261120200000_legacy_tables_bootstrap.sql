-- Six tables app.html has read/written from for a while, none ever captured
-- in a migration -- the exact situation users was in before 20261113235900,
-- caught by auditing every api('<table>', ...) call in app.html against
-- every table any migration actually creates. Without this, a fresh
-- database built from migrations alone would be missing blog_posts,
-- client_briefs, group_chats, group_messages, help_posts, and notifications
-- entirely, breaking Official Updates, admin client-brief triage, group
-- chats, MY Help, and notifications on day one.
--
-- Columns are reverse-engineered directly from every api('<table>', ...)
-- call in app.html, same method as the original users bootstrap -- not
-- invented.

begin;

-- blog_posts: admin-authored editorial content ("Official Updates" rail on
-- Home, plus the public blog). Only ever read by members; only ever written
-- by the admin "Publish an Official Update" screen.
create table if not exists public.blog_posts (
  id         uuid primary key default gen_random_uuid(),
  category   text,
  title      text not null,
  excerpt    text,
  body       text,
  date       text,       -- free-text display date, not a real timestamp (matches existing render: p.date||'')
  read_time  text,       -- free-text ("2 min read"), same reasoning
  status     text not null default 'draft' check (status in ('draft','published')),
  created_at timestamptz not null default now()
);

alter table public.blog_posts enable row level security;
drop policy if exists blog_posts_select_published on public.blog_posts;
create policy blog_posts_select_published on public.blog_posts for select using (
  status = 'published' or public.is_platform_admin()
);
drop policy if exists blog_posts_write_admin on public.blog_posts;
create policy blog_posts_write_admin on public.blog_posts for all using (public.is_platform_admin()) with check (public.is_platform_admin());

-- client_briefs: inbound consulting/service requests from CLIENTS (not
-- members) -- admin-triaged in the existing Admin > Client Briefs screen.
-- No insert path exists anywhere in this repo (app.html only ever reads and
-- PATCHes status) -- these rows get created by whatever external intake
-- process feeds the admin queue today (a form or automation outside this
-- codebase), not by anything here. RLS is admin-only for both read and
-- write; the external intake process, whatever it is, must use the service
-- role key to insert, same pattern as linkedin_connections.
create table if not exists public.client_briefs (
  id              uuid primary key default gen_random_uuid(),
  urgency         text default 'normal' check (urgency in ('normal','urgent','critical')),
  confidentiality text,
  domain_needed   text,
  description     text,
  status          text not null default 'pending' check (status in ('pending','reviewing','assigned','completed')),
  created_at      timestamptz not null default now()
);

alter table public.client_briefs enable row level security;
drop policy if exists client_briefs_admin_all on public.client_briefs;
create policy client_briefs_admin_all on public.client_briefs for all using (public.is_platform_admin()) with check (public.is_platform_admin());

-- group_chats: admin-curated broadcast/topic chat rooms open to every active
-- member (distinct from both DMs and the newer Communities system -- this
-- is simple shared chat rooms, not posts/threads).
create table if not exists public.group_chats (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  description text,
  type        text default 'general',
  created_at  timestamptz not null default now()
);

alter table public.group_chats enable row level security;
drop policy if exists group_chats_select_active_members on public.group_chats;
create policy group_chats_select_active_members on public.group_chats for select using (
  exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
  or public.is_platform_admin()
);
drop policy if exists group_chats_write_admin on public.group_chats;
create policy group_chats_write_admin on public.group_chats for all using (public.is_platform_admin()) with check (public.is_platform_admin());

create table if not exists public.group_messages (
  id         uuid primary key default gen_random_uuid(),
  chat_id    uuid not null references public.group_chats(id) on delete cascade,
  from_id    uuid not null references public.users(id) on delete cascade,
  content    text not null,
  created_at timestamptz not null default now()
);

create index if not exists group_messages_chat_idx on public.group_messages(chat_id);

alter table public.group_messages enable row level security;
drop policy if exists group_messages_select_active_members on public.group_messages;
create policy group_messages_select_active_members on public.group_messages for select using (
  exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
  or public.is_platform_admin()
);
drop policy if exists group_messages_insert_own on public.group_messages;
create policy group_messages_insert_own on public.group_messages for insert with check (
  from_id in (select id from public.users where auth_id = auth.uid())
);

-- help_posts: the live "MY Help" Q&A board -- a real, actively-written
-- feature (submitHelp has a genuine insert path), unlike the old dead
-- forum_posts this lineage already retired. Open posting/reading to every
-- active member.
create table if not exists public.help_posts (
  id          uuid primary key default gen_random_uuid(),
  author_id   uuid not null references public.users(id) on delete cascade,
  title       text not null,
  content     text not null,
  type        text default 'question',
  reply_count int not null default 0,
  created_at  timestamptz not null default now()
);

alter table public.help_posts enable row level security;
drop policy if exists help_posts_select_active_members on public.help_posts;
create policy help_posts_select_active_members on public.help_posts for select using (
  exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
  or public.is_platform_admin()
);
drop policy if exists help_posts_insert_own on public.help_posts;
create policy help_posts_insert_own on public.help_posts for insert with check (
  author_id in (select id from public.users where auth_id = auth.uid())
);

-- notifications: per-member feed, read-only from the client except marking
-- a notification as read. app.html subscribes to postgres_changes INSERT on
-- this table (setupRT's 'notifs' channel) and has no client insert path at
-- all -- whatever creates a row today must do it with the service role key
-- (same as linkedin_connections), which is also why there's no insert
-- policy for authenticated/anon below, by design, not an oversight.
create table if not exists public.notifications (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.users(id) on delete cascade,
  title      text not null,
  body       text,
  read       boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists notifications_user_idx on public.notifications(user_id);

alter table public.notifications enable row level security;
drop policy if exists notifications_select_own on public.notifications;
create policy notifications_select_own on public.notifications for select using (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists notifications_update_own_read on public.notifications;
create policy notifications_update_own_read on public.notifications for update using (
  user_id in (select id from public.users where auth_id = auth.uid())
) with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);

alter publication supabase_realtime add table public.notifications;

commit;
