// functions/p/[id].js -- a Cloudflare Pages Function, file-based routing:
// any request to /p/<uuid> runs this, server-side, before anything static
// is served. This is the actual "public visibility" page: real HTML with
// real content and Open Graph/Twitter Card tags baked in at request time,
// so a shared link unfurls properly and a search engine can index it --
// neither of which app.html's client-rendered SPA shell can ever do, since
// a crawler or link-preview bot never runs its JavaScript.
//
// Reads from the posts_public view (SB_KEY below is the anon key, which is
// not a secret -- the app's own client code embeds the same one; the real
// access control is posts_public's own definition, which only ever
// surfaces a row when the author explicitly flipped public_visible on).
const SB_URL = 'https://npyoyylrqprawyavnfvv.supabase.co';
const SB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5weW95eWxycXByYXd5YXZuZnZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ2NTQ4NTgsImV4cCI6MjExMDIzMDg1OH0.K56AWim0w16YuL0r7AZMmkE_gj9MGb3tlRucPoy3gx8';

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function notFoundPage() {
  return new Response(
    `<!doctype html><html><head><meta charset="utf-8"><title>Post not found — MahaYukti</title>
    <meta name="robots" content="noindex"></head>
    <body style="font-family:sans-serif;max-width:600px;margin:80px auto;text-align:center;color:#101e33">
      <h1 style="font-family:serif">This post isn't public</h1>
      <p>It may have been removed, or the author hasn't made it publicly visible.</p>
      <a href="/" style="color:#C9943A">Go to MahaYukti →</a>
    </body></html>`,
    { status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8' } },
  );
}

export async function onRequestGet(context) {
  const { id } = context.params;
  if (!id || !/^[0-9a-f-]{36}$/i.test(id)) return notFoundPage();

  const res = await fetch(
    `${SB_URL}/rest/v1/posts_public?id=eq.${id}&select=*`,
    { headers: { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}` } },
  );
  const rows = res.ok ? await res.json() : [];
  const post = rows[0];
  if (!post) return notFoundPage();

  // A post made "as" an org shows the org's name here too -- the in-app
  // feed already does this (renderPostCards), this page was the one place
  // that still fell back to the individual author's name regardless.
  let authorName = post.author_display_name || post.author_username || 'A MahaYukti member';
  if (post.posted_as_org_id) {
    const orgRes = await fetch(
      `${SB_URL}/rest/v1/organizations?id=eq.${post.posted_as_org_id}&select=name`,
      { headers: { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}` } },
    );
    const org = (orgRes.ok ? await orgRes.json() : [])[0];
    if (org) authorName = org.name;
  }
  const title = post.title || `A post by ${authorName} on MahaYukti`;
  const description = (post.body || '').slice(0, 200);
  const image = (post.image_urls && post.image_urls[0]) || post.image_url || null;
  const pageUrl = `https://mahayukti.com/p/${id}`;
  const appUrl = `https://mahayukti.com/app.html#post-${id}`;

  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<link rel="canonical" href="${pageUrl}">
<meta property="og:type" content="article">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${pageUrl}">
${image ? `<meta property="og:image" content="${esc(image)}">` : ''}
<meta name="twitter:card" content="${image ? 'summary_large_image' : 'summary'}">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
${image ? `<meta name="twitter:image" content="${esc(image)}">` : ''}
<script type="application/ld+json">${JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'SocialMediaPosting',
    headline: title,
    articleBody: post.body,
    datePublished: post.created_at,
    author: { '@type': 'Person', name: authorName },
    url: pageUrl,
  })}</script>
<style>
  body{font-family:'Public Sans',sans-serif;max-width:640px;margin:0 auto;padding:40px 20px;color:#101e33;line-height:1.6}
  .wordmark{font-family:serif;font-size:22px;font-weight:700;margin-bottom:28px}
  .wordmark span{color:#C9943A}
  .author{font-weight:600;margin-bottom:4px}
  .date{font-size:13px;color:rgba(16,30,51,0.4);margin-bottom:20px}
  .title{font-family:serif;font-size:22px;font-weight:700;margin-bottom:12px}
  .body{font-size:16px;white-space:pre-wrap;margin-bottom:24px}
  img{max-width:100%;border-radius:6px;margin-bottom:20px}
  .cta{display:inline-block;background:#C9943A;color:#101e33;font-weight:700;text-decoration:none;padding:12px 24px;border-radius:4px}
</style>
</head>
<body>
  <div class="wordmark">Maha<span>Yukti</span></div>
  <div class="author">${esc(authorName)}</div>
  <div class="date">${new Date(post.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</div>
  ${post.title ? `<div class="title">${esc(post.title)}</div>` : ''}
  ${image ? `<img src="${esc(image)}" alt="">` : ''}
  <div class="body">${esc(post.body)}</div>
  <a class="cta" href="${appUrl}">Open in MahaYukti →</a>
</body>
</html>`;

  return new Response(html, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=300' },
  });
}
