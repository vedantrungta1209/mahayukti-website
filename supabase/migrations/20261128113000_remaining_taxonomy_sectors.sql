-- Level 2/3 depth for the last 5 real L1 sector_tags rows that had none
-- (14 L1s existed, "Other" deliberately stays a flat catch-all and is
-- skipped): Government & Public Affairs, Real Estate & Infrastructure,
-- Science & Deep-Tech, Trades & Craft, Culture & Public Influence. Same
-- additive pattern as every prior taxonomy migration this session -- pure
-- data, no code changes, the cascading picker already renders whatever
-- sector_tags holds.

-- Government & Public Affairs
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Policy & Regulatory Affairs', 'policy-regulatory-affairs', 1),
  ('Bureaucratic & Institutional Liaison', 'bureaucratic-institutional-liaison', 2),
  ('Public Sector & PSU Advisory', 'public-sector-psu-advisory', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'government-public-affairs';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Public Policy Advocacy & Lobbying Compliance', 'public-policy-advocacy-lobbying', 1),
  ('Regulatory Impact Assessment & Pre-Legislative Consultation', 'regulatory-impact-assessment', 2),
  ('Parliamentary & Committee Liaison', 'parliamentary-committee-liaison', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'policy-regulatory-affairs';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Central Government Ministry Liaison & File Movement', 'ministry-liaison-file-movement', 1),
  ('State Secretariat & District Administration Coordination', 'state-secretariat-district-coordination', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'bureaucratic-institutional-liaison';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('PSU Disinvestment & Strategic Sale Advisory', 'psu-disinvestment-strategic-sale', 1),
  ('Government Tender & Public Procurement (GeM) Strategy', 'government-tender-gem-procurement', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'public-sector-psu-advisory';

-- Real Estate & Infrastructure
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Land Acquisition & Title', 'land-acquisition-title', 1),
  ('Regulatory & Project Compliance', 'real-estate-regulatory-compliance', 2),
  ('Infrastructure Finance & Development', 'infrastructure-finance-development', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'real-estate-infrastructure';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Land Title Due Diligence & Litigation Risk Assessment', 'land-title-due-diligence', 1),
  ('Land Acquisition, Rehabilitation & Resettlement (LARR) Compliance', 'larr-compliance', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'land-acquisition-title';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('RERA Compliance & Dispute Resolution', 'rera-compliance-dispute-resolution', 1),
  ('Environmental Clearance & Forest Land Diversion Advisory', 'environmental-clearance-forest-diversion', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'real-estate-regulatory-compliance';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('PPP / InvIT Structuring for Infrastructure Projects', 'ppp-invit-structuring', 1),
  ('Construction Arbitration & EPC Contract Disputes', 'construction-arbitration-epc-disputes', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'infrastructure-finance-development';

-- Science & Deep-Tech
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Advanced Computing & Emerging Hardware', 'advanced-computing-emerging-hardware', 1),
  ('Lab-to-Market Commercialisation', 'lab-to-market-commercialisation', 2),
  ('Scientific & Regulatory Advisory', 'scientific-regulatory-advisory', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'science-deep-tech';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Quantum Computing Research Commercialisation', 'quantum-computing-commercialisation', 1),
  ('Semiconductor Design & Fabrication Strategy', 'semiconductor-design-fabrication', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'advanced-computing-emerging-hardware';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Tech Transfer Licensing & IP Spin-Out Structuring', 'tech-transfer-licensing-spinout', 1),
  ('Deep-Tech Grant & DST/BIRAC Funding Navigation', 'deep-tech-grant-dst-birac-funding', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'lab-to-market-commercialisation';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Biotech / Deep-Tech Regulatory Approval Pathways', 'biotech-deep-tech-regulatory-pathways', 1),
  ('Space-Tech & IN-SPACe Compliance Advisory', 'space-tech-inspace-compliance', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'scientific-regulatory-advisory';

-- Trades & Craft
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Artisan & Craft Enterprise', 'artisan-craft-enterprise', 1),
  ('Skilled Trades & Vocational Scaling', 'skilled-trades-vocational-scaling', 2),
  ('Craft Commerce & Market Access', 'craft-commerce-market-access', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'trades-craft';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('GI (Geographical Indication) Tag Registration & Protection', 'gi-tag-registration-protection', 1),
  ('Artisan Cluster Formalisation & Export Readiness', 'artisan-cluster-export-readiness', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'artisan-craft-enterprise';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Trade Certification & Skill India Accreditation Advisory', 'trade-certification-skill-india', 1),
  ('Contractor / Vendor Onboarding for Skilled Trades', 'contractor-vendor-onboarding-trades', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'skilled-trades-vocational-scaling';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Handicraft / Handloom Export Compliance', 'handicraft-handloom-export-compliance', 1),
  ('D2C & Marketplace Onboarding for Craft Businesses', 'd2c-marketplace-onboarding-craft', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'craft-commerce-market-access';

-- Culture & Public Influence
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Media & Entertainment Advisory', 'media-entertainment-advisory', 1),
  ('Public Relations & Reputation Management', 'pr-reputation-management', 2),
  ('Cultural Institutions & Heritage', 'cultural-institutions-heritage', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'culture-public-influence';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Content Licensing & OTT Distribution Rights', 'content-licensing-ott-distribution', 1),
  ('Celebrity / Influencer Brand Risk & Contract Structuring', 'celebrity-influencer-brand-risk', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'media-entertainment-advisory';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Crisis Communication & Reputation Recovery Strategy', 'crisis-communication-reputation-recovery', 1),
  ('Government / Regulatory Media Relations', 'government-regulatory-media-relations', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'pr-reputation-management';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Museum / Heritage Site Public-Private Partnership Advisory', 'museum-heritage-ppp-advisory', 1),
  ('Cultural Grant & Sponsorship Structuring', 'cultural-grant-sponsorship-structuring', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'cultural-institutions-heritage';
