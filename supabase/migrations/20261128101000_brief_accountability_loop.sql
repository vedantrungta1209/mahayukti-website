-- The "Zero-Cut Accountable Rating Loop" -- the third time this exact gap
-- has come up across the strategic-review documents this session: money
-- for an Exchange engagement moves entirely off-platform (by design, the
-- platform's own zero-cut positioning), so the app has zero visibility
-- into whether an engagement actually went well. There was also, until
-- now, no suspend/freeze mechanism for an ALREADY-ACTIVE member anywhere
-- in the schema (checked repeatedly this session -- status only ever
-- transitioned pending->active/rejected, or active->deactivated by the
-- member's own choice). This migration builds both halves: a real binary
-- outcome rating between the two real parties of an awarded Exchange
-- engagement, and a real consequence (immediate suspension, pending admin
-- review) when one party reports the other didn't deliver.
--
-- Deliberately NOT the external proposal's literal framing (an anonymous
-- "client" and an auto-matched "expert"): this app's real Exchange briefs
-- are between two real members (a brief author and the member whose
-- response they awarded), both with real accounts that can log in and
-- rate each other -- so the loop is built bidirectionally, not just
-- client-rates-expert. A bad-faith brief author who ghosts on an agreed
-- fee is exactly as real a risk as an expert who disappears.

alter table public.users add column if not exists suspension_reason text;

-- awarded_response_id was already on exchange_briefs and already rendered
-- in the UI as a "✓ AWARDED" badge -- but exchange_briefs_public (the only
-- view a non-author, including the actual awarded responder, can read)
-- never exposed it. That's a real pre-existing bug this surfaced: the
-- awarded responder could never see their own response had been awarded,
-- and (more importantly for this migration) had no way to know an
-- engagement existed to rate. Re-applying the exact anon-exposure logic
-- from the original view unchanged -- awarded_response_id isn't sensitive
-- the way author_id is, so it's added as a plain passthrough column.
create or replace view public.exchange_briefs_public
with (security_invoker = false)
as
select
  id,
  brief_type,
  description,
  bucket_id,
  anonymous,
  case
    when anonymous
      and author_id not in (select id from public.users where auth_id = auth.uid())
      and not is_platform_admin()
    then null
    else author_id
  end as author_id,
  status,
  created_at,
  awarded_response_id
from public.exchange_briefs;

grant select on public.exchange_briefs_public to authenticated;

-- Whether two users are genuinely the two parties of a real awarded
-- engagement -- SECURITY DEFINER, same reasoning as is_organization_admin:
-- avoids RLS recursion between brief_outcomes' own policy and the
-- exchange_briefs/exchange_brief_responses tables it has to check against.
create or replace function public.is_brief_counterparty(p_brief_id uuid, p_rater uuid, p_ratee uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists(
    select 1
    from public.exchange_briefs b
    join public.exchange_brief_responses r on r.id = b.awarded_response_id
    where b.id = p_brief_id
      and b.status in ('matched', 'closed')
      and p_rater <> p_ratee
      and (
        (b.author_id = p_rater and r.responder_id = p_ratee)
        or (b.author_id = p_ratee and r.responder_id = p_rater)
      )
  );
$$;

create table public.brief_outcomes (
  id              uuid primary key default gen_random_uuid(),
  brief_id        uuid not null references public.exchange_briefs(id) on delete cascade,
  rater_id        uuid not null references public.users(id) on delete cascade,
  ratee_id        uuid not null references public.users(id) on delete cascade,
  deliverable_met boolean not null,
  note            text,
  created_at      timestamptz not null default now(),
  unique (brief_id, rater_id),
  constraint brief_outcomes_no_self_rating check (rater_id <> ratee_id)
);

create index brief_outcomes_brief_idx on public.brief_outcomes(brief_id);
create index brief_outcomes_ratee_idx on public.brief_outcomes(ratee_id);

alter table public.brief_outcomes enable row level security;

-- Visible to either party or an admin -- not broadly public (unlike
-- vouches, this carries a negative-outcome risk and a free-text note that
-- could name specifics of a dispute).
create policy brief_outcomes_select_party_or_admin on public.brief_outcomes
  for select to authenticated
  using (
    rater_id = (select id from public.users where auth_id = auth.uid())
    or ratee_id = (select id from public.users where auth_id = auth.uid())
    or public.is_platform_admin()
  );

-- Only as yourself, only about the real counterparty of a real awarded
-- engagement that has actually reached matched/closed -- is_brief_counterparty
-- is the only thing standing between this and anyone rating anyone.
create policy brief_outcomes_insert_party on public.brief_outcomes
  for insert to authenticated
  with check (
    rater_id = (select id from public.users where auth_id = auth.uid())
    and public.is_brief_counterparty(brief_id, rater_id, ratee_id)
  );

-- No update/delete policy -- a rating is a one-time, honest signal at the
-- close of an engagement, not something to revise after the fact (same
-- reasoning as moderation reports being immutable once filed).

-- The real consequence: a verified "not delivered" rating immediately
-- suspends the ratee's account (locks them out, same gate as
-- pending/rejected/deactivated via renderPendingScreen), pending a real
-- admin's review -- not a silent queue entry with no teeth, and not a
-- permanent ban either (an admin can reinstate via the existing
-- users_update_admin_all policy, same PATCH pattern as every other admin
-- action in this app). Only fires if the ratee is currently active --
-- doesn't fight with or override pending/rejected/deactivated states.
create or replace function public.apply_brief_outcome_consequence()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if not new.deliverable_met then
    update public.users
      set status = 'suspended',
          suspension_reason = 'A counterparty reported that an Exchange engagement was not delivered as agreed. An admin is reviewing this and can reinstate the account.'
      where id = new.ratee_id
        and status = 'active';
  end if;
  return new;
end;
$$;

create trigger trg_brief_outcome_consequence
  after insert on public.brief_outcomes
  for each row
  execute function public.apply_brief_outcome_consequence();
