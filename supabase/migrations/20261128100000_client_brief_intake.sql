-- client_briefs (20261120200000) already had the admin-side triage screen
-- (Pending/Reviewing/Assigned/Done) fully built, but its own migration
-- comment said plainly: "No insert path exists anywhere in this repo...
-- these rows get created by whatever external intake process feeds the
-- admin queue today... not by anything here." There was no real public
-- intake -- this is that intake, plus the contact columns it needs that
-- the original schema never had (an admin can "Assign" a brief but had no
-- way to ever reach the actual client).
alter table public.client_briefs add column if not exists contact_name text;
alter table public.client_briefs add column if not exists contact_email text;
alter table public.client_briefs add column if not exists contact_phone text;
alter table public.client_briefs add column if not exists company text;

-- RLS is unchanged (admin-only for both read and write, from the original
-- migration) -- the public intake Edge Function inserts via the service
-- role key, same pattern this app already uses for linkedin_connections and
-- the razorpay webhook, never via a client-facing insert policy. A public
-- INSERT policy here would let anyone read back what they just inserted
-- only if PostgREST returned the row, which the function deliberately
-- doesn't ask for (POST with no Prefer: return=representation), but there
-- is still no reason to open RLS at all when the service role already
-- covers the one legitimate writer.
