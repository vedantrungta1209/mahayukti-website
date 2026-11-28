-- Level 2/3 depth for two existing L1 sector_tags rows ("Defence & Security",
-- "Healthcare & Medicine" -- both already seeded in 20261128102000, matching
-- their long-standing `buckets` namesakes 1:1) that otherwise have no
-- children, unlike Cybersecurity & Infosec / Technology & AI. Purely
-- additive: no new L1 row, no change to messaging/connections/moderation.

-- Level 2/3 under Defence & Security.
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Aerospace & Unmanned Systems', 'aerospace-unmanned-systems', 1),
  ('Strategic Supply Chain & Logistics', 'defence-supply-chain-logistics', 2),
  ('Homeland Security & Modernisation', 'homeland-security-modernisation', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'defence-security';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('UAV / Drone Payload Integration', 'uav-drone-payload-integration', 1),
  ('Anti-Drone (C-UAS) Interception Systems', 'anti-drone-cuas-interception', 2),
  ('Avionics Certification & DGCA Compliance', 'avionics-certification-dgca', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'aerospace-unmanned-systems';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Dual-Use Technology Export Licensing', 'dual-use-export-licensing', 1),
  ('Tier-2/Tier-3 Indigenisation (Make-in-India Frameworks)', 'tier-2-3-indigenisation', 2),
  ('Secure Communication & Tactical Networking Hardware', 'secure-comms-tactical-networking', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'defence-supply-chain-logistics';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Border Surveillance & Perimeter Intrusion Systems', 'border-surveillance-perimeter-intrusion', 1),
  ('Tactical Gear & Ballistics Procurement Advisory', 'tactical-gear-ballistics-procurement', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'homeland-security-modernisation';

-- Level 2/3 under Healthcare & Medicine.
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Clinical Operations & Regulatory Compliance', 'clinical-ops-regulatory-compliance', 1),
  ('Healthcare Infrastructure & M&A', 'healthcare-infrastructure-ma', 2),
  ('Digital Health & MedTech', 'digital-health-medtech', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'healthcare-medicine';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('NABH / JCI Accreditation Strategy & Audit Recovery', 'nabh-jci-accreditation-strategy', 1),
  ('CDSCO Drug / Medical Device Licensing', 'cdsco-drug-device-licensing', 2),
  ('Clinical Trial Protocol & Ethics Committee Setup', 'clinical-trial-protocol-ethics', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'clinical-ops-regulatory-compliance';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Brownfield Hospital Acquisition Due Diligence', 'brownfield-hospital-acquisition-dd', 1),
  ('Medical Equipment Procurement & Lifecycle Financing', 'medical-equipment-procurement-financing', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'healthcare-infrastructure-ma';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('ABDM (Ayushman Bharat Digital Mission) Architecture Compliance', 'abdm-architecture-compliance', 1),
  ('Telehealth Data Privacy & HIPAA/DISHA Architecture', 'telehealth-data-privacy-hipaa-disha', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'digital-health-medtech';
