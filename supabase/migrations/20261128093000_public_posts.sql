-- Public visibility layer, phase 1: a member can opt a specific post into
-- being viewable by anyone, logged in or not -- the structural gap behind
-- "nothing here is shareable or Google-indexable the way a public tweet or
-- public LinkedIn post is." This is strictly additive and opt-in per post;
-- every existing post defaults to NOT public, so nothing already posted
-- becomes visible to anyone who couldn't already see it.
alter table public.posts add column if not exists public_visible boolean not null default false;

-- A member may only make their OWN post public, and only if its audience
-- is already 'everyone' -- a post deliberately scoped to 'connections' or
-- 'sector' can never be flipped public through this path, so the two
-- visibility systems (internal audience vs. public-to-the-world) can't be
-- used to accidentally escape the narrower one.
create or replace function public.validate_public_visible()
returns trigger
language plpgsql
as $function$
begin
  if new.public_visible and coalesce(new.audience,'everyone') <> 'everyone' then
    raise exception 'Only a post already visible to everyone in the register can be made public.';
  end if;
  return new;
end;
$function$;

drop trigger if exists trg_validate_public_visible on public.posts;
create trigger trg_validate_public_visible before insert or update on public.posts
  for each row execute function public.validate_public_visible();

-- Deliberately exposed to anon -- this is the one intentional public-read
-- surface in the whole schema. Only ever the minimum needed to render a
-- real, shareable page: no email/phone/city, no connections, no internal
-- member fields. Real name only shows under the exact same
-- show_real_name + real_name_approved gate used everywhere else in the
-- app; otherwise it falls back to the username, same as dname() client-side.
create view public.posts_public as
select
  p.id, p.title, p.body, p.image_url, p.image_urls, p.created_at,
  p.author_id,
  u.username as author_username,
  case when u.show_real_name and u.real_name_approved then u.real_name else null end as author_display_name
from public.posts p
join public.users u on u.id = p.author_id
where p.public_visible = true and p.community_id is null;

grant select on public.posts_public to anon, authenticated;
