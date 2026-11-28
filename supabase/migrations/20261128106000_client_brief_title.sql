-- Admin triage on client_briefs today only has domain_needed (a short taxonomy
-- label) and a truncated description to scan a queue by -- there's no short,
-- human-written headline, so every row reads the same at a glance ("Finance",
-- "Finance", "Legal"...). A short problem title ("Customs clearance bottleneck
-- at Mumbai port") makes the triage queue actually scannable.
alter table public.client_briefs add column if not exists title text;
