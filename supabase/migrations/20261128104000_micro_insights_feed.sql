-- "Flash Intelligence" -- a short-form, sector-tagged insights feed, deliberately
-- separate from the general social `posts` feed built in Phase 1. Where the social
-- feed carries images, links, and longer updates, this is a strict, noise-free
-- channel for rapid professional analysis (e.g. a sudden SEBI/RBI policy shift) --
-- the "open MahaYukti daily even when not transacting" hook. Kept as its own table
-- and screen rather than another `posts.audience` mode, since the content-shape
-- rules below (hard length cap, no links/media at all) are a different contract
-- than the general feed's and don't belong mixed into its audience/mute/block logic.

create table public.member_insights (
  id            uuid primary key default gen_random_uuid(),
  author_id     uuid not null references public.users(id) on delete cascade,
  content       varchar(500) not null,
  sector_tag_id uuid references public.sector_tags(id) on delete set null,
  created_at    timestamptz not null default now(),
  constraint member_insights_content_not_blank check (length(trim(content)) > 0),
  -- The content-shape "moat": no external links or bare domains, enforced as a
  -- table CHECK (not just an RLS insert policy) so it can't be bypassed by any
  -- insert path, including a future admin/service import.
  constraint member_insights_no_links check (content !~* '(https?://|www\.[a-z0-9-]+\.[a-z]{2,})')
);

create index member_insights_sector_idx on public.member_insights(sector_tag_id);
create index member_insights_created_idx on public.member_insights(created_at desc);

alter table public.member_insights enable row level security;

-- Read access: any active member (this is a members-only "register" perk, not a
-- public feed like posts_public -- clients/unauthenticated visitors never see it).
create policy member_insights_select_active on public.member_insights
  for select to authenticated
  using (exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active'));

-- Write access: strictly gated to verified, active members posting as themselves.
create policy member_insights_insert_own_active on public.member_insights
  for insert to authenticated
  with check (
    author_id = (select id from public.users where auth_id = auth.uid())
    and exists (select 1 from public.users u where u.id = author_id and u.status = 'active')
  );

-- Author can retract their own insight; admin can remove any as a moderation action
-- (same authority as elsewhere -- no separate report/escalation plumbing for this
-- lightweight format; an abusive insight is removed the same way an abusive post is).
create policy member_insights_delete_own_or_admin on public.member_insights
  for delete to authenticated
  using (
    author_id = (select id from public.users where auth_id = auth.uid())
    or public.is_platform_admin()
  );
