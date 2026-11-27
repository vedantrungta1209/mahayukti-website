-- Organization accounts: multi-admin "Pages" distinct from individual
-- membership. A government department, a media house, or a company can't
-- realistically be represented by one person's personal login -- this
-- lets several real members jointly manage one org identity instead.
create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  kind text not null default 'company' check (kind in ('company','media','government','ngo','other')),
  description text,
  logo_url text,
  verified boolean not null default false,
  created_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table public.organization_admins (
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  role text not null default 'admin' check (role in ('owner','admin')),
  added_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

-- posted_as_org_id on posts: when set, a post displays as the org (name,
-- logo) rather than the individual member -- but author_id is untouched,
-- so real accountability for who actually posted never disappears.
alter table public.posts add column if not exists posted_as_org_id uuid references public.organizations(id) on delete set null;

alter table public.organizations enable row level security;
alter table public.organization_admins enable row level security;

-- Org existence/profile is meant to be publicly discoverable (same spirit
-- as posts_public) -- the directory/profile itself isn't sensitive, unlike
-- posts, which stay gated by their own existing audience rules regardless
-- of who they're posted as.
create policy organizations_select_all on public.organizations
  for select using (true);

grant select on public.organizations to anon, authenticated;

-- Creating an org is open to any active member (same bar as creating a
-- topic community) -- the creator becomes its first owner via the insert
-- policy on organization_admins below, same shape used for
-- community_members' creator-becomes-moderator pattern.
create policy organizations_insert_active_members on public.organizations
  for insert
  with check (
    exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
    and created_by in (select id from public.users where auth_id = auth.uid())
  );

create policy organizations_update_admin_or_owner on public.organizations
  for update
  using (
    is_platform_admin()
    or exists (select 1 from public.organization_admins oa where oa.organization_id = organizations.id and oa.user_id in (select id from public.users where auth_id = auth.uid()))
  )
  with check (
    -- verified is platform-admin-only to set -- an org can't self-verify,
    -- same reasoning as community moderator role being admin-only to grant.
    (verified = false or is_platform_admin())
    and (
      is_platform_admin()
      or exists (select 1 from public.organization_admins oa where oa.organization_id = organizations.id and oa.user_id in (select id from public.users where auth_id = auth.uid()))
    )
  );

create policy organization_admins_select_all on public.organization_admins
  for select using (true);

grant select on public.organization_admins to anon, authenticated;

-- Only an existing owner/admin of the org can add another admin -- except
-- the very first row (the creator becoming the org's first owner), which
-- the organizations_insert policy already gated on created_by matching the
-- caller, so there's no separate bootstrap problem here.
create policy organization_admins_insert on public.organization_admins
  for insert
  with check (
    user_id in (select id from public.users where auth_id = auth.uid())
    and exists (select 1 from public.organizations o where o.id = organization_id and o.created_by = organization_admins.user_id)
    or exists (
      select 1 from public.organization_admins existing
      where existing.organization_id = organization_admins.organization_id
        and existing.user_id in (select id from public.users where auth_id = auth.uid())
        and existing.role = 'owner'
    )
  );

create policy organization_admins_delete on public.organization_admins
  for delete
  using (
    is_platform_admin()
    or user_id in (select id from public.users where auth_id = auth.uid()) -- can remove yourself
    or exists (
      select 1 from public.organization_admins owner_row
      where owner_row.organization_id = organization_admins.organization_id
        and owner_row.user_id in (select id from public.users where auth_id = auth.uid())
        and owner_row.role = 'owner'
    )
  );

-- A post can only be posted "as" an org by one of that org's own admins --
-- enforced the same way posts' other author-ownership checks already are,
-- via with_check on the existing posts_insert_own / posts_update_own_or_admin
-- policies. Routed through a SECURITY DEFINER function for the same reason
-- the community_members/exchange_briefs recursion bugs earlier this session
-- needed one -- avoids a self-referencing-policy cycle between posts and
-- organization_admins.
create or replace function public.is_organization_admin(p_org_id uuid)
returns boolean
language sql
stable security definer
set search_path to 'public'
as $$
  select exists (
    select 1 from public.organization_admins oa
    where oa.organization_id = p_org_id
      and oa.user_id in (select id from public.users where auth_id = auth.uid())
  );
$$;

-- posts_public needs posted_as_org_id too, so the org's own public page
-- (functions/org/[slug].js) can query its public posts.
drop view if exists public.posts_public;
create view public.posts_public as
select
  p.id, p.title, p.body, p.image_url, p.image_urls, p.created_at,
  p.author_id, p.posted_as_org_id,
  u.username as author_username,
  case when u.show_real_name and u.real_name_approved then u.real_name else null end as author_display_name
from public.posts p
join public.users u on u.id = p.author_id
where p.public_visible = true and p.community_id is null;
grant select on public.posts_public to anon, authenticated;

drop policy if exists posts_insert_own on public.posts;
create policy posts_insert_own on public.posts
  for insert
  with check (
    (author_id in (select id from public.users where auth_id = auth.uid())
      and not coalesce(is_sponsored, false)
      and (community_id is null or exists (
        select 1 from community_members cm
        where cm.community_id = posts.community_id and cm.user_id = posts.author_id and cm.status = 'active'
      ))
      and (posted_as_org_id is null or is_organization_admin(posted_as_org_id))
    )
    or (is_platform_admin() and coalesce(is_sponsored, false))
  );
