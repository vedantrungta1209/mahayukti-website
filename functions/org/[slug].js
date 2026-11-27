// functions/org/[slug].js -- same real-SSR approach as functions/p/[id].js,
// but for an organization's public page: its profile plus any posts it has
// posted as itself that are also public_visible. organizations itself is
// already publicly readable (organizations_select_all), so this only needs
// posts_public for the post list.
const SB_URL = 'https://npyoyylrqprawyavnfvv.supabase.co';
const SB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5weW95eWxycXByYXd5YXZuZnZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ2NTQ4NTgsImV4cCI6MjExMDIzMDg1OH0.K56AWim0w16YuL0r7AZMmkE_gj9MGb3tlRucPoy3gx8';

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function notFoundPage() {
  return new Response(
    `<!doctype html><html><head><meta charset="utf-8"><title>Organization not found — MahaYukti</title>
    <meta name="robots" content="noindex"></head>
    <body style="font-family:sans-serif;max-width:600px;margin:80px auto;text-align:center;color:#101e33">
      <h1 style="font-family:serif">No organization here</h1>
      <a href="/" style="color:#C9943A">Go to MahaYukti →</a>
    </body></html>`,
    { status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' } },
  );
}

export async function onRequestGet(context) {
  const { slug } = context.params;
  if (!slug) return notFoundPage();

  const orgRes = await fetch(
    `${SB_URL}/rest/v1/organizations?slug=eq.${encodeURIComponent(slug)}&select=*`,
    { headers: { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}` } },
  );
  const org = (orgRes.ok ? await orgRes.json() : [])[0];
  if (!org) return notFoundPage();

  const postsRes = await fetch(
    `${SB_URL}/rest/v1/posts_public?posted_as_org_id=eq.${org.id}&order=created_at.desc&limit=20&select=*`,
    { headers: { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}` } },
  );
  const posts = postsRes.ok ? await postsRes.json() : [];

  const kindLabel = { company: 'Company', media: 'Media house', government: 'Government body', ngo: 'NGO', other: 'Organization' }[org.kind] || 'Organization';
  const pageUrl = `https://mahayukti.com/org/${esc(slug)}`;

  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(org.name)} — MahaYukti</title>
<meta name="description" content="${esc(org.description || kindLabel + ' on MahaYukti')}">
<link rel="canonical" href="${pageUrl}">
<meta property="og:type" content="profile">
<meta property="og:title" content="${esc(org.name)}">
<meta property="og:description" content="${esc(org.description || kindLabel + ' on MahaYukti')}">
<meta property="og:url" content="${pageUrl}">
${org.logo_url ? `<meta property="og:image" content="${esc(org.logo_url)}">` : ''}
<script type="application/ld+json">${JSON.stringify({
    '@context': 'https://schema.org',
    '@type': org.kind === 'government' ? 'GovernmentOrganization' : org.kind === 'ngo' ? 'NGO' : 'Organization',
    name: org.name,
    description: org.description,
    url: pageUrl,
  })}</script>
<style>
  body{font-family:'Public Sans',sans-serif;max-width:640px;margin:0 auto;padding:40px 20px;color:#101e33;line-height:1.6}
  .wordmark{font-family:serif;font-size:22px;font-weight:700;margin-bottom:28px}
  .wordmark span{color:#C9943A}
  .kind{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#C9943A;margin-bottom:6px}
  .name{font-family:serif;font-size:26px;font-weight:700;margin-bottom:10px}
  .desc{font-size:15px;color:rgba(16,30,51,0.7);margin-bottom:28px}
  .post{border-top:1px solid rgba(16,30,51,0.1);padding:18px 0}
  .post .date{font-size:12px;color:rgba(16,30,51,0.4);margin-bottom:6px}
  .post img{max-width:100%;border-radius:6px;margin:10px 0}
  .cta{display:inline-block;background:#C9943A;color:#101e33;font-weight:700;text-decoration:none;padding:12px 24px;border-radius:4px;margin-top:20px}
</style>
</head>
<body>
  <div class="wordmark">Maha<span>Yukti</span></div>
  <div class="kind">${esc(kindLabel)}${org.verified ? ' · Verified' : ''}</div>
  <div class="name">${esc(org.name)}</div>
  ${org.description ? `<div class="desc">${esc(org.description)}</div>` : ''}
  ${posts.map((p) => `<div class="post">
    <div class="date">${new Date(p.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</div>
    ${p.title ? `<strong>${esc(p.title)}</strong><br>` : ''}
    ${esc(p.body)}
    ${p.image_url ? `<img src="${esc(p.image_url)}" alt="">` : ''}
  </div>`).join('') || '<p style="color:rgba(16,30,51,0.4);margin-top:20px">No public posts yet.</p>'}
  <a class="cta" href="https://mahayukti.com/app.html">Open MahaYukti →</a>
</body>
</html>`;

  return new Response(html, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=300' },
  });
}
