-- Build spec's Brief Detail screen (§3, canvas BriefDetail.dc.html) shows a real response
-- list on the brief itself, with a "keep my response private to the poster" opt-out --
-- i.e. the wireframe's implied default is PUBLIC, opt into private. Today's actual RLS
-- (exchange_brief_responses_select_participant, from 20261120170000) only ever lets the
-- responder and the brief's author see a response -- every response sent so far was sent
-- under that implicit privacy, with no opt-out ever offered. Defaulting new rows to public
-- would retroactively expose private messages nobody agreed to share, so this migration
-- inverts the wireframe's default: private_to_poster defaults true (existing rows keep
-- today's effective privacy unchanged), and the new UI's checkbox is "share this response
-- publicly" (unchecked = private), not "keep private" (unchecked = public).

alter table public.exchange_brief_responses
  add column if not exists private_to_poster boolean not null default true;

drop policy if exists exchange_brief_responses_select_participant on public.exchange_brief_responses;

create policy exchange_brief_responses_select_participant on public.exchange_brief_responses for select using (
  responder_id in (select id from public.users where auth_id = auth.uid())
  or exists (select 1 from public.exchange_briefs b where b.id = exchange_brief_responses.brief_id
             and b.author_id in (select id from public.users where auth_id = auth.uid()))
  or public.is_platform_admin()
  or (
    not private_to_poster
    and exists (select 1 from public.users u where u.auth_id = auth.uid() and u.status = 'active')
  )
);
