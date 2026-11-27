-- Image attachments in DMs and group chats (text-only today).
alter table public.messages add column if not exists image_url text;
alter table public.group_messages add column if not exists image_url text;

-- User-created group chats. group_chats_write_admin already covers admin
-- for every command; this adds a second, narrower path for any active
-- member to create one of their own. created_by lets a creator manage
-- their own group later without needing admin.
alter table public.group_chats add column if not exists created_by uuid references public.users(id) on delete set null;

create policy group_chats_insert_active_members on public.group_chats
  for insert
  with check (
    exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
    and created_by in (select id from public.users where auth_id = auth.uid())
  );
