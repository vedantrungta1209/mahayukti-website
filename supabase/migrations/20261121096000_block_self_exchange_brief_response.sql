-- Same class of gap as 20261121093000 (marketplace self-inquiry): loadExchange()'s
-- "Respond" button rendered unconditionally, including on the viewer's own brief, and
-- exchange_brief_responses_insert_own's RLS only ever checked responder_id = the
-- querying user, never that the brief's real author_id differs. Checks against the raw
-- exchange_briefs table (not exchange_briefs_public), since the public view correctly
-- nulls out author_id for OTHER people's anonymous briefs but preserves it for the real
-- author's own anonymous brief -- the raw table is what actually determines ownership
-- regardless of the anonymous flag either way.
--
-- Client-side fix: the button is now hidden when author_id (read through the public
-- view, which, as above, still reveals it correctly to the real author) matches the
-- viewer's own id. This migration closes it at the database level too.

drop policy if exists exchange_brief_responses_insert_own on public.exchange_brief_responses;

create policy exchange_brief_responses_insert_own on public.exchange_brief_responses
for insert
with check (
  responder_id in (select users.id from public.users where users.auth_id = auth.uid())
  and not exists (
    select 1 from public.exchange_briefs b
    where b.id = exchange_brief_responses.brief_id
      and b.author_id = exchange_brief_responses.responder_id
  )
);
