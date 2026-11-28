-- Replaces 20261128101000's automatic single-"No"-suspends trigger
-- entirely, per explicit direction after walking through the failure
-- mode: a rating can only come from a real is_brief_counterparty()
-- relationship, but two or more people motivated to target someone (a
-- public or polarizing member, for instance) could still manufacture
-- trivial real brief engagements purely to collect "No"s with zero actual
-- delivery failure involved -- and the more prominent someone is, the
-- MORE exposed they'd be to exactly that, which is backwards for a
-- consequence meant to track real non-delivery. No status change should
-- ever fire without a human actually looking at the case.
--
-- New model: everything becomes a report. member_reports generalizes
-- reporting to the ACCOUNT level (any member can report any other member,
-- for any reason, same shape as the existing post_reports system but
-- aimed at a person instead of a post) -- not gated behind having had a
-- real Exchange engagement with them, unlike brief_outcomes. A brief
-- "No" rating still exists and is still a real, useful signal, but it no
-- longer mutates users.status by itself -- it's just one more fact an
-- admin sees in the same review surface as member_reports. Suspend and
-- permanently-ban are now ALWAYS a deliberate, manual admin action, never
-- an automatic threshold.

-- The single-"No" auto-suspend trigger from 20261128101000 is fully removed.
drop trigger if exists trg_brief_outcome_consequence on public.brief_outcomes;
drop function if exists public.apply_brief_outcome_consequence();

create table public.member_reports (
  id          uuid primary key default gen_random_uuid(),
  reporter_id uuid not null references public.users(id) on delete cascade,
  reported_id uuid not null references public.users(id) on delete cascade,
  reason      text not null,
  note        text,
  status      text not null default 'open' check (status in ('open', 'reviewed')),
  created_at  timestamptz not null default now(),
  constraint member_reports_no_self_report check (reporter_id <> reported_id)
);

create index member_reports_reported_idx on public.member_reports(reported_id);
create index member_reports_status_idx on public.member_reports(status);

alter table public.member_reports enable row level security;

-- Visible to the reporter (their own filed reports), the reported member's
-- own admin-facing context is intentionally NOT exposed to them (same
-- reasoning as post_reports -- a reported party doesn't get to see who
-- reported them or read the raw reasons), and admins.
create policy member_reports_select_own_or_admin on public.member_reports
  for select to authenticated
  using (
    reporter_id = (select id from public.users where auth_id = auth.uid())
    or public.is_platform_admin()
  );

create policy member_reports_insert_own on public.member_reports
  for insert to authenticated
  with check (
    reporter_id = (select id from public.users where auth_id = auth.uid())
    and exists (select 1 from public.users u where u.id = reported_id and u.status = 'active')
  );

create policy member_reports_update_admin on public.member_reports
  for update to authenticated
  using (public.is_platform_admin())
  with check (public.is_platform_admin());

-- Per-account admin toggle for high-profile/sensitive accounts: reports
-- can still be filed against a shielded account (never silently blocked --
-- that would look like favoritism if it ever came out), but the account is
-- excluded from the review queue's "needs attention" volume-based sorting,
-- so a pile of reports alone never creates escalating pressure toward
-- action on its own. An admin still has to go looking and judge it the
-- same deliberate way as anything else.
alter table public.users add column if not exists shielded_from_report_escalation boolean not null default false;

-- One admin-facing surface combining both signals (general account reports
-- + brief "not delivered" ratings) per member -- the manual review model
-- only works if an admin can see everything about an account in one place
-- rather than two separate disconnected lists. security_invoker defaults
-- to false (runs as the view owner), so the explicit is_platform_admin()
-- guard in the WHERE clause is load-bearing, not decorative -- without it
-- a non-admin querying this view would see every other member's report
-- history, since the view would otherwise bypass member_reports' own RLS.
create view public.admin_flagged_members
with (security_invoker = false)
as
select
  u.id as user_id,
  u.real_name,
  u.username,
  u.email,
  u.status,
  u.shielded_from_report_escalation,
  coalesce(mr.open_reports, 0) as open_reports,
  coalesce(bo.no_count, 0) as brief_no_count
from public.users u
left join (
  select reported_id, count(*) as open_reports
  from public.member_reports
  where status = 'open'
  group by reported_id
) mr on mr.reported_id = u.id
left join (
  select ratee_id, count(*) as no_count
  from public.brief_outcomes
  where deliverable_met = false
  group by ratee_id
) bo on bo.ratee_id = u.id
where public.is_platform_admin()
  and (coalesce(mr.open_reports, 0) > 0 or coalesce(bo.no_count, 0) > 0 or u.status in ('suspended', 'expelled'));

grant select on public.admin_flagged_members to authenticated;
