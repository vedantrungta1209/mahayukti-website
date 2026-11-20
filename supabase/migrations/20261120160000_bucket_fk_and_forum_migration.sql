-- Two corrections, decided with Vedant after reviewing the live schema:
--
-- 1. users.domain_group turns out to already store the same 13 sector names as
--    app.html's own BUCKETS constant (confirmed: the signup form writes
--    $('a-bucket').value straight into it) -- there was never a second, truly
--    different taxonomy, just free text instead of a foreign key. This adds a
--    real bucket_id FK and backfills it by exact name match. domain_group is
--    left in place (nothing reads it is removed) but is now the display copy,
--    not the source of truth -- new code should join through bucket_id.
--
-- 2. forum_posts (never captured in a migration, and app.html only ever reads
--    it -- no insert path exists anywhere in the client, so there is no real
--    reply feature behind its stored reply_count) gets folded into the new
--    communities/posts system rather than kept as a second discussion surface.
--    Each distinct domain_group actually present in forum_posts becomes one
--    bridge "topic" community; each forum_posts row becomes a posts row with
--    community_id set, title/pinned preserved. Guarded with to_regclass so
--    this is a no-op if forum_posts doesn't exist in this database at all.

begin;

-- ---- 1. bucket_id FK + backfill -----------------------------------------

alter table public.users add column if not exists bucket_id uuid references public.buckets(id);

-- The live BUCKETS list has an 'Other' option the seeded buckets table never
-- got (it only has the 12 named sectors) -- add it so the backfill below has
-- somewhere to point members who picked 'Other' at signup.
insert into public.buckets (slug, name, sort_order)
values ('other', 'Other', 13)
on conflict (slug) do nothing;

update public.users u
set bucket_id = b.id
from public.buckets b
where u.bucket_id is null and u.domain_group = b.name;

-- posts.bucket_id (added in the previous migration) should back up the same
-- way for any post authored with the audience selector left on its default.
-- Nothing to backfill yet since posts is brand new in this same lineage.

-- ---- 2. fold forum_posts into communities/posts, if it exists -----------

do $$
declare
  rec record;
  v_community_id uuid;
  v_bucket_id uuid;
begin
  if to_regclass('public.forum_posts') is null then
    raise notice 'forum_posts does not exist in this database -- nothing to migrate.';
    return;
  end if;

  alter table public.posts add column if not exists community_id uuid references public.communities(id);
  alter table public.posts add column if not exists title text;
  alter table public.posts add column if not exists pinned boolean not null default false;

  for rec in
    select distinct domain_group from public.forum_posts where domain_group is not null
  loop
    select id into v_bucket_id from public.buckets where name = rec.domain_group;

    select id into v_community_id from public.communities
      where kind = 'topic' and name = rec.domain_group || ' — General Discussion';

    if v_community_id is null then
      insert into public.communities (name, kind, bucket_id, requires_verification)
      values (rec.domain_group || ' — General Discussion', 'topic', v_bucket_id, false)
      returning id into v_community_id;
    end if;

    insert into public.posts (author_id, body, title, bucket_id, audience, pinned, created_at, community_id)
    select fp.author_id, fp.content, fp.title, v_bucket_id, 'sector', coalesce(fp.pinned, false), fp.created_at, v_community_id
    from public.forum_posts fp
    where fp.domain_group = rec.domain_group;
  end loop;

  raise notice 'forum_posts migrated into communities/posts. The old forum_posts table was left in place -- drop it in a later migration once app.html no longer reads it.';
end $$;

commit;
