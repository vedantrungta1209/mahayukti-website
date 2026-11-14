-- Recreates the `users` table that the shipped app.html apply/login/admin flow
-- depends on. This table only ever existed in the old (now-unreachable) Supabase
-- project, created ad hoc via the dashboard -- never captured as a migration.
-- Columns are reverse-engineered directly from every `api('users', ...)` /
-- `/rest/v1/users` call in app.html (grep 'users' app.html), not invented.

create extension if not exists pgcrypto;

create table public.users (
  id uuid primary key default gen_random_uuid(),
  auth_id uuid references auth.users(id) on delete cascade,
  username text unique,
  real_name text,
  show_real_name boolean not null default true,
  real_name_approved boolean not null default false,
  email text,
  phone text,
  city text,
  state text,
  domain text,
  domain_group text,
  role text not null default 'member',
  founding_member boolean not null default false,
  founding_approved boolean not null default false,
  experience text,
  organisation text,
  show_organisation boolean not null default true,
  about text,
  qualification text,
  linkedin text,
  source text,
  submission_id text,
  status text not null default 'pending',
  admin_notes text,
  approved_at timestamptz,
  created_at timestamptz not null default now()
);

create unique index users_auth_id_key on public.users(auth_id);
create index users_status_idx on public.users(status);

-- Security-definer check, so an RLS policy can ask "is the CURRENT user an admin"
-- without recursively re-triggering RLS on `users` itself.
create or replace function public.is_platform_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.users u
    where u.auth_id = auth.uid() and u.role = 'admin' and u.status = 'active'
  );
$$;

alter table public.users enable row level security;

-- A freshly-signed-up member inserts exactly one row for themselves, right after signUp.
create policy users_insert_own
  on public.users for insert
  to authenticated
  with check (auth_id = auth.uid());

-- Everyone can read their own row (pending/active/rejected -- the pending-status screen needs this).
create policy users_select_own
  on public.users for select
  to authenticated
  using (auth_id = auth.uid());

-- The member directory lists other ACTIVE, non-admin members by design (app.html ST.members query).
create policy users_select_active_members
  on public.users for select
  to authenticated
  using (status = 'active');

-- Admins can read everything, including the pending-applications queue.
create policy users_select_admin_all
  on public.users for select
  to authenticated
  using (public.is_platform_admin());

-- A member can edit a small set of their own fields (the app only ever PATCHes `about` for self).
create policy users_update_own
  on public.users for update
  to authenticated
  using (auth_id = auth.uid())
  with check (auth_id = auth.uid());

-- Admins approve/reject by PATCHing status/role/admin_notes/approved_at on any row.
create policy users_update_admin_all
  on public.users for update
  to authenticated
  using (public.is_platform_admin())
  with check (true);
