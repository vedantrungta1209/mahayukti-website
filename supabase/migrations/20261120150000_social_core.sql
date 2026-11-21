-- Social core: posts, likes, comments, hashtags, member-to-member connect/follow,
-- and communities (one shared primitive for open topic forums and institution-
-- verified alumni groups, per the architecture doc's "new account type is mostly
-- configuration" principle).
--
-- Naming note: `member_connections` (below) is the LinkedIn-style "add as a
-- connection, needs acceptance" feature between two MahaYukti members. Do not
-- confuse it with the existing `linkedin_connections` table (20261114180000),
-- which stores a member's OAuth token to LinkedIn-the-platform for cross-
-- posting -- an unrelated feature that happens to share a word in its name.
--
-- All author/actor columns reference public.users(id) (ST.profile.id), the same
-- convention `messages` already uses -- never auth.users directly.
--
-- Not applied to the live database from this session -- ready to run, held for
-- review, same as every other migration on this branch's lineage.

begin;

-- =========================================================================
-- 1. Posts, likes, comments
-- =========================================================================

create table if not exists public.posts (
  id                   uuid primary key default gen_random_uuid(),
  author_id            uuid not null references public.users(id) on delete cascade,
  body                 text not null,
  -- The sector the poster is attributing this post to (shown on the card, used for
  -- "shown because: in your sector" feed transparency). Null only for official updates.
  bucket_id            uuid references public.buckets(id),
  -- Who the poster chose to reach -- the audience selector in the composer:
  --   'sector'      -> just bucket_id above
  --   'buckets'     -> bucket_id above + every id in audience_bucket_ids
  --   'connections' -> accepted member_connections only, any sector
  --   'everyone'    -> no targeting at all
  audience             text not null default 'sector'
                         check (audience in ('sector','buckets','connections','everyone')),
  audience_bucket_ids  uuid[],
  link_url             text,   -- external embed (YouTube/Spotify/article) the composer auto-detected
  link_title           text,
  image_url            text,
  is_article           boolean not null default false,   -- long-form Article vs a short post
  is_sponsored         boolean not null default false,
  sponsor_user_id       uuid references public.users(id), -- who paid, when is_sponsored
  -- community_id/title/pinned were originally only added later via ALTER
  -- TABLE in 20261120160000, but posts_insert_own below (in THIS file's own
  -- RLS section) already needs community_id to exist -- caught only by an
  -- actual `supabase db push` against the real database, which is exactly
  -- the kind of ordering bug a text read-through or JS syntax check can
  -- never catch. Defined here from the start instead. No inline FK to
  -- communities(id) -- that table doesn't exist yet at this point in the
  -- file (it's created in section 4, below) -- the constraint is added
  -- right after communities itself is created instead.
  community_id         uuid,
  title                text,
  pinned               boolean not null default false,
  created_at           timestamptz not null default now()
);

create index if not exists posts_author_idx on public.posts(author_id);
create index if not exists posts_bucket_idx on public.posts(bucket_id);
create index if not exists posts_created_idx on public.posts(created_at desc);
create index if not exists posts_community_idx on public.posts(community_id);

create table if not exists public.post_likes (
  post_id    uuid not null references public.posts(id) on delete cascade,
  user_id    uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (post_id, user_id)
);

create table if not exists public.post_comments (
  id                 uuid primary key default gen_random_uuid(),
  post_id            uuid not null references public.posts(id) on delete cascade,
  author_id          uuid not null references public.users(id) on delete cascade,
  parent_comment_id  uuid references public.post_comments(id) on delete cascade,
  body               text not null,
  created_at         timestamptz not null default now()
);

create index if not exists post_comments_post_idx on public.post_comments(post_id);

-- =========================================================================
-- 2. Hashtags
-- =========================================================================

create table if not exists public.hashtags (
  id  uuid primary key default gen_random_uuid(),
  tag text not null unique  -- stored lowercase, without the '#'
);

create table if not exists public.post_hashtags (
  post_id    uuid not null references public.posts(id) on delete cascade,
  hashtag_id uuid not null references public.hashtags(id) on delete cascade,
  primary key (post_id, hashtag_id)
);

-- =========================================================================
-- 3. Connect (needs acceptance, like Facebook/LinkedIn) and Follow (one-way,
--    no acceptance, like X/Instagram) -- deliberately two separate mechanisms.
-- =========================================================================

create table if not exists public.member_connections (
  requester_id  uuid not null references public.users(id) on delete cascade,
  addressee_id  uuid not null references public.users(id) on delete cascade,
  status        text not null default 'pending' check (status in ('pending','accepted','declined')),
  created_at    timestamptz not null default now(),
  responded_at  timestamptz,
  primary key (requester_id, addressee_id),
  constraint member_connections_not_self check (requester_id <> addressee_id)
);

create index if not exists member_connections_addressee_idx on public.member_connections(addressee_id);

create table if not exists public.follows (
  follower_id uuid not null references public.users(id) on delete cascade,
  followee_id uuid not null references public.users(id) on delete cascade,
  created_at  timestamptz not null default now(),
  primary key (follower_id, followee_id),
  constraint follows_not_self check (follower_id <> followee_id)
);

create index if not exists follows_followee_idx on public.follows(followee_id);

-- =========================================================================
-- 4. Communities -- one shared primitive for open topic forums and
--    institution-verified alumni groups. The only difference is the
--    verification rule on join, not a second code path.
-- =========================================================================

create table if not exists public.communities (
  id                     uuid primary key default gen_random_uuid(),
  name                   text not null,
  kind                   text not null check (kind in ('topic','institution')),
  bucket_id              uuid references public.buckets(id),  -- topic communities tag a sector
  institution_name       text,                                  -- institution communities store the school/college
  requires_verification  boolean not null default false,        -- true for 'institution' kind
  created_by             uuid references public.users(id),
  created_at             timestamptz not null default now()
);

create table if not exists public.community_members (
  community_id uuid not null references public.communities(id) on delete cascade,
  user_id      uuid not null references public.users(id) on delete cascade,
  -- 'pending' = requested to join an institution community, awaiting verification
  status       text not null default 'active' check (status in ('active','pending')),
  joined_at    timestamptz not null default now(),
  primary key (community_id, user_id)
);

create index if not exists community_members_user_idx on public.community_members(user_id);

-- Now that communities exists, add the FK posts.community_id couldn't
-- declare inline above.
do $$
begin
  if not exists (
    select 1 from information_schema.table_constraints
    where constraint_name = 'posts_community_id_fkey' and table_name = 'posts'
  ) then
    alter table public.posts
      add constraint posts_community_id_fkey
      foreign key (community_id) references public.communities(id);
  end if;
end $$;

-- =========================================================================
-- RLS
-- =========================================================================

alter table public.posts              enable row level security;
alter table public.post_likes          enable row level security;
alter table public.post_comments       enable row level security;
alter table public.hashtags            enable row level security;
alter table public.post_hashtags       enable row level security;
alter table public.member_connections  enable row level security;
alter table public.follows             enable row level security;
alter table public.communities         enable row level security;
alter table public.community_members   enable row level security;

-- Posts: audience filtering happens in the app's query (bucket match / connection
-- match / everyone), not in RLS -- RLS here only enforces "active members and
-- admins can read; you can only write as yourself." Narrowing to the right
-- audience is a feed-ranking concern, not a security boundary, since every post
-- is from a verified member of the same trust register, never public internet.
drop policy if exists posts_select_active_members on public.posts;
create policy posts_select_active_members on public.posts for select using (
  exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
  or public.is_platform_admin()
);

-- Originally just checked author identity -- anyone could set community_id
-- to ANY community, including one they were never approved into (an
-- institution community's pending-verification queue existed specifically
-- to gate this), and post there directly via a plain API call bypassing the
-- UI's own joinCommunityIfNeeded flow entirely. community_id is nullable on
-- purpose (an ordinary feed post has none) so the check only applies when
-- it's actually set.
drop policy if exists posts_insert_own on public.posts;
create policy posts_insert_own on public.posts for insert with check (
  author_id in (select id from public.users where auth_id = auth.uid())
  and (
    community_id is null
    or exists (
      select 1 from public.community_members cm
      where cm.community_id = posts.community_id
        and cm.user_id = posts.author_id
        and cm.status = 'active'
    )
  )
);

drop policy if exists posts_delete_own_or_admin on public.posts;
create policy posts_delete_own_or_admin on public.posts for delete using (
  author_id in (select id from public.users where auth_id = auth.uid())
  or public.is_platform_admin()
);

drop policy if exists post_likes_select_all on public.post_likes;
create policy post_likes_select_all on public.post_likes for select using (true);

drop policy if exists post_likes_insert_own on public.post_likes;
create policy post_likes_insert_own on public.post_likes for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists post_likes_delete_own on public.post_likes;
create policy post_likes_delete_own on public.post_likes for delete using (
  user_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists post_comments_select_all on public.post_comments;
create policy post_comments_select_all on public.post_comments for select using (true);

drop policy if exists post_comments_insert_own on public.post_comments;
create policy post_comments_insert_own on public.post_comments for insert with check (
  author_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists post_comments_delete_own_or_admin on public.post_comments;
create policy post_comments_delete_own_or_admin on public.post_comments for delete using (
  author_id in (select id from public.users where auth_id = auth.uid())
  or public.is_platform_admin()
);

drop policy if exists hashtags_select_all on public.hashtags;
create policy hashtags_select_all on public.hashtags for select using (true);
drop policy if exists hashtags_insert_authenticated on public.hashtags;
create policy hashtags_insert_authenticated on public.hashtags for insert with check (auth.role() = 'authenticated');

drop policy if exists post_hashtags_select_all on public.post_hashtags;
create policy post_hashtags_select_all on public.post_hashtags for select using (true);
drop policy if exists post_hashtags_insert_own_post on public.post_hashtags;
create policy post_hashtags_insert_own_post on public.post_hashtags for insert with check (
  exists (select 1 from public.posts p join public.users u on u.id = p.author_id
          where p.id = post_hashtags.post_id and u.auth_id = auth.uid())
);

-- Connections: either side of a pending/accepted request can see the row; only
-- the requester can create it; only the addressee can change its status.
drop policy if exists member_connections_select_participant on public.member_connections;
create policy member_connections_select_participant on public.member_connections for select using (
  requester_id in (select id from public.users where auth_id = auth.uid())
  or addressee_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists member_connections_insert_own on public.member_connections;
create policy member_connections_insert_own on public.member_connections for insert with check (
  requester_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists member_connections_update_addressee on public.member_connections;
create policy member_connections_update_addressee on public.member_connections for update using (
  addressee_id in (select id from public.users where auth_id = auth.uid())
) with check (
  addressee_id in (select id from public.users where auth_id = auth.uid())
);

-- No delete policy existed at all -- neither disconnecting from someone
-- normally, nor the block flow's own connection cleanup, could ever work;
-- both would be silently rejected by RLS's default deny. Either side of a
-- connection can remove it, same as either side being able to see it.
drop policy if exists member_connections_delete_participant on public.member_connections;
create policy member_connections_delete_participant on public.member_connections for delete using (
  requester_id in (select id from public.users where auth_id = auth.uid())
  or addressee_id in (select id from public.users where auth_id = auth.uid())
);

-- Follows: public read (an active member's follow graph isn't private), write
-- only as yourself.
drop policy if exists follows_select_all on public.follows;
create policy follows_select_all on public.follows for select using (true);

drop policy if exists follows_insert_own on public.follows;
create policy follows_insert_own on public.follows for insert with check (
  follower_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists follows_delete_own on public.follows;
create policy follows_delete_own on public.follows for delete using (
  follower_id in (select id from public.users where auth_id = auth.uid())
);

-- Communities: public read (the directory browses all of them); creating one
-- is open for 'topic' kind, admin-only for 'institution' kind (institution
-- verification is a manual review step, same queue as org account verification).
drop policy if exists communities_select_all on public.communities;
create policy communities_select_all on public.communities for select using (true);

drop policy if exists communities_insert on public.communities;
create policy communities_insert on public.communities for insert with check (
  (kind = 'topic' and auth.role() = 'authenticated')
  or (kind = 'institution' and public.is_platform_admin())
);

drop policy if exists community_members_select_all on public.community_members;
create policy community_members_select_all on public.community_members for select using (true);

drop policy if exists community_members_insert_own on public.community_members;
create policy community_members_insert_own on public.community_members for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
);

drop policy if exists community_members_delete_own on public.community_members;
create policy community_members_delete_own on public.community_members for delete using (
  user_id in (select id from public.users where auth_id = auth.uid())
  or public.is_platform_admin()
);

-- No update policy existed at all -- approving a pending institution-
-- community member (PATCH status='active') would have been silently
-- rejected by RLS's default deny, same class of bug as the delete-only-own
-- policy above blocking an admin's deny action.
drop policy if exists community_members_update_admin on public.community_members;
create policy community_members_update_admin on public.community_members for update using (
  public.is_platform_admin()
) with check (
  public.is_platform_admin()
);

-- Realtime: the feed and comment thread want live updates the same way
-- messages already do.
alter publication supabase_realtime add table public.posts;
alter publication supabase_realtime add table public.post_comments;
alter publication supabase_realtime add table public.post_likes;

commit;
