-- Automated content flagging, feeding into the SAME moderation queue admins
-- already use for member reports -- not a separate system, just another
-- source of rows in post_reports. This is a basic, maintainable
-- pattern-based first pass (obvious spam link floods, denylisted terms),
-- not a full ML moderation pipeline -- it exists to catch the clearest
-- cases automatically instead of waiting on a member to report them.
alter table public.post_reports add column if not exists source text not null default 'member' check (source in ('member','auto'));
alter table public.post_reports alter column reporter_id drop not null;

create or replace function public.auto_flag_post()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  link_count int;
  reason_text text;
  denylist text[] := array['viagra','crypto giveaway','click here to claim','guaranteed income','work from home \$\$\$'];
  term text;
begin
  -- Spam-link flood: three or more URLs in one post is overwhelmingly a
  -- spam pattern on a professional register, essentially never a real
  -- legitimate post.
  select count(*) into link_count from regexp_matches(coalesce(new.body,''), 'https?://', 'g');
  if link_count >= 3 then
    reason_text := 'Automated: ' || link_count || ' links in one post (possible spam)';
  else
    foreach term in array denylist loop
      if new.body ilike '%' || term || '%' then
        reason_text := 'Automated: matched denylisted phrase';
        exit;
      end if;
    end loop;
  end if;

  if reason_text is not null then
    insert into public.post_reports (post_id, reporter_id, reason, source)
    values (new.id, null, reason_text, 'auto');
  end if;
  return new;
end;
$function$;

create trigger trg_auto_flag_post after insert on public.posts
  for each row execute function public.auto_flag_post();
