-- Multi-tier sector taxonomy (Level 1 -> Level 2 -> Level 3), additive and
-- parallel to the existing flat `buckets`/domain_group system used for
-- member profiles and Directory filtering. Deliberately NOT a replacement
-- or migration of that system -- every existing member's profile bucket
-- stays exactly as it is; this only adds real depth to brief-level and
-- client-intake-level tagging, where nothing existed for it to conflict
-- with. Content seeded for the two sectors actually worked out so far
-- (Cybersecurity & Infosec / Technology & AI, and the Finance-related
-- sub-areas, mapped onto the REAL existing L1 buckets they belong to
-- rather than inventing a new conflicting "Finance & Corporate Advisory"
-- top-level sector that doesn't exist anywhere else in this app). The
-- other existing sectors get an L1 row with no L2/L3 depth yet -- the
-- picker degrades gracefully to L1-only for those.
--
-- (The accountability loop's repeat-offense handling is NOT revised here
-- -- see 20261128103000_manual_moderation_review.sql instead, which
-- replaces automatic suspension entirely with manual admin review.)

create table public.sector_tags (
  id         uuid primary key default gen_random_uuid(),
  parent_id  uuid references public.sector_tags(id) on delete cascade,
  level      int not null check (level in (1, 2, 3)),
  name       text not null,
  slug       text not null unique,
  sort_order int not null default 0
);

create index sector_tags_parent_idx on public.sector_tags(parent_id);

alter table public.sector_tags enable row level security;

-- Pure taxonomy, not user data -- readable by anyone, signed in or not
-- (the brief picker needs it for members, and the public, unauthenticated
-- client-intake form on index.html needs the exact same tree), writable
-- only by an admin seeding/maintaining it.
create policy sector_tags_select_all on public.sector_tags
  for select to anon, authenticated using (true);

create policy sector_tags_admin_write on public.sector_tags
  for all to authenticated
  using (public.is_platform_admin())
  with check (public.is_platform_admin());

-- Seed: Level 1 -- the existing 12 buckets, minus "Technology &
-- Cybersecurity" split into two per the explicit instruction to separate
-- infosec from general technology/AI (mixing them wastes a true
-- specialist's time on mismatched briefs).
insert into public.sector_tags (level, name, slug, sort_order) values
  (1, 'Legal', 'legal', 1),
  (1, 'Accounting & Audit', 'accounting-audit', 2),
  (1, 'Cybersecurity & Infosec', 'cybersecurity-infosec', 3),
  (1, 'Technology & AI', 'technology-ai', 4),
  (1, 'Capital & Funding', 'capital-funding', 5),
  (1, 'Business & Industry', 'business-industry', 6),
  (1, 'Government & Public Affairs', 'government-public-affairs', 7),
  (1, 'Defence & Security', 'defence-security', 8),
  (1, 'Culture & Public Influence', 'culture-public-influence', 9),
  (1, 'Trades & Craft', 'trades-craft', 10),
  (1, 'Science & Deep-Tech', 'science-deep-tech', 11),
  (1, 'Healthcare & Medicine', 'healthcare-medicine', 12),
  (1, 'Real Estate & Infrastructure', 'real-estate-infrastructure', 13),
  (1, 'Other', 'other', 14);

-- Level 2/3 under Cybersecurity & Infosec.
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, 'Information Security & Incident Response', 'infosec-incident-response', 1
from public.sector_tags where slug = 'cybersecurity-infosec';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Ransomware Negotiation & Extortion Handling', 'ransomware-negotiation', 1),
  ('Post-Breach Digital Forensics', 'post-breach-forensics', 2),
  ('VAPT (Vulnerability Assessment & Penetration Testing) Compliance', 'vapt-compliance', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'infosec-incident-response';

-- Level 2/3 under Technology & AI.
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Software Architecture & Infrastructure', 'software-architecture-infra', 1),
  ('AI & Emerging Tech', 'ai-emerging-tech', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'technology-ai';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Failed Enterprise Migration Recovery (ERP/CRM)', 'failed-erp-migration-recovery', 1),
  ('Cloud Cost Optimization & FinOps', 'cloud-cost-finops', 2),
  ('High-Scale Database Architecture', 'high-scale-db-architecture', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'software-architecture-infra';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('LLM Fine-Tuning & Custom Model Deployment', 'llm-fine-tuning-deployment', 1),
  ('Computer Vision Integration', 'computer-vision-integration', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'ai-emerging-tech';

-- Level 2/3 under the real existing finance-adjacent buckets -- the
-- proposed draft's "Finance & Corporate Advisory" doesn't exist anywhere
-- else in this app's taxonomy, so its content is mapped onto the actual
-- L1 sectors it belongs to instead of inventing a conflicting 14th
-- top-level sector: M&A/fundraising under Capital & Funding, tax/GST under
-- Accounting & Audit, and distress/restructuring under Business & Industry
-- (genuinely cross-cutting, but fundamentally a business-operations
-- problem even where it touches legal/finance).
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, 'Corporate Finance & M&A', 'corporate-finance-ma', 1
from public.sector_tags where slug = 'capital-funding';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Cross-Border Transaction Structuring', 'cross-border-transaction-structuring', 1),
  ('Valuation Defensibility & Financial Due Diligence', 'valuation-due-diligence', 2),
  ('Fundraising Pitch & Term-Sheet Advisory', 'fundraising-term-sheet-advisory', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'corporate-finance-ma';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, 'Tax & Regulatory Compliance', 'tax-regulatory-compliance', 1
from public.sector_tags where slug = 'accounting-audit';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('GST Dispute Resolution & Appellate Representation', 'gst-dispute-resolution', 1),
  ('FEMA & Cross-Border Capital Compliance', 'fema-cross-border-compliance', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'tax-regulatory-compliance';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, 'Distress & Restructuring', 'distress-restructuring', 1
from public.sector_tags where slug = 'business-industry';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('SME Debt Restructuring & IBC Proceedings', 'sme-debt-restructuring-ibc', 1),
  ('Strategic Cost-Cutting & Cash Runway Extension', 'cost-cutting-runway-extension', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'distress-restructuring';

-- Additive, nullable on both the real brief flows -- doesn't disturb the
-- existing bucket_id/domain_needed flat fields at all.
alter table public.exchange_briefs add column if not exists sector_tag_id uuid references public.sector_tags(id);
alter table public.client_briefs add column if not exists sector_tag_id uuid references public.sector_tags(id);

