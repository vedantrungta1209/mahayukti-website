#!/usr/bin/env python3
"""
MahaYukti Daily Marketing Automation — 2 Posts Per Day
POST 1 (8:00 AM IST): Client-facing — targets potential clients across all domains
POST 2 (6:00 PM IST): Member-facing — targets professionals for enrolment
"""

import os, json, datetime, requests, sys, base64, textwrap
from PIL import Image, ImageDraw, ImageFont

# ── Credentials ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MAKE_WEBHOOK_URL  = os.environ["MAKE_WEBHOOK_URL"]
GH_TOKEN          = os.environ["GH_TOKEN"]
POST_TYPE         = os.environ.get("POST_TYPE", "morning")  # "morning" or "evening"

# ── Brand ──────────────────────────────────────────────────────────────────
NAVY  = (11, 27, 58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (6, 15, 35)

TODAY    = datetime.date.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
POST_ID  = TODAY.strftime("%Y%m%d") + f"_{POST_TYPE}"
DAY      = TODAY.weekday()  # 0=Mon … 6=Sun

# ══════════════════════════════════════════════════════════════════════════
# DOMAIN & SUBDOMAIN UNIVERSE
# Everything MahaYukti covers — clients can come from any of these
# ══════════════════════════════════════════════════════════════════════════

CLIENT_DOMAINS = {
    "Legal & Judiciary": [
        "Corporate Law", "Mergers & Acquisitions", "Intellectual Property",
        "Contract Disputes", "Arbitration & Mediation", "Criminal Defence",
        "Real Estate Law", "Tax Litigation", "Constitutional Law",
        "Regulatory Compliance", "White Collar Crime", "Cross-border Disputes",
        "Startup Legal Advisory", "Family & Succession Law", "Labour & Employment Law"
    ],
    "Finance & Banking": [
        "Investment Banking", "Private Equity", "Venture Capital",
        "Wealth Management", "Corporate Treasury", "Trade Finance",
        "Derivatives & Structured Products", "Fintech Advisory",
        "Basel/RBI Compliance", "Debt Restructuring", "IPO Advisory",
        "Family Office Management", "Microfinance & NBFC", "Insurance Advisory",
        "Forex & Commodities"
    ],
    "Technology": [
        "AI & Machine Learning", "Cloud Architecture", "Product Strategy",
        "CTO Advisory", "Digital Transformation", "SaaS Growth",
        "Data Engineering", "Blockchain & Web3", "DevSecOps",
        "Enterprise Software", "Tech M&A Due Diligence", "EdTech",
        "HealthTech", "AgriTech", "GovTech"
    ],
    "Cybersecurity": [
        "Incident Response", "Ransomware Recovery", "VAPT",
        "SOC Setup & Management", "CISO Advisory", "Data Breach Response",
        "Regulatory Compliance (CERT-In, DPDP)", "Cloud Security",
        "OT/ICS Security", "Red Team Operations", "Threat Intelligence",
        "Dark Web Monitoring", "Board-level Cyber Risk Advisory",
        "Cyber Insurance Advisory", "Zero Trust Architecture"
    ],
    "Medicine & Healthcare": [
        "Hospital Administration", "Clinical Research", "MedTech",
        "Pharmaceutical Advisory", "Healthcare Policy",
        "Mental Health Services", "Telemedicine", "Medical Ethics & Law",
        "Oncology Advisory", "Surgical Innovation",
        "Healthcare M&A", "Insurance & TPA", "Diagnostics",
        "Public Health & Epidemiology", "Ayurveda & Integrative Medicine"
    ],
    "Intelligence & Research": [
        "Geopolitical Risk", "Corporate Intelligence",
        "Due Diligence & Background Verification", "Competitive Intelligence",
        "Market Research & Strategy", "Policy Research",
        "Academic Research Consulting", "Defence & Strategic Affairs",
        "Supply Chain Intelligence", "ESG Research",
        "Media Intelligence", "Electoral & Political Research",
        "Crisis Intelligence", "Open Source Intelligence (OSINT)",
        "Financial Crime Investigation"
    ],
    "Crisis Management": [
        "Corporate Reputation Crisis", "Regulatory Investigation Response",
        "Media & PR Crisis", "Cybersecurity Breach Crisis",
        "Legal Crisis & Litigation Management", "Financial Distress & Insolvency",
        "Leadership & Succession Crisis", "Product Recall & Liability",
        "Labour Dispute Escalation", "Cross-border Crisis",
        "Startup Funding Collapse", "Data Privacy Breach",
        "Healthcare & Clinical Crisis", "Political & Regulatory Crackdown",
        "Natural Disaster Business Continuity"
    ]
}

MEMBER_DOMAINS = {
    "Senior Lawyers & Advocates": [
        "Supreme Court Advocates", "High Court Practitioners",
        "Corporate Counsel", "IP Attorneys", "Arbitrators & Mediators",
        "Legal Academics", "Retired Judges", "Law Firm Partners"
    ],
    "Finance & Banking Professionals": [
        "Investment Bankers", "Fund Managers", "CFOs & Finance Directors",
        "Chartered Accountants", "Actuaries", "Fintech Founders",
        "Private Bankers", "Credit Risk Professionals"
    ],
    "Technology Leaders": [
        "CTOs & VPs Engineering", "AI/ML Researchers",
        "Tech Founders & Co-founders", "Product Leaders",
        "Cloud Architects", "Data Scientists", "Deep Tech Innovators",
        "Tech Policy Professionals"
    ],
    "Cybersecurity Experts": [
        "CISOs", "Ethical Hackers & Pentesters",
        "Threat Intelligence Analysts", "Security Architects",
        "Incident Responders", "Cyber Law Professionals",
        "SOC Managers", "Cyber Risk Consultants"
    ],
    "Medical & Healthcare Professionals": [
        "Senior Consultants & Specialists", "Hospital CEOs & Directors",
        "Medical Researchers", "Healthcare Investors",
        "MedTech Entrepreneurs", "Healthcare Policy Experts",
        "Pharmaceutical Executives", "Medical Ethicists"
    ],
    "Intelligence & Research Professionals": [
        "Former Intelligence Officers", "Geopolitical Analysts",
        "Corporate Intelligence Specialists", "Policy Researchers",
        "Investigative Journalists", "Strategic Advisors",
        "Think Tank Fellows", "Defence & Security Consultants"
    ]
}

# ── Rotating schedules ─────────────────────────────────────────────────────
# Morning posts rotate through client domains (7 day cycle)
MORNING_ROTATION = [
    ("Legal & Judiciary",        "Contract Disputes"),
    ("Finance & Banking",        "Debt Restructuring"),
    ("Cybersecurity",            "Ransomware Recovery"),
    ("Crisis Management",        "Corporate Reputation Crisis"),
    ("Technology",               "Digital Transformation"),
    ("Medicine & Healthcare",    "Healthcare M&A"),
    ("Intelligence & Research",  "Geopolitical Risk"),
]

# Evening posts rotate through member domains (6 day cycle)
EVENING_ROTATION = [
    ("Senior Lawyers & Advocates",          "Supreme Court Advocates"),
    ("Finance & Banking Professionals",     "Fintech Founders"),
    ("Cybersecurity Experts",               "CISOs"),
    ("Technology Leaders",                  "Tech Founders & Co-founders"),
    ("Medical & Healthcare Professionals",  "Senior Consultants & Specialists"),
    ("Intelligence & Research Professionals","Geopolitical Analysts"),
]

if POST_TYPE == "morning":
    domain, subdomain = MORNING_ROTATION[DAY % len(MORNING_ROTATION)]
    # Pick a random crisis subdomain 2x per week (Wed + Sat)
    if DAY in [2, 5]:
        domain, subdomain = "Crisis Management", MORNING_ROTATION[DAY % len(MORNING_ROTATION)][1]
else:
    domain, subdomain = EVENING_ROTATION[DAY % len(EVENING_ROTATION)]

# ══════════════════════════════════════════════════════════════════════════
# STEP 1 — Generate content via Claude
# ══════════════════════════════════════════════════════════════════════════
def generate_content():
    print(f"Generating {POST_TYPE} post | Domain: {domain} | Subdomain: {subdomain}")

    system = """You are the content strategist for MahaYukti — India's first private, 
multi-domain professional network connecting elite lawyers, bankers, fintech founders, 
cybersecurity experts, doctors, intelligence professionals and researchers.

Brand voice: Authoritative. Premium. Exclusive. Ambitious. Trustworthy.
Never generic, never salesy. Every post must feel like it came from 
the most respected professional network in India.
Colors: Deep navy #0B1B3A and gold #C9943A.
Website: mahayukti.com

Respond ONLY with a valid JSON object. No markdown. No preamble. No backticks."""

    if POST_TYPE == "morning":
        prompt = f"""Create a CLIENT-FACING morning post.

Target: Businesses, founders, executives, and organisations who need expert help in:
Domain: {domain}
Subdomain: {subdomain}

The post should make them feel: "MahaYukti connects me to the exact expert I need right now."
Tone: Problem-aware, solution-oriented, premium. Speak to their pain point first.
Include crisis urgency where relevant.

Return this exact JSON:
{{
  "title": "Blog post title (compelling, problem-aware, 8-12 words)",
  "excerpt": "One sentence that hits the pain point (max 25 words)",
  "blog_content": "Full blog post (800-1000 words). Open with a real-world scenario/pain point. Explain why finding the right expert is hard. Position MahaYukti as the solution. Include 2-3 specific use cases in {domain}. Close with CTA to reach out at mahayukti.com. Use paragraph breaks, no bullet points.",
  "linkedin_text": "LinkedIn post (150-200 words). Open with a bold statement or stat. Build to why MahaYukti exists for this exact problem. End: mahayukti.com",
  "instagram_caption": "Instagram caption (80-100 words). Punchy, visual language. 8-10 hashtags at end.",
  "facebook_text": "Facebook post (100-150 words). Conversational, relatable scenario. CTA at end.",
  "image_headline": "Bold image headline (max 7 words, uppercase impact)",
  "image_subtext": "Supporting image line (max 10 words)",
  "post_type": "client",
  "domain": "{domain}",
  "subdomain": "{subdomain}"
}}"""
    else:
        prompt = f"""Create a MEMBER ENROLMENT evening post.

Target: Senior professionals who should JOIN MahaYukti as members/participants:
Domain: {domain}
Subdomain: {subdomain}

The post should make them feel: "This network was built for people like me."
Tone: Aspirational, exclusive, collegial. Speak to their professional identity and ambition.
Emphasise: exclusive access, peer network, cross-domain intelligence, founding member opportunity.

Return this exact JSON:
{{
  "title": "Blog post title (identity-driven, aspirational, 8-12 words)",
  "excerpt": "One sentence that speaks to their professional ambition (max 25 words)",
  "blog_content": "Full blog post (800-1000 words). Open by painting a picture of what their professional life looks like inside MahaYukti. Describe the cross-domain connections, the intelligence, the exclusive access. Address why India's best professionals need this NOW. Include specific scenarios for {subdomain} professionals. Close with CTA to apply at mahayukti.com.",
  "linkedin_text": "LinkedIn post (150-200 words). Speak directly to {subdomain} professionals. Make them feel seen and valued. End with apply link: mahayukti.com",
  "instagram_caption": "Instagram caption (80-100 words). Aspirational, identity-affirming. 8-10 hashtags.",
  "facebook_text": "Facebook post (100-150 words). Community feel, belonging, exclusive opportunity.",
  "image_headline": "Bold image headline (max 7 words, identity-affirming)",
  "image_subtext": "Supporting image line (max 10 words)",
  "post_type": "member",
  "domain": "{domain}",
  "subdomain": "{subdomain}"
}}"""

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 2500,
            "system": system,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=60
    )
    r.raise_for_status()
    raw = r.json()["content"][0]["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    content = json.loads(raw.strip())
    print("✅ Content generated")
    return content

# ══════════════════════════════════════════════════════════════════════════
# STEP 2 — Generate branded PNG image
# ══════════════════════════════════════════════════════════════════════════
def generate_image(content, width, height, filepath):
    img  = Image.new("RGB", (width, height), NAVY)
    draw = ImageDraw.Draw(img)

    # Background texture — subtle diagonal lines
    for i in range(0, width + height, 40):
        draw.line([(i, 0), (0, i)], fill=(15, 32, 68), width=1)

    # Gold bars
    draw.rectangle([(0, 0), (width, 7)], fill=GOLD)
    draw.rectangle([(0, height - 7), (width, height)], fill=GOLD)
    draw.rectangle([(0, 0), (5, height)], fill=GOLD)

    # Dark overlay panel for text area
    draw.rectangle([(30, 20), (width - 30, height - 20)], fill=(8, 20, 45))
    draw.rectangle([(30, 20), (width - 30, 22)], fill=GOLD)

    try:
        font_logo  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   int(height * 0.038))
        font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",  int(height * 0.082))
        font_med   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",       int(height * 0.046))
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        int(height * 0.030))
        font_tag   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   int(height * 0.026))
    except:
        font_logo = font_big = font_med = font_small = font_tag = ImageFont.load_default()

    # Logo + tagline
    draw.text((55, 42), "MAHAYUKTI", fill=GOLD, font=font_logo)
    draw.text((55, 42 + int(height * 0.05)), "India's Premier Professional Network", fill=LIGHT, font=font_small)

    # Domain tag pill
    tag_text = f"  {content.get('domain', domain).upper()}  "
    tag_bbox = draw.textbbox((0,0), tag_text, font=font_tag)
    tag_w    = tag_bbox[2] - tag_bbox[0] + 20
    tag_y    = int(height * 0.28)
    draw.rectangle([(55, tag_y), (55 + tag_w, tag_y + int(height*0.048))], fill=GOLD)
    draw.text((65, tag_y + 4), tag_text.strip(), fill=NAVY, font=font_tag)

    # Post type badge
    badge = "FOR CLIENTS" if POST_TYPE == "morning" else "JOIN US"
    badge_bbox = draw.textbbox((0,0), badge, font=font_tag)
    badge_w    = badge_bbox[2] - badge_bbox[0] + 20
    draw.rectangle([(width - 55 - badge_w, tag_y), (width - 55, tag_y + int(height*0.048))],
                   outline=GOLD, width=1)
    draw.text((width - 55 - badge_w + 10, tag_y + 4), badge, fill=GOLD, font=font_tag)

    # Main headline
    headline = content["image_headline"].upper()
    words    = headline.split()
    lines    = []
    line     = ""
    for word in words:
        test = (line + " " + word).strip()
        bbox = draw.textbbox((0,0), test, font=font_big)
        if bbox[2] - bbox[0] > width - 120:
            if line: lines.append(line)
            line = word
        else:
            line = test
    if line: lines.append(line)

    y = int(height * 0.42)
    for l in lines:
        bbox = draw.textbbox((0,0), l, font=font_big)
        w    = bbox[2] - bbox[0]
        draw.text(((width - w) / 2, y), l, fill=WHITE, font=font_big)
        y += int(height * 0.105)

    # Gold rule
    draw.rectangle([(width//2 - 50, y+8), (width//2 + 50, y+11)], fill=GOLD)
    y += 28

    # Subtext
    subtext = content["image_subtext"]
    wrapped = textwrap.wrap(subtext, width=int(width / (height * 0.027)))
    for line in wrapped:
        bbox = draw.textbbox((0,0), line, font=font_med)
        w    = bbox[2] - bbox[0]
        draw.text(((width - w) / 2, y), line, fill=LIGHT, font=font_med)
        y += int(height * 0.065)

    # Footer
    footer_y = height - 48
    draw.text((55, footer_y), "mahayukti.com", fill=GOLD, font=font_small)
    right_text = DATE_STR
    rb = draw.textbbox((0,0), right_text, font=font_small)
    draw.text((width - 55 - (rb[2]-rb[0]), footer_y), right_text, fill=LIGHT, font=font_small)

    img.save(filepath, "JPEG", quality=95)
    print(f"✅ Image: {filepath}")

# ══════════════════════════════════════════════════════════════════════════
# STEP 3 — Upload image to GitHub (serves as CDN)
# ══════════════════════════════════════════════════════════════════════════
def upload_image(filepath, filename):
    repo    = "vedantrungta1209/mahayukti-website"
    api_url = f"https://api.github.com/repos/{repo}/contents/images/{filename}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    check = requests.get(api_url, headers=headers)
    sha   = check.json().get("sha") if check.status_code == 200 else None

    payload = {"message": f"Image: {filename}", "content": encoded, "branch": "main"}
    if sha: payload["sha"] = sha

    r = requests.put(api_url, headers=headers, json=payload)
    r.raise_for_status()
    url = f"https://mahayukti.com/images/{filename}"
    print(f"✅ Uploaded: {url}")
    return url

# ══════════════════════════════════════════════════════════════════════════
# STEP 4 — Update blog-data.json
# ══════════════════════════════════════════════════════════════════════════
def update_blog(content, image_filename):
    repo    = "vedantrungta1209/mahayukti-website"
    api_url = f"https://api.github.com/repos/{repo}/contents/blog-data.json"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    r        = requests.get(api_url, headers=headers); r.raise_for_status()
    data     = r.json()
    sha      = data["sha"]
    blog_db  = json.loads(base64.b64decode(data["content"]).decode())

    new_post = {
        "id":        POST_ID,
        "date":      DATE_STR,
        "time":      "08:00" if POST_TYPE == "morning" else "18:00",
        "post_type": POST_TYPE,
        "audience":  "Clients" if POST_TYPE == "morning" else "Members",
        "domain":    domain,
        "subdomain": subdomain,
        "title":     content["title"],
        "excerpt":   content["excerpt"],
        "content":   content["blog_content"],
        "image":     image_filename
    }

    blog_db["posts"].insert(0, new_post)
    blog_db["posts"] = blog_db["posts"][:180]  # keep 90 days × 2 posts

    updated = base64.b64encode(
        json.dumps(blog_db, indent=2, ensure_ascii=False).encode()
    ).decode()

    r2 = requests.put(api_url, headers=headers, json={
        "message": f"[{POST_TYPE.upper()}] {content['title']} [{DATE_STR}]",
        "content": updated, "sha": sha, "branch": "main"
    })
    r2.raise_for_status()
    print("✅ Blog updated → Cloudflare deploying...")

# ══════════════════════════════════════════════════════════════════════════
# STEP 5 — Post to socials via Make.com
# ══════════════════════════════════════════════════════════════════════════
def post_to_socials(content, image_url, ig_image_url):
    payload = {
        "post_type":          POST_TYPE,
        "audience":           "clients" if POST_TYPE == "morning" else "members",
        "domain":             domain,
        "linkedin_text":      content["linkedin_text"],
        "instagram_caption":  content["instagram_caption"],
        "facebook_text":      content["facebook_text"],
        "image_url":          image_url,
        "ig_image_url":       ig_image_url,
        "title":              content["title"],
        "link":               "https://mahayukti.com"
    }
    r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    r.raise_for_status()
    print("✅ Sent to Make.com → Facebook + Instagram + LinkedIn")

# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{'🌅' if POST_TYPE=='morning' else '🌆'} MahaYukti {POST_TYPE.upper()} Post — {DATE_STR}")
    print(f"🎯 Audience: {'Potential Clients' if POST_TYPE=='morning' else 'Member Enrolment'}")
    print(f"📌 Domain: {domain} → {subdomain}\n")

    content = generate_content()

    # Landscape image (LinkedIn + Facebook)
    land_name = f"post-{POST_ID}-land.png"
    land_path = f"/tmp/{land_name}"
    generate_image(content, 1200, 627, land_path)
    land_url  = upload_image(land_path, land_name)

    # Square image (Instagram)
    sq_name   = f"post-{POST_ID}-sq.jpg"
    sq_path   = f"/tmp/{sq_name}"
    generate_image(content, 1080, 1080, sq_path)
    sq_url    = upload_image(sq_path, sq_name)

    update_blog(content, land_name)

    # Wait for Cloudflare to deploy the uploaded images before Instagram fetches them
    import time
    print("⏳ Waiting 90s for Cloudflare deployment...")
    time.sleep(90)

    post_to_socials(content, land_url, sq_url)

    print(f"\n✅ Done! '{content['title']}'")

if __name__ == "__main__":
    main()
