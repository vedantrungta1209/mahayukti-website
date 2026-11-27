-- Comment likes, mirroring post_likes exactly (composite PK, same RLS shape).
-- Access gating goes through can_access_post(post_comments.post_id) since
-- there's no separate per-comment visibility rule -- a comment is visible
-- (and likeable) exactly when its parent post is.
create table public.comment_likes (
  comment_id uuid not null references public.post_comments(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (comment_id, user_id)
);

alter table public.comment_likes enable row level security;

create policy comment_likes_select_all on public.comment_likes
  for select
  using (exists (select 1 from public.post_comments c where c.id = comment_id and can_access_post(c.post_id)));

create policy comment_likes_insert_own on public.comment_likes
  for insert
  with check (
    user_id in (select id from public.users where auth_id = auth.uid())
    and exists (select 1 from public.post_comments c where c.id = comment_id and can_access_post(c.post_id))
  );

create policy comment_likes_delete_own on public.comment_likes
  for delete
  using (user_id in (select id from public.users where auth_id = auth.uid()));
