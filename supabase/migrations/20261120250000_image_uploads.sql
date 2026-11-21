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

-- file_size_limit and allowed_mime_types weren't set originally, meaning
-- the bucket accepted a file of any type or size -- the client only
-- declares accept="image/*" on the <input>, which the browser doesn't
-- enforce as a hard rule and a direct Storage API call ignores entirely.
-- 8MB covers a real phone photo with room to spare without letting someone
-- run up storage costs with arbitrarily large uploads.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('uploads', 'uploads', true, 8388608, array['image/jpeg','image/png','image/webp','image/gif'])
on conflict (id) do update set
  file_size_limit = 8388608,
  allowed_mime_types = array['image/jpeg','image/png','image/webp','image/gif'];

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
