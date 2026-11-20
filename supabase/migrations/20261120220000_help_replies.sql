-- MY Help has a real, actively-used post path (submitHelp) but the
-- reply_count shown on every card was never backed by anything -- no table,
-- no insert path, no way to even view a reply if one existed. Every post
-- was permanently stuck at "0 replies" while presenting itself as a Q&A
-- board ("Ask the first question"). Adding the missing half.

begin;

create table if not exists public.help_replies (
  id           uuid primary key default gen_random_uuid(),
  help_post_id uuid not null references public.help_posts(id) on delete cascade,
  author_id    uuid not null references public.users(id) on delete cascade,
  content      text not null,
  created_at   timestamptz not null default now()
);

create index if not exists help_replies_post_idx on public.help_replies(help_post_id);

alter table public.help_replies enable row level security;

drop policy if exists help_replies_select_active_members on public.help_replies;
create policy help_replies_select_active_members on public.help_replies for select using (
  exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
  or public.is_platform_admin()
);
drop policy if exists help_replies_insert_own on public.help_replies;
create policy help_replies_insert_own on public.help_replies for insert with check (
  author_id in (select id from public.users where auth_id = auth.uid())
);

commit;
