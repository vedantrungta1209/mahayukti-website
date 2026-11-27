-- Multi-image posts. Keeps the existing image_url column untouched for
-- every already-published post (nothing re-renders differently for them);
-- new posts with more than one image populate image_urls instead, and the
-- client treats image_urls as the richer source of truth, falling back to
-- image_url when it's empty -- same additive, never-breaks-old-rows pattern
-- as the avatar_url and edited_at columns added this session.
alter table public.posts add column if not exists image_urls text[];
