// functions/sitemap.xml.js -- a real, dynamic sitemap covering every public
// post and organization page (functions/p/[id].js, functions/org/[slug].js).
// Static sitemap.xml only ever listed the fixed marketing pages; this closes
// the loop on the public-visibility layer actually being discoverable by
// search engines, not just directly linkable.
const SB_URL = 'https://npyoyylrqprawyavnfvv.supabase.co';
const SB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5weW95eWxycXByYXd5YXZuZnZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ2NTQ4NTgsImV4cCI6MjExMDIzMDg1OH0.K56AWim0w16YuL0r7AZMmkE_gj9MGb3tlRucPoy3gx8';

export async function onRequestGet() {
  const headers = { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}` };

  const [postsRes, orgsRes] = await Promise.all([
    fetch(`${SB_URL}/rest/v1/posts_public?select=id,created_at&order=created_at.desc&limit=5000`, { headers }),
    fetch(`${SB_URL}/rest/v1/organizations?select=slug,created_at&limit=5000`, { headers }),
  ]);
  const posts = postsRes.ok ? await postsRes.json() : [];
  const orgs = orgsRes.ok ? await orgsRes.json() : [];

  const urls = [
    '<url><loc>https://mahayukti.com/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
    '<url><loc>https://mahayukti.com/app.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>',
    '<url><loc>https://mahayukti.com/privacypolicy</loc></url>',
    '<url><loc>https://mahayukti.com/terms</loc></url>',
    '<url><loc>https://mahayukti.com/legal</loc></url>',
    ...posts.map((p) => `<url><loc>https://mahayukti.com/p/${p.id}</loc><lastmod>${p.created_at.slice(0, 10)}</lastmod></url>`),
    ...orgs.map((o) => `<url><loc>https://mahayukti.com/org/${o.slug}</loc></url>`),
  ];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': 'public, max-age=3600' },
  });
}
