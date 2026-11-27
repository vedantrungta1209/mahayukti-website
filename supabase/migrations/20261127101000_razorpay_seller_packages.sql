-- Real payment integration for seller packages, replacing the
-- manual-admin-approval-only flow. Columns are additive -- every
-- subscription row that went through the old admin-activate path keeps
-- working exactly as before, these just track the new Razorpay path.
alter table public.seller_package_subscriptions add column if not exists razorpay_order_id text;
alter table public.seller_package_subscriptions add column if not exists razorpay_payment_id text;

create index if not exists seller_package_subscriptions_order_idx on public.seller_package_subscriptions (razorpay_order_id);
