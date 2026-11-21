-- Settings/Privacy (who can message you, blocked users) and Feed Preferences
-- (sector weighting, muting, saved posts).
--
-- Deliberately NOT adding show_phone/show_email toggles: the profile screen's
-- own copy already states phone numbers are never shown to anyone, full stop
-- -- that's a hardcoded platform policy, not a per-member setting, so a
-- toggle for it would be fake configurability. Email works the same way
-- already (never rendered in the directory or any profile view). Only
-- messaging permission is a real per-member choice.

begin;

alter table public.users add column if not exists allow_messages_from text not null default 'everyone'
  check (allow_messages_from in ('connections','everyone'));

create table if not exists public.blocked_users (
  blocker_id uuid not null references public.users(id) on delete cascade,
  blocked_id uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (blocker_id, blocked_id),
  constraint blocked_users_not_self check (blocker_id <> blocked_id)
);

create table if not exists public.saved_posts (
  user_id    uuid not null references public.users(id) on delete cascade,
  post_id    uuid not null references public.posts(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, post_id)
);

create table if not exists public.muted_users (
  muter_id   uuid not null references public.users(id) on delete cascade,
  muted_id   uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (muter_id, muted_id),
  constraint muted_users_not_self check (muter_id <> muted_id)
);

create table if not exists public.muted_hashtags (
  user_id    uuid not null references public.users(id) on delete cascade,
  hashtag_id uuid not null references public.hashtags(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, hashtag_id)
);

create table if not exists public.user_bucket_weights (
  user_id    uuid not null references public.users(id) on delete cascade,
  bucket_id  uuid not null references public.buckets(id) on delete cascade,
  weight     text not null default 'normal' check (weight in ('more','normal','less')),
  primary key (user_id, bucket_id)
);

alter table public.blocked_users      enable row level security;
alter table public.saved_posts        enable row level security;
alter table public.muted_users        enable row level security;
alter table public.muted_hashtags     enable row level security;
alter table public.user_bucket_weights enable row level security;

drop policy if exists blocked_users_select_own on public.blocked_users;
create policy blocked_users_select_own on public.blocked_users for select using (
  blocker_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists blocked_users_insert_own on public.blocked_users;
create policy blocked_users_insert_own on public.blocked_users for insert with check (
  blocker_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists blocked_users_delete_own on public.blocked_users;
create policy blocked_users_delete_own on public.blocked_users for delete using (
  blocker_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists saved_posts_select_own on public.saved_posts;
create policy saved_posts_select_own on public.saved_posts for select using (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists saved_posts_insert_own on public.saved_posts;
create policy saved_posts_insert_own on public.saved_posts for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists saved_posts_delete_own on public.saved_posts;
create policy saved_posts_delete_own on public.saved_posts for delete using (
  user_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists muted_users_select_own on public.muted_users;
create policy muted_users_select_own on public.muted_users for select using (
  muter_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists muted_users_insert_own on public.muted_users;
create policy muted_users_insert_own on public.muted_users for insert with check (
  muter_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists muted_users_delete_own on public.muted_users;
create policy muted_users_delete_own on public.muted_users for delete using (
  muter_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists muted_hashtags_select_own on public.muted_hashtags;
create policy muted_hashtags_select_own on public.muted_hashtags for select using (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists muted_hashtags_insert_own on public.muted_hashtags;
create policy muted_hashtags_insert_own on public.muted_hashtags for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists muted_hashtags_delete_own on public.muted_hashtags;
create policy muted_hashtags_delete_own on public.muted_hashtags for delete using (
  user_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists user_bucket_weights_select_own on public.user_bucket_weights;
create policy user_bucket_weights_select_own on public.user_bucket_weights for select using (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists user_bucket_weights_upsert_own on public.user_bucket_weights;
create policy user_bucket_weights_upsert_own on public.user_bucket_weights for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);
drop policy if exists user_bucket_weights_update_own on public.user_bucket_weights;
create policy user_bucket_weights_update_own on public.user_bucket_weights for update using (
  user_id in (select id from public.users where auth_id = auth.uid())
);

-- Enforce allow_messages_from where it actually matters: the existing
-- messages_insert_own policy (20261114210000) only ever checked that the
-- sender was who they claimed to be -- it had no idea the setting above
-- exists, so adding the column without this would make it decorative.
-- A sender can always message the recipient if either side has an accepted
-- member_connection, regardless of the recipient's setting -- "connections
-- only" means connections only, not "nobody."
drop policy if exists messages_insert_own on public.messages;
create policy messages_insert_own on public.messages for insert
  to authenticated
  with check (
    from_id in (select id from public.users where auth_id = auth.uid())
    and not exists (
      select 1 from public.blocked_users bu
      where (bu.blocker_id = messages.to_id and bu.blocked_id = messages.from_id)
         or (bu.blocker_id = messages.from_id and bu.blocked_id = messages.to_id)
    )
    and (
      (select allow_messages_from from public.users where id = messages.to_id) = 'everyone'
      or exists (
        select 1 from public.member_connections mc
        where mc.status = 'accepted'
          and ((mc.requester_id = messages.from_id and mc.addressee_id = messages.to_id)
            or (mc.requester_id = messages.to_id and mc.addressee_id = messages.from_id))
      )
    )
  );

commit;
