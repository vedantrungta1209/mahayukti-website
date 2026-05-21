#!/usr/bin/env python3
"""
MahaYukti Daily Marketing Automation
Generates blog post + social content via Claude API
Creates branded PNG images
Posts to Facebook, Instagram, LinkedIn via Make.com webhook
Commits blog post to GitHub repo
"""

import os
import json
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap
import sys

# ── Config ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MAKE_WEBHOOK_URL  = os.environ["MAKE_WEBHOOK_URL"]

# Brand colors
NAVY  = (11, 27, 58)       # #0B1B3A
GOLD  = (201, 148, 58)     # #C9943A
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)

# Content pillars — rotated by day of week
PILLARS = [
    "Network Insight",        # Monday
    "Domain Spotlight",       # Tuesday
    "Founding Member Value",  # Wednesday
    "Cross-Domain Opportunity", # Thursday
    "India Professional Ecosystem", # Friday
    "Platform Feature",       # Saturday
    "Join MahaYukti",         # Sunday
]

TODAY      = datetime.date.today()
DAY_INDEX  = TODAY.weekday()  # 0=Monday … 6=Sunday
PILLAR     = PILLARS[DAY_INDEX]
DATE_STR   = TODAY.strftime("%Y-%m-%d")
POST_ID    = TODAY.strftime("%Y%m%d")

# ── Step 1: Generate content via Claude API ─────────────────────────────────
def generate_content():
    print(f"Generating content for pillar: {PILLAR}")

    system_prompt = """You are the content strategist for MahaYukti — India's first private, 
multi-domain professional network. Members include senior lawyers, bankers, fintech founders, 
cybersecurity experts, doctors, and intelligence professionals.

Brand voice: Authoritative. Premium. Exclusive. Ambitious. Never salesy or generic.
Brand colors: Deep navy #0B1B3A and gold #C9943A.
Website: mahayukti.com

You must respond ONLY with a valid JSON object, no markdown, no preamble."""

    user_prompt = f"""Today's content pillar: {PILLAR}
Today's date: {DATE_STR}

Generate a JSON object with these exact fields:
{{
  "title": "Blog post title (compelling, 8-12 words)",
  "excerpt": "One sentence teaser (max 25 words)",
  "blog_content": "Full blog post (800-1000 words, professional tone, 4-5 paragraphs, ends with CTA to apply at mahayukti.com)",
  "linkedin_text": "LinkedIn post (150-200 words, insight-led, professional, ends with mahayukti.com)",
  "instagram_caption": "Instagram caption (80-100 words, punchy, 8-10 relevant hashtags at end)",
  "facebook_text": "Facebook post (100-150 words, community-oriented, conversational)",
  "image_headline": "Short bold headline for image card (max 8 words)",
  "image_subtext": "Supporting line for image card (max 12 words)"
}}"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
    )

    response.raise_for_status()
    raw = response.json()["content"][0]["text"].strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    content = json.loads(raw)
    print("✅ Content generated")
    return content

# ── Step 2: Generate branded PNG image ─────────────────────────────────────
def generate_image(content, width, height, filename):
    img  = Image.new("RGB", (width, height), NAVY)
    draw = ImageDraw.Draw(img)

    # Gold top bar
    draw.rectangle([(0, 0), (width, 8)], fill=GOLD)
    # Gold bottom bar
    draw.rectangle([(0, height - 8), (width, height)], fill=GOLD)
    # Gold left accent
    draw.rectangle([(0, 0), (6, height)], fill=GOLD)

    # Load fonts — fallback to default if not available
    try:
        font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", int(height * 0.08))
        font_med   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", int(height * 0.045))
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(height * 0.032))
    except:
        font_big   = ImageFont.load_default()
        font_med   = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # MahaYukti wordmark
    draw.text((40, 30), "MAHAYUKTI", fill=GOLD, font=font_small)

    # Gold divider under wordmark
    draw.rectangle([(40, 65), (width - 40, 67)], fill=GOLD)

    # Main headline
    headline = content["image_headline"].upper()
    wrapped  = textwrap.wrap(headline, width=int(width / (height * 0.048)))
    y = int(height * 0.28)
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font_big)
        w    = bbox[2] - bbox[0]
        draw.text(((width - w) / 2, y), line, fill=WHITE, font=font_big)
        y += int(height * 0.11)

    # Gold rule
    draw.rectangle([(width // 2 - 60, y + 10), (width // 2 + 60, y + 13)], fill=GOLD)
    y += 35

    # Subtext
    subtext = content["image_subtext"]
    wrapped2 = textwrap.wrap(subtext, width=int(width / (height * 0.028)))
    for line in wrapped2:
        bbox = draw.textbbox((0, 0), line, font=font_med)
        w    = bbox[2] - bbox[0]
        draw.text(((width - w) / 2, y), line, fill=LIGHT, font=font_med)
        y += int(height * 0.065)

    # Bottom: website + pillar tag
    draw.text((40, height - 50), "mahayukti.com", fill=GOLD, font=font_small)
    pillar_text = PILLAR.upper()
    bbox = draw.textbbox((0, 0), pillar_text, font=font_small)
    draw.text((width - bbox[2] - bbox[0] - 40, height - 50), pillar_text, fill=LIGHT, font=font_small)

    img.save(filename)
    print(f"✅ Image saved: {filename}")
    return filename

# ── Step 3: Upload image to GitHub and get raw URL ─────────────────────────
def upload_image_to_github(filepath, filename):
    import base64

    gh_token = os.environ["GH_TOKEN"]
    repo     = "vedantrungta1209/mahayukti-website"
    api_url  = f"https://api.github.com/repos/{repo}/contents/images/{filename}"

    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    # Check if file exists (need SHA to update)
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    check = requests.get(api_url, headers=headers)
    sha   = check.json().get("sha") if check.status_code == 200 else None

    payload = {
        "message": f"Add image {filename}",
        "content": encoded,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(api_url, headers=headers, json=payload)
    r.raise_for_status()

    raw_url = f"https://raw.githubusercontent.com/{repo}/main/images/{filename}"
    print(f"✅ Image uploaded: {raw_url}")
    return raw_url

# ── Step 4: Update blog-data.json in GitHub ────────────────────────────────
def update_blog(content):
    import base64

    gh_token = os.environ["GH_TOKEN"]
    repo     = "vedantrungta1209/mahayukti-website"
    api_url  = f"https://api.github.com/repos/{repo}/contents/blog-data.json"
    headers  = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Fetch current file
    r   = requests.get(api_url, headers=headers)
    r.raise_for_status()
    data     = r.json()
    sha      = data["sha"]
    raw      = base64.b64decode(data["content"]).decode("utf-8")
    blog_db  = json.loads(raw)

    # Build new post
    new_post = {
        "id":      POST_ID,
        "date":    DATE_STR,
        "title":   content["title"],
        "excerpt": content["excerpt"],
        "content": content["blog_content"],
        "pillar":  PILLAR,
        "image":   f"post-{POST_ID}.png"
    }

    # Prepend (newest first), keep last 90 posts
    blog_db["posts"].insert(0, new_post)
    blog_db["posts"] = blog_db["posts"][:90]

    updated = base64.b64encode(json.dumps(blog_db, indent=2, ensure_ascii=False).encode()).decode()

    payload = {
        "message": f"Blog post: {content['title']} [{DATE_STR}]",
        "content": updated,
        "sha":     sha,
        "branch":  "main"
    }

    r2 = requests.put(api_url, headers=headers, json=payload)
    r2.raise_for_status()
    print("✅ Blog updated on GitHub → Cloudflare will auto-deploy")

# ── Step 5: Post to socials via Make.com webhook ───────────────────────────
def post_to_socials(content, image_url):
    payload = {
        "linkedin_text":    content["linkedin_text"],
        "instagram_caption": content["instagram_caption"],
        "facebook_text":    content["facebook_text"],
        "image_url":        image_url,
        "title":            content["title"],
        "link":             "https://mahayukti.com"
    }

    r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    r.raise_for_status()
    print("✅ Sent to Make.com → posting to Facebook, Instagram, LinkedIn")

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🚀 MahaYukti Daily Automation — {DATE_STR}")
    print(f"📌 Pillar: {PILLAR}\n")

    # 1. Generate content
    content = generate_content()

    # 2. Generate images (3 sizes)
    img_filename = f"post-{POST_ID}.png"
    img_path     = f"/tmp/{img_filename}"

    # LinkedIn/Facebook: 1200x627
    generate_image(content, 1200, 627, img_path)

    # 3. Upload image to GitHub (serves as CDN via raw.githubusercontent.com)
    image_url = upload_image_to_github(img_path, img_filename)

    # Instagram square: 1080x1080 (separate upload)
    ig_filename = f"post-{POST_ID}-sq.png"
    ig_path     = f"/tmp/{ig_filename}"
    generate_image(content, 1080, 1080, ig_path)
    ig_image_url = upload_image_to_github(ig_path, ig_filename)

    # 4. Update blog JSON → triggers Cloudflare deploy
    update_blog(content)

    # 5. Post to all socials via Make.com
    post_to_socials(content, image_url)

    print("\n✅ All done! Blog deployed, socials posted.")
    print(f"   Title: {content['title']}")

if __name__ == "__main__":
    main()
