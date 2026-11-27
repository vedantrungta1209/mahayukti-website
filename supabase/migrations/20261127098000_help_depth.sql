-- Upvoting, mirroring post_likes/comment_likes exactly.
create table public.help_post_votes (
  help_post_id uuid not null references public.help_posts(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (help_post_id, user_id)
);
alter table public.help_post_votes enable row level security;
create policy help_post_votes_select_active_members on public.help_post_votes
  for select using (exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active') or is_platform_admin());
create policy help_post_votes_insert_own on public.help_post_votes
  for insert with check (user_id in (select id from public.users where auth_id = auth.uid()));
create policy help_post_votes_delete_own on public.help_post_votes
  for delete using (user_id in (select id from public.users where auth_id = auth.uid()));

create table public.help_reply_votes (
  help_reply_id uuid not null references public.help_replies(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (help_reply_id, user_id)
);
alter table public.help_reply_votes enable row level security;
create policy help_reply_votes_select_active_members on public.help_reply_votes
  for select using (exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active') or is_platform_admin());
create policy help_reply_votes_insert_own on public.help_reply_votes
  for insert with check (user_id in (select id from public.users where auth_id = auth.uid()));
create policy help_reply_votes_delete_own on public.help_reply_votes
  for delete using (user_id in (select id from public.users where auth_id = auth.uid()));

-- Mark-as-best-answer: only the question's own author (or admin) may set
-- it, and only to a reply that actually belongs to that same post --
-- enforced in with_check since RLS can't easily FK-validate that any
-- other way.
alter table public.help_posts add column if not exists best_reply_id uuid references public.help_replies(id) on delete set null;

create policy help_posts_update_best_reply on public.help_posts
  for update
  using (author_id in (select id from public.users where auth_id = auth.uid()) or is_platform_admin())
  with check (
    (author_id in (select id from public.users where auth_id = auth.uid()) or is_platform_admin())
    and (best_reply_id is null or exists (select 1 from public.help_replies r where r.id = best_reply_id and r.help_post_id = help_posts.id))
  );
