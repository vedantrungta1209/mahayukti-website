-- Soft rate-limit on cold DM outreach -- chosen over the earlier "Brief-Anchored"
-- gate (parked, see memory) specifically because it preserves today's live open
-- Directory/connections messaging untouched: a member can still message anyone
-- whose privacy setting allows it, this only throttles how many BRAND NEW
-- unconnected people they can cold-message per week, as an anti-scraping /
-- anti-poaching-spam measure once the taxonomy build makes this register a
-- genuinely valuable map of specialised talent.
--
-- Deliberately counts DISTINCT NEW cold conversations started, not total
-- messages sent -- an ongoing back-and-forth with someone you've already
-- messaged (even if you're still not formally "connected") is never metered
-- message-by-message; only the first contact with a brand-new unconnected
-- recipient consumes a token. can_message() (20261121095000) already governs
-- whether a message is ALLOWED at all (block/privacy/connection check); this
-- is an additional throttle layered on top, enforced as a BEFORE INSERT
-- trigger (not folded into the RLS policy) so the counter increment is a
-- single, reliable side effect per row rather than living inside a
-- potentially-re-evaluated RLS predicate.

create table public.member_rate_limits (
  member_id                   uuid primary key references public.users(id) on delete cascade,
  cold_messages_sent_this_week int not null default 0,
  last_reset_at                timestamptz not null default now()
);

alter table public.member_rate_limits enable row level security;

-- Read-only for the member themselves (lets a future "N tokens left this
-- week" UI read their own row) and admins; nothing else needs direct access
-- since only the trigger below (SECURITY DEFINER) ever writes to it.
create policy member_rate_limits_select_own_or_admin on public.member_rate_limits
  for select to authenticated
  using (
    member_id = (select id from public.users where auth_id = auth.uid())
    or public.is_platform_admin()
  );

create or replace function public.enforce_cold_outreach_rate_limit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_cap constant int := 5; -- day-one soft cap: 5 new unconnected conversations / rolling week
  v_connected boolean;
  v_prior_thread boolean;
  v_row public.member_rate_limits%rowtype;
begin
  -- Admin accounts (platform support/official outreach) are exempt from the cap.
  if exists (select 1 from public.users where id = new.from_id and role = 'admin') then
    return new;
  end if;

  select exists(
    select 1 from public.member_connections mc
    where mc.status = 'accepted'
      and ((mc.requester_id = new.from_id and mc.addressee_id = new.to_id)
        or (mc.requester_id = new.to_id and mc.addressee_id = new.from_id))
  ) into v_connected;

  select exists(
    select 1 from public.messages m
    where (m.from_id = new.from_id and m.to_id = new.to_id)
       or (m.from_id = new.to_id and m.to_id = new.from_id)
  ) into v_prior_thread;

  -- Already connected, or any prior message either direction between this
  -- exact pair -- not a new cold outreach, no token consumed.
  if v_connected or v_prior_thread then
    return new;
  end if;

  insert into public.member_rate_limits (member_id)
  values (new.from_id)
  on conflict (member_id) do nothing;

  select * into v_row from public.member_rate_limits where member_id = new.from_id for update;

  if now() - v_row.last_reset_at >= interval '7 days' then
    update public.member_rate_limits
      set cold_messages_sent_this_week = 0, last_reset_at = now()
      where member_id = new.from_id;
    v_row.cold_messages_sent_this_week := 0;
  end if;

  if v_row.cold_messages_sent_this_week >= v_cap then
    raise exception 'cold_outreach_cap_reached';
  end if;

  update public.member_rate_limits
    set cold_messages_sent_this_week = cold_messages_sent_this_week + 1
    where member_id = new.from_id;

  return new;
end;
$$;

drop trigger if exists trg_enforce_cold_outreach_rate_limit on public.messages;
create trigger trg_enforce_cold_outreach_rate_limit
  before insert on public.messages
  for each row
  execute function public.enforce_cold_outreach_rate_limit();
