-- Same class of bug just fixed on users, found by applying the same check
-- to every table built this session with a "status" column and a self-
-- update policy: seller_subs_update_own_or_admin (20261120210000) had no
-- column restriction at all. A member could self-PATCH their OWN
-- seller_package_subscriptions row to status='active', push expires_at
-- years out, or zero/negative listings_used -- completely bypassing the
-- payment gate that entire feature exists to enforce, via one API call,
-- with no payment ever actually confirmed.
--
-- listings_used is the one field a member legitimately self-updates
-- (submitListing's own self-PATCH after a successful listing insert) --
-- clamped to only ever move forward by exactly 1 per update, matching that
-- call's own pattern, so it can't be abused to go backward/negative either.

begin;

create or replace function public.enforce_self_update_seller_subs()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.role() = 'authenticated'
     and old.user_id in (select id from public.users where auth_id = auth.uid())
     and not public.is_platform_admin() then
    new.status := old.status;
    new.package_id := old.package_id;
    new.activated_at := old.activated_at;
    new.expires_at := old.expires_at;
    if new.listings_used is distinct from old.listings_used + 1 then
      new.listings_used := old.listings_used;
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_enforce_self_update_seller_subs on public.seller_package_subscriptions;
create trigger trg_enforce_self_update_seller_subs
  before update on public.seller_package_subscriptions
  for each row
  execute function public.enforce_self_update_seller_subs();

-- member_connections_update_addressee (20261120150000) let the addressee
-- change ANY column on their row, not just status/responded_at --
-- including requester_id/addressee_id themselves. The addressee could
-- rewrite requester_id to a third member's id and set status='accepted',
-- fabricating a "so-and-so connected with me" relationship that third
-- member never actually requested or consented to -- a social-graph
-- integrity issue, not just a cosmetic one (Connect/Follow counts and the
-- relevance feed's proximity scoring both read this table as ground truth).
create or replace function public.enforce_addressee_update_scope()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.role() = 'authenticated'
     and old.addressee_id in (select id from public.users where auth_id = auth.uid())
     and not public.is_platform_admin() then
    new.requester_id := old.requester_id;
    new.addressee_id := old.addressee_id;
    new.created_at := old.created_at;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_enforce_addressee_update_scope on public.member_connections;
create trigger trg_enforce_addressee_update_scope
  before update on public.member_connections
  for each row
  execute function public.enforce_addressee_update_scope();

-- api_keys_update_own (20261120180000) let a member change ANY column on
-- their own key, including scopes and key_hash -- so a key created with
-- scopes=['post','read_profile'] could self-escalate to add
-- 'send_messages' (or any other scope) after the fact, or have its hash
-- swapped. revoked_at and label are the only legitimate self-update
-- targets (revokeApiKey only ever touches revoked_at).
create or replace function public.enforce_self_update_api_keys()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.role() = 'authenticated'
     and old.user_id in (select id from public.users where auth_id = auth.uid())
     and not public.is_platform_admin() then
    new.key_hash := old.key_hash;
    new.scopes := old.scopes;
    new.user_id := old.user_id;
    new.created_at := old.created_at;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_enforce_self_update_api_keys on public.api_keys;
create trigger trg_enforce_self_update_api_keys
  before update on public.api_keys
  for each row
  execute function public.enforce_self_update_api_keys();

-- The most serious of this batch: community_members_insert_own
-- (20261120150000) only checked that the inserted row's user_id matched
-- the caller -- nothing stopped anyone from directly INSERTing their own
-- row with status='active' for an institution-verified community, fully
-- bypassing the pending-approval queue the admin "Create an institution-
-- verified community" / approve-or-deny UI exists specifically to enforce.
-- Combined with posts_insert_own's community membership check (which only
-- looks for an 'active' row, exactly what this let you fake for free),
-- this meant the entire institution-verification premise -- "this is
-- really IIT Delhi Alumni, really verified" -- had no actual backing.
-- A self-inserted row into a verified community may now only ever be
-- 'pending'; only an admin update (the real approve flow) can set 'active'.
drop policy if exists community_members_insert_own on public.community_members;
create policy community_members_insert_own on public.community_members for insert with check (
  user_id in (select id from public.users where auth_id = auth.uid())
  and (
    public.is_platform_admin()
    or not exists (select 1 from public.communities c where c.id = community_members.community_id and c.requires_verification)
    or community_members.status = 'pending'
  )
);

-- posts_insert_own (20261120150000, already revised once this session for
-- the community_id bypass) had a second, worse gap: no restriction on
-- is_sponsored or sponsor_user_id at all. Any member could self-INSERT a
-- post with is_sponsored=true -- fully skipping the Advertise -> admin
-- review flow that "every ad is reviewed before it goes live" (the actual
-- copy shown in the Advertise screen) depends on -- and could even set
-- sponsor_user_id to a DIFFERENT member's id, falsely crediting someone
-- else as the advertiser.
--
-- Fixing this surfaced a second, separate bug: approveAd() in app.html
-- creates the real post as the ADMIN's own authenticated session, but with
-- author_id set to the ADVERTISER (so it displays correctly under their
-- name), not the admin. Under the original policy's single
-- "author_id must equal the caller" check, that insert would itself have
-- been rejected by RLS -- the approval flow was never actually going to
-- work once applied, caught here before it was ever run against a real
-- database.
drop policy if exists posts_insert_own on public.posts;
create policy posts_insert_own on public.posts for insert with check (
  (
    author_id in (select id from public.users where auth_id = auth.uid())
    and not coalesce(is_sponsored, false)
    and (
      community_id is null
      or exists (
        select 1 from public.community_members cm
        where cm.community_id = posts.community_id
          and cm.user_id = posts.author_id
          and cm.status = 'active'
      )
    )
  )
  or (
    -- The real ad-approval path: an admin creates the post on the
    -- advertiser's behalf once a campaign is approved. is_sponsored must
    -- be true here -- an admin can't use this branch to post as someone
    -- else for free.
    public.is_platform_admin() and coalesce(is_sponsored, false)
  )
);

-- ad_campaigns_insert_own (20261120180000) had the same shape of gap, now
-- low-impact rather than exploitable since the posts fix above means
-- self-setting status='active' here no longer creates any real post --
-- but fixing it anyway keeps the admin queue's own labels (PENDING REVIEW
-- vs LIVE) honest rather than self-reported.
drop policy if exists ad_campaigns_insert_own on public.ad_campaigns;
create policy ad_campaigns_insert_own on public.ad_campaigns for insert with check (
  advertiser_id in (select id from public.users where auth_id = auth.uid())
  and status = 'pending_review'
);

commit;
