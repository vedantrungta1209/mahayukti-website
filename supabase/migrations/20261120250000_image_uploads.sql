-- posts.image_url and marketplace_listings.photo_urls have existed since
-- this session's own first migration, but nothing anywhere ever uploaded a
-- file into them -- no <input type="file">, no storage bucket, no call to
-- Supabase Storage at all. "Pictures and videos" was explicitly part of
-- the original ask; images are the real, buildable half of that (video
-- needs real transcoding/size infrastructure this app doesn't have yet,
-- so this deliberately stays scoped to images, not a half-built video
-- feature). A Storage bucket needs creating either way before any upload
-- UI is worth writing.

begin;

insert into storage.buckets (id, name, public)
values ('uploads', 'uploads', true)
on conflict (id) do nothing;

-- Path convention the app writes to: uploads/<auth_uid>/<timestamp>-<name>.
-- Anyone can READ (the bucket is public -- images need to render for every
-- viewer, verified member or not, same as any other public image URL
-- would), but a member may only WRITE into their own folder, keyed off the
-- first path segment matching their own auth.uid().
drop policy if exists uploads_public_read on storage.objects;
create policy uploads_public_read on storage.objects for select using (
  bucket_id = 'uploads'
);

drop policy if exists uploads_insert_own_folder on storage.objects;
create policy uploads_insert_own_folder on storage.objects for insert with check (
  bucket_id = 'uploads'
  and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists uploads_delete_own_folder on storage.objects;
create policy uploads_delete_own_folder on storage.objects for delete using (
  bucket_id = 'uploads'
  and (storage.foldername(name))[1] = auth.uid()::text
);

commit;
