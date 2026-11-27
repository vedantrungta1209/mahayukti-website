-- Edit own post. DELETE already existed (posts_delete_own_or_admin) but was
-- never wired into the UI; UPDATE never existed at all. Mirrors the same
-- own-row-or-admin shape as the delete policy. Only body/title/image_url/
-- link_url/link_title are meant to be editable client-side (audience and
-- community_id shouldn't silently change after the fact) -- enforced in the
-- client call, not here, same pattern as every other self-update in this
-- schema (e.g. users' enforce_self_update_restrictions clamps server-side,
-- but simpler fields here don't need a trigger since nothing security-
-- sensitive lives on this row).
-- with_check also blocks a non-admin from flipping is_sponsored:true on their
-- own UPDATE -- posts_insert_own already blocks self-sponsoring at creation
-- time, and without this an UPDATE would be a silent bypass of that exact
-- restriction.
create policy posts_update_own_or_admin on public.posts
  for update
  using (author_id in (select id from public.users where auth_id = auth.uid()) or is_platform_admin())
  with check (
    (author_id in (select id from public.users where auth_id = auth.uid()) and not coalesce(is_sponsored, false))
    or is_platform_admin()
  );
