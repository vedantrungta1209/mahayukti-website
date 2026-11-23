-- app.html's own extractHashtags() only ever derives a tag from
-- /#([a-zA-Z][a-zA-Z0-9_]{1,49})/ matches in a post body, lowercased before
-- insert -- but that's a client-side rule only. The hashtags table itself had
-- no constraint beyond uniqueness, so any authenticated member calling the
-- PostgREST endpoint directly (trivial with devtools/curl + their own JWT)
-- could insert an arbitrary string as a tag. That string is rendered via
-- innerHTML in the trending-hashtags widget on every member's Home screen
-- and in the hashtag detail header -- those call sites are now escaped with
-- esc(), but a format constraint at the source closes the same hole for any
-- future render path that forgets to.
alter table public.hashtags
  add constraint hashtags_tag_format check (tag ~ '^[a-z][a-z0-9_]{1,49}$');
