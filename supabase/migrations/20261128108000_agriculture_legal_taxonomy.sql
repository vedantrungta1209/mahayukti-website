-- New L1: Agriculture & Agri-Tech. Unlike Defence & Security / Healthcare &
-- Medicine (seeded in 20261128107000), this has no existing match in either
-- the old flat `buckets` table or the current 14 sector_tags L1 rows -- a
-- genuinely new top-level vertical, not a case of attaching children to
-- something that already exists. Confirmed with the user before adding a
-- 15th L1 row rather than forcing it under the nearest existing bucket
-- (Business & Industry), which would have degraded match signal for the
-- specialised agri-tech sub-domains below.
insert into public.sector_tags (level, name, slug, sort_order) values
  (1, 'Agriculture & Agri-Tech', 'agriculture-agri-tech', 15);

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Supply Chain, Logistics & Cold Storage', 'agri-supply-chain-cold-storage', 1),
  ('Precision Agriculture & Farm Automation', 'precision-agriculture-farm-automation', 2),
  ('Agri-FinTech & Input Supply', 'agri-fintech-input-supply', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'agriculture-agri-tech';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Perishable Cold-Chain Infrastructure & Logistics Optimization', 'perishable-cold-chain-logistics', 1),
  ('Mandi Procurement & ONDC Agriculture Network Integration', 'mandi-procurement-ondc-agri', 2),
  ('Post-Harvest Loss Mitigation Protocols', 'post-harvest-loss-mitigation', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'agri-supply-chain-cold-storage';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Farm-Level IoT Deployment & Remote Sensing Data', 'farm-iot-remote-sensing', 1),
  ('Drone-as-a-Service (DaaS) Crop Spraying & Mapping Analytics', 'daas-crop-spraying-mapping', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'precision-agriculture-farm-automation';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Institutional Agri-Lending & Alternative Credit Scoring', 'institutional-agri-lending-credit-scoring', 1),
  ('Crop Insurance Risk Modeling & Claim Settlement Verification', 'crop-insurance-risk-modeling-claims', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'agri-fintech-input-supply';

-- Level 2/3 under the EXISTING "Legal" L1 row (not a new "Legal, Regulatory &
-- Corporate Governance" L1 -- that name was the proposal's framing, but
-- "Legal" already exists as an L1 and these are its children, same as
-- Cybersecurity/Tech-AI and Defence/Healthcare got children attached to
-- their existing rows rather than duplicate top-level sectors).
insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 2, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Corporate Governance & Board Advisory', 'corporate-governance-board-advisory', 1),
  ('Intellectual Property & Technology Law', 'ip-technology-law', 2),
  ('Dispute Resolution & Arbitrations', 'dispute-resolution-arbitrations', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'legal';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Independent Director Risk & Corporate Compliance Auditing', 'independent-director-risk-compliance-audit', 1),
  ('Internal Investigations, Whistleblower Claims & Fraud Forensics', 'internal-investigations-whistleblower-fraud', 2),
  ('Shareholder Activism Defense & Proxy Advisory Strategy', 'shareholder-activism-proxy-advisory', 3)
) as v(name, slug, sort_order)
where sector_tags.slug = 'corporate-governance-board-advisory';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Cross-Border Patent Filings & Tech Transfer Licensing', 'cross-border-patent-tech-transfer', 1),
  ('Data Sovereign Compliance & DPDP Act Readiness', 'data-sovereign-dpdp-readiness', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'ip-technology-law';

insert into public.sector_tags (parent_id, level, name, slug, sort_order)
select id, 3, v.name, v.slug, v.sort_order
from public.sector_tags, (values
  ('Commercial Arbitration Strategy & NCLT Proceedings Advocacy', 'commercial-arbitration-nclt-advocacy', 1),
  ('White-Collar Defense & ED/SFIO Advisory', 'white-collar-defense-ed-sfio-advisory', 2)
) as v(name, slug, sort_order)
where sector_tags.slug = 'dispute-resolution-arbitrations';
