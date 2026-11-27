-- api_keys (hashed storage, scopes, revocation) already existed -- what
-- was missing was anything actually serving requests against them. This
-- adds the one new piece of state the API itself needs: a per-key,
-- per-minute request counter so a key can be rate-limited.
create table public.api_key_usage (
  key_id uuid not null references public.api_keys(id) on delete cascade,
  window_start timestamptz not null,
  request_count int not null default 0,
  primary key (key_id, window_start)
);

alter table public.api_key_usage enable row level security;

-- No client-facing policy at all -- this table is only ever touched by
-- api-v1's own service-role client, same as the payment/push tables
-- already following this pattern this session. RLS is enabled with no
-- policies, so even a stray anon/authenticated query sees nothing.
