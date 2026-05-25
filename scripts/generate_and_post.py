#!/usr/bin/env python3
"""
MahaYukti Daily Marketing Automation — 2 Posts Per Day
POST 1 (8:00 AM IST): Client-facing — targets potential clients across all domains
POST 2 (6:00 PM IST): Member-facing — targets professionals for enrolment
"""

import os, json, datetime, requests, sys, base64, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Credentials ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
GH_TOKEN              = os.environ["GH_TOKEN"]
POST_TYPE             = os.environ.get("POST_TYPE", "morning")  # "morning" or "evening"
ONLY_PLATFORMS        = os.environ.get("ONLY_PLATFORMS", "")    # comma-separated: "instagram", "linkedin", etc. Empty = all

# Social platform credentials (set as GitHub Actions secrets)
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN   = os.environ.get("LINKEDIN_AUTHOR_URN", "")    # urn:li:organization:XXX
FB_PAGE_ACCESS_TOKEN  = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID            = os.environ.get("FB_PAGE_ID", "")
IG_USER_ID            = os.environ.get("IG_USER_ID", "")
YOUTUBE_TOKEN_JSON    = os.environ.get("YOUTUBE_TOKEN_JSON", "")

# ── Brand ──────────────────────────────────────────────────────────────────
NAVY  = (11, 27, 58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (6, 15, 35)

TODAY    = datetime.date.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
POST_ID  = TODAY.strftime("%Y%m%d") + f"_{POST_TYPE}"

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
# Morning posts — client-facing, relatable real-world scenarios (14-day cycle)
MORNING_ROTATION = [
    ("Legal & Judiciary",        "Contract Disputes"),
    ("Finance & Banking",        "Debt Restructuring"),
    ("Cybersecurity",            "Ransomware Recovery"),
    ("Crisis Management",        "Corporate Reputation Crisis"),
    ("Technology",               "Digital Transformation"),
    ("Medicine & Healthcare",    "Healthcare M&A"),
    ("Intelligence & Research",  "Geopolitical Risk"),
    ("Legal & Judiciary",        "Startup Legal Advisory"),
    ("Finance & Banking",        "IPO Advisory"),
    ("Cybersecurity",            "Data Breach Response"),
    ("Crisis Management",        "Startup Funding Collapse"),
    ("Technology",               "AI & Machine Learning"),
    ("Medicine & Healthcare",    "Clinical Research"),
    ("Legal & Judiciary",        "Family & Succession Law"),
]

# Evening posts — member/consultant facing (8-day cycle)
EVENING_ROTATION = [
    ("Senior Lawyers & Advocates",           "Supreme Court Advocates"),
    ("Finance & Banking Professionals",      "Fintech Founders"),
    ("Cybersecurity Experts",                "CISOs"),
    ("Technology Leaders",                   "Tech Founders & Co-founders"),
    ("Medical & Healthcare Professionals",   "Senior Consultants & Specialists"),
    ("Intelligence & Research Professionals","Geopolitical Analysts"),
    ("Finance & Banking Professionals",      "Chartered Accountants"),
    ("Technology Leaders",                   "AI/ML Researchers"),
]

# ── Content angles (7 rotating frames) ────────────────────────────────────
CONTENT_ANGLES = [
    {
        "name": "gap_story",
        "description": (
            "Open with a real, specific scenario where a professional let a client down because of a "
            "knowledge gap — not incompetence, but depth. Show the exact moment they needed a "
            "specialist, not a generalist. Ground it in a named role and Indian city. Then show how "
            "Mahayukti bridges that gap. End by explaining: describe your problem at mahayukti.com, "
            "get matched to the verified specialist, get the outcome you actually needed."
        ),
    },
    {
        "name": "india_problem",
        "description": (
            "Frame this around the India-specific expert discovery problem: crores of capable "
            "professionals exist, but finding the RIGHT one for a niche need is completely broken. "
            "No directory, no referral, no Google search reliably surfaces the exact expert you need. "
            "Mahayukti is the fix — a vetted network where clients describe their problem and get "
            "introduced to the one professional in India best suited for it. Be specific and concrete."
        ),
    },
    {
        "name": "how_it_works",
        "description": (
            "Dedicate this post to clearly explaining what Mahayukti actually is and how it works — "
            "because most people don't know and are confused. "
            "FOR CLIENTS: You describe your problem → Mahayukti matches you → You work directly with a verified specialist. "
            "FOR EXPERTS: You apply → You get vetted → You get introduced to clients who need exactly your expertise. "
            "Make it feel simple, human, and obvious. Use a specific example from the domain/subdomain."
        ),
    },
    {
        "name": "community_angle",
        "description": (
            "Show the contrast: cold outreach, dead referrals, generic consultants, and random Google "
            "results — versus Mahayukti, where every professional is vetted, trusted, and reachable. "
            "Make it feel like joining something real — not an app, not a marketplace. A community of "
            "India's best professionals, with genuine accountability. Show what belonging looks like "
            "from both sides: a client who got the exact expert, a professional who found the exact case."
        ),
    },
    {
        "name": "founder_journey",
        "description": (
            "Tell a specific, lived-in story of a founder or business owner. Give them a concrete "
            "role and city (e.g. 'a Surat textile exporter', 'a Bengaluru SaaS founder'). Name the "
            "exact problem. Show what they tried first, why it failed (generic advice, wrong referral, "
            "LinkedIn cold message with no reply), and how Mahayukti gave them the exact specialist. "
            "The resolution should feel specific — not 'they got help' but 'the IP lawyer in Mumbai "
            "who had handled exactly this kind of trademark dispute.'"
        ),
    },
    {
        "name": "counterintuitive",
        "description": (
            "Challenge a belief the reader holds. Examples: 'Your CA is not your business advisor — "
            "they are your compliance officer', 'Having a lawyer on retainer is not the same as "
            "having the RIGHT lawyer', 'The expert you need has probably never posted on LinkedIn'. "
            "Use the counterintuitive insight to reframe why Mahayukti's depth and specificity matter. "
            "Then explain clearly: Mahayukti is where you find that exact expert — vetted, reachable, accountable."
        ),
    },
    {
        "name": "two_sided_value",
        "description": (
            "Write a post that speaks to BOTH sides of Mahayukti in one piece — clients who need "
            "expert help, and professionals who want their expertise to reach the right people. "
            "Show how the network works because both sides are in it together. Make it clear that "
            "Mahayukti is not a tool — it is a community with real humans on both sides, and signing "
            "up (whether as a client or as a professional) is how you enter that community."
        ),
    },
]

# ── Persistent counter — separate files for morning and evening ─────────────
_SCRIPTS_DIR    = Path(__file__).parent
MORNING_COUNTER = _SCRIPTS_DIR / "topic_counter_morning.txt"
EVENING_COUNTER = _SCRIPTS_DIR / "topic_counter_evening.txt"


def _get_topic_and_angle():
    counter_file = MORNING_COUNTER if POST_TYPE == "morning" else EVENING_COUNTER
    rotation     = MORNING_ROTATION if POST_TYPE == "morning" else EVENING_ROTATION

    count = int(counter_file.read_text().strip()) if counter_file.exists() else 0
    counter_file.write_text(str(count + 1))

    d, s  = rotation[count % len(rotation)]
    angle = CONTENT_ANGLES[count % len(CONTENT_ANGLES)]
    return d, s, angle


domain, subdomain, content_angle = _get_topic_and_angle()

# ══════════════════════════════════════════════════════════════════════════
# STEP 1 — Generate content via Claude
# ══════════════════════════════════════════════════════════════════════════
def generate_content():
    print(f"Generating {POST_TYPE} post | Domain: {domain} | Subdomain: {subdomain} | Angle: {content_angle['name']}")

    system = """\
WHAT MAHAYUKTI IS — say this clearly in every post:
Mahayukti is India's vetted professional advisory network.
When you have a complex problem that needs deep, specific expertise — legal, financial, tech, \
cybersecurity, medical, or intelligence — Mahayukti connects you to the exact verified specialist \
for that need. Not a generalist. Not a Google result. The one professional in India who has \
done this exact thing before.

THE FOUNDING INSIGHT:
Everyone already has a CA, a lawyer, a tech friend — but none of them have full depth. Your CA \
formed your company but doesn't know export compliance. Your lawyer handles contracts but not IP \
litigation. Your tech cousin can't do full-stack architecture. Mahayukti exists because the expert \
you actually need is out there — you just can't find them reliably. We fix that.

TWO SIDES, TWO CLEAR VALUE PROPOSITIONS:

FOR CLIENTS (people who need expert help):
1. Describe your problem at mahayukti.com
2. Mahayukti matches you with the verified specialist for your exact need
3. Work directly with that expert — with full accountability
→ CTA: "Describe your problem at mahayukti.com"

FOR MEMBERS / CONSULTANTS (experts who join):
1. Apply at mahayukti.com with your domain and credentials
2. Get vetted by the Mahayukti team
3. Get introduced to clients who need exactly your expertise — and earn from it
→ CTA: "Apply to join at mahayukti.com"

NETWORK STRUCTURE: Participants → Members → Advisory Group → Founding Members → Admin
Not a service. Not an app. A community of India's best professionals, open to anyone with a real need.

BRAND VOICE: Specific. Human. Grounded. Direct. Never vague, never corporate, never salesy.
WEBSITE: mahayukti.com
COLORS: Deep navy #0B1B3A, Gold #C9943A

HARD RULES — never break:
- Every post must make it clear what Mahayukti actually does — do not assume the reader knows.
- Every post must have a concrete, actionable CTA that drives sign-up or application.
- Never open with "Imagine this:" — banned.
- Never use "Who do you call" or any variation — banned.
- Never describe Mahayukti as a "marketplace", "platform", "app", or "firm".
- Titles must be specific to the scenario — never a template.
- LinkedIn must sound like a real person wrote it, not a PR agency.

Respond ONLY with a valid JSON object. No markdown. No preamble. No backticks.\
"""

    angle_instruction = (
        f'\nContent angle for this post ("{content_angle["name"]}"):\n'
        f'{content_angle["description"]}\n'
        "Use this angle to shape the opening, structure, and tone of blog_content and linkedin_text.\n"
    )

    if POST_TYPE == "morning":
        prompt = f"""Create a CLIENT-FACING morning post for Mahayukti.

Target audience: Indian business owners, founders, executives, and individuals who are dealing with a \
complex problem in the following domain and need the RIGHT expert — not a generic one.

Domain: {domain}
Subdomain: {subdomain}
{angle_instruction}

GOAL: The reader must finish this post knowing exactly what Mahayukti is, why it exists, and \
how to get help right now. They should feel: "This is exactly the solution I've been looking for."

MANDATORY in every post:
1. A clear, one-sentence explanation of what Mahayukti does (work it naturally into the content)
2. A concrete example specific to {subdomain} showing the gap Mahayukti fills
3. A 3-step explainer of how it works for a client (describe problem → get matched → work with expert)
4. A direct CTA: "Describe your problem at mahayukti.com — get matched to the exact specialist you need."

Tone: Specific, honest, human. Speak to a real pain point, not a hypothetical. Set it in India — \
use Indian cities, roles, and contexts. No corporate language.

Return this exact JSON:
{{
  "title": "Blog post title — specific to {subdomain} scenario, not a template (8-12 words)",
  "excerpt": "One sentence that hits the exact pain point for {subdomain} clients (max 25 words)",
  "blog_content": "Full blog post (900-1100 words). Use the content angle to open. Explain the specific problem in {domain}/{subdomain}. Show why finding the right expert in India is broken. Introduce Mahayukti clearly — what it is, how it works for a client, why it is different. Give 2 specific use cases in {subdomain}. End with direct CTA to mahayukti.com. Paragraph breaks only — no bullet points.",
  "linkedin_text": "LinkedIn post (180-220 words). Open with the specific pain point. Explain what Mahayukti is in plain language. Show how it works in 3 steps. End with: 'Describe your problem at mahayukti.com'. Sound like a real person — not a brand account.",
  "instagram_caption": "Instagram caption (90-110 words). Hook in first line. Explain Mahayukti in 2 sentences. Specific scenario. CTA: mahayukti.com. 8-10 relevant hashtags at end.",
  "facebook_text": "Facebook post (120-160 words). Conversational and relatable. Specific Indian scenario. Explain what Mahayukti does. Clear CTA at end.",
  "image_headline": "Bold image headline (max 7 words, specific to the problem — not generic)",
  "image_subtext": "One supporting line (max 10 words, includes mahayukti.com)",
  "post_type": "client",
  "domain": "{domain}",
  "subdomain": "{subdomain}"
}}"""
    else:
        prompt = f"""Create a CONSULTANT / MEMBER RECRUITMENT evening post for Mahayukti.

Target audience: Senior Indian professionals with deep expertise in the following domain who should \
JOIN Mahayukti as Members or Participants — and start getting matched with clients who need their skills.

Domain: {domain}
Subdomain: {subdomain}
{angle_instruction}

GOAL: The reader must finish this post understanding what Mahayukti is, why joining it is a clear \
professional and financial opportunity, and exactly how to apply. They should feel: \
"This community was built for people like me — and I need to be in it."

MANDATORY in every post:
1. A clear explanation of what Mahayukti is (one sentence, worked into the content naturally)
2. A specific, honest picture of what being a Mahayukti Member looks like for a {subdomain} professional
3. The 3-step join process (apply → get vetted → get matched with clients)
4. What they gain: client introductions, peer network, reputation, earnings
5. Direct CTA: "Apply to join at mahayukti.com"

Tone: Collegial, direct, identity-affirming. Speak to their professional reality — the gap between \
their expertise and the clients who can't find them. No vague aspiration. No corporate language.

Return this exact JSON:
{{
  "title": "Blog post title — specific to {subdomain} professionals, not a template (8-12 words)",
  "excerpt": "One sentence speaking to the professional opportunity for {subdomain} experts (max 25 words)",
  "blog_content": "Full blog post (900-1100 words). Use the content angle to open — speak directly to a {subdomain} professional's reality. Show the gap: their expertise exists but clients can't reach them. Introduce Mahayukti clearly — what it is, how it works for a Member. Paint a specific picture of what being in the network looks like. Explain the join process. Close with direct CTA to apply at mahayukti.com. Paragraph breaks only — no bullet points.",
  "linkedin_text": "LinkedIn post (180-220 words). Speak directly to {subdomain} professionals. Open with a truth they recognise about their work. Explain Mahayukti in plain language. Show what joining means in 3 steps. End with: 'Apply to join at mahayukti.com'. Sound like a real colleague — not a recruitment ad.",
  "instagram_caption": "Instagram caption (90-110 words). Identity-affirming hook. 2-sentence Mahayukti explanation. What they gain. CTA: mahayukti.com. 8-10 hashtags.",
  "facebook_text": "Facebook post (120-160 words). Community feel — belonging and opportunity. Specific to {subdomain}. Explain Mahayukti clearly. CTA to apply.",
  "image_headline": "Bold image headline (max 7 words, speaks to the professional — identity-affirming)",
  "image_subtext": "One supporting line (max 10 words, includes mahayukti.com)",
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
            "max_tokens": 5000,
            "system": system,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=120
    )
    r.raise_for_status()
    raw = r.json()["content"][0]["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()
    # Extract the first complete JSON object in case the model adds trailing commentary
    import re as _re
    m = _re.search(r'\{.*\}', raw, _re.DOTALL)
    if m:
        raw = m.group(0)
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
# STEP 5 — Direct social posting (no Make.com)
# ══════════════════════════════════════════════════════════════════════════

_LI_HEADERS = lambda: {
    "Authorization":            f"Bearer {LINKEDIN_ACCESS_TOKEN}",
    "LinkedIn-Version":         "202310",
    "X-Restli-Protocol-Version":"2.0.0",
    "Content-Type":             "application/json",
}

def post_to_linkedin(content, sq_path):
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_AUTHOR_URN:
        print("⚠️  LinkedIn credentials missing — skipping")
        return

    # 1. Initialize image upload (owner = person or org URN, both work)
    init = requests.post(
        "https://api.linkedin.com/rest/images?action=initializeUpload",
        headers=_LI_HEADERS(),
        json={"initializeUploadRequest": {"owner": LINKEDIN_AUTHOR_URN}},
    )
    init.raise_for_status()
    val        = init.json()["value"]
    upload_url = val["uploadUrl"]
    image_urn  = val["image"]

    # 2. Upload image binary
    with open(sq_path, "rb") as f:
        up = requests.put(
            upload_url,
            data=f,
            headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                     "Content-Type": "application/octet-stream"},
        )
        up.raise_for_status()

    # 3. Publish post
    requests.post(
        "https://api.linkedin.com/rest/posts",
        headers=_LI_HEADERS(),
        json={
            "author":         LINKEDIN_AUTHOR_URN,
            "commentary":     content["linkedin_text"],
            "visibility":     "PUBLIC",
            "distribution":   {"feedDistribution": "MAIN_FEED",
                               "targetEntities": [],
                               "thirdPartyDistributionChannels": []},
            "content":        {"media": {"title": content["title"], "id": image_urn}},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        },
    ).raise_for_status()
    print("✅ LinkedIn posted")


def post_to_facebook(content, sq_url):
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️  Facebook credentials missing — skipping")
        return
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos",
        data={
            "url":          sq_url,
            "caption":      content["facebook_text"],
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
    )
    r.raise_for_status()
    print("✅ Facebook photo posted")


def post_to_facebook_reel(content, reel_url):
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️  Facebook credentials missing — skipping reel")
        return
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos",
        data={
            "file_url":       reel_url,
            "description":    content["facebook_text"],
            "published":      "true",
            "access_token":   FB_PAGE_ACCESS_TOKEN,
        },
    )
    r.raise_for_status()
    print("✅ Facebook Reel posted")


def _ig_wait_for_container(container_id, max_polls=45, sleep_s=20):
    import time as _t
    for i in range(max_polls):
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code,status", "access_token": FB_PAGE_ACCESS_TOKEN},
        )
        data   = resp.json()
        status = data.get("status_code", "")
        print(f"   [poll {i+1}] HTTP {resp.status_code} | status_code={status!r} | raw={data}")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram container {status}: {data}")
        _t.sleep(sleep_s)
    raise TimeoutError("Instagram container did not finish in time")


def post_to_instagram_image(content, sq_url):
    if not FB_PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("⚠️  Instagram credentials missing — skipping")
        return
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={
            "image_url":    sq_url,
            "caption":      content["instagram_caption"],
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
    )
    print(f"   Container create HTTP {r.status_code}: {r.json()}")
    r.raise_for_status()
    cid = r.json()["id"]
    _ig_wait_for_container(cid, max_polls=3, sleep_s=20)  # DEBUG: 3 polls only
    requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": FB_PAGE_ACCESS_TOKEN},
    ).raise_for_status()
    print("✅ Instagram image posted")


def post_to_instagram_reel(content, reel_url):
    if not FB_PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("⚠️  Instagram credentials missing — skipping reel")
        return
    resolved_url = reel_url
    print(f"   Reel URL: {resolved_url}")
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media",
        data={
            "media_type":   "REELS",
            "video_url":    resolved_url,
            "caption":      content["instagram_caption"],
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
    )
    print(f"   Container create HTTP {r.status_code}: {r.json()}")
    r.raise_for_status()
    cid = r.json()["id"]
    _ig_wait_for_container(cid, max_polls=3, sleep_s=20)  # DEBUG: 3 polls only
    requests.post(
        f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish",
        data={"creation_id": cid, "access_token": FB_PAGE_ACCESS_TOKEN},
    ).raise_for_status()
    print("✅ Instagram Reel posted")


def upload_to_youtube(content, reel_path):
    if not YOUTUBE_TOKEN_JSON:
        print("⚠️  YouTube token missing — skipping")
        return
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("⚠️  google-api-python-client not installed — skipping YouTube")
        return

    creds = Credentials.from_authorized_user_info(
        json.loads(YOUTUBE_TOKEN_JSON),
        ["https://www.googleapis.com/auth/youtube.upload"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title":       content["title"][:100],
            "description": content["blog_content"][:5000],
            "tags":        [domain, subdomain, "MahaYukti", "India", "professionals",
                            "expert network", "Indian business"],
            "categoryId":  "27",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media   = MediaFileUpload(reel_path, mimetype="video/mp4", resumable=True,
                              chunksize=8 * 1024 * 1024)
    request = yt.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    print(f"✅ YouTube uploaded: https://youtube.com/watch?v={response['id']}")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    import time
    print(f"\n{'🌅' if POST_TYPE=='morning' else '🌆'} MahaYukti {POST_TYPE.upper()} Post — {DATE_STR}")
    print(f"🎯 Audience: {'Potential Clients' if POST_TYPE=='morning' else 'Member Enrolment'}")
    print(f"📌 Domain: {domain} → {subdomain}\n")

    content = generate_content()

    # Landscape image — kept for blog thumbnail
    land_name = f"post-{POST_ID}-land.png"
    land_path = f"/tmp/{land_name}"
    generate_image(content, 1200, 627, land_path)
    upload_image(land_path, land_name)

    # Square JPEG — used for all social platforms
    sq_name = f"post-{POST_ID}-sq.jpg"
    sq_path = f"/tmp/{sq_name}"
    generate_image(content, 1080, 1080, sq_path)
    sq_url  = upload_image(sq_path, sq_name)

    update_blog(content, land_name)

    # Generate reel (non-fatal — text posts still go out if reel fails)
    reel_path, reel_url = None, None
    try:
        from reel_generator import generate_reel
        print("\n🎬 Generating reel...")
        reel_path, reel_url = generate_reel(content, POST_ID, GH_TOKEN)
        print(f"   Reel ready: {reel_url}")
    except Exception as e:
        print(f"⚠️  Reel failed (continuing without it): {e}")

    # Upload reel to YouTube immediately (uses local file)
    if reel_path and os.path.exists(reel_path):
        try:
            print("\n📺 Uploading to YouTube...")
            upload_to_youtube(content, reel_path)
        except Exception as e:
            print(f"⚠️  YouTube upload failed: {e}")

    # Wait for Cloudflare and GitHub CDN to propagate uploaded images/reels
    print("\n⏳ Waiting 300s for CDN propagation...")
    time.sleep(300)

    _only = [p.strip().lower() for p in ONLY_PLATFORMS.split(",") if p.strip()]
    print("\n📣 Posting to social platforms..." + (f" (only: {', '.join(_only)})" if _only else ""))
    for name, fn, args in [
        ("LinkedIn",          post_to_linkedin,        (content, sq_path)),
        ("Facebook photo",    post_to_facebook,        (content, sq_url)),
        ("Facebook Reel",     post_to_facebook_reel,   (content, reel_url) if reel_url else None),
        ("Instagram image",   post_to_instagram_image, (content, sq_url)),
        ("Instagram Reel",    post_to_instagram_reel,  (content, reel_url) if reel_url else None),
    ]:
        if args is None:
            print(f"   {name}: skipped (no reel)")
            continue
        if _only and not any(p in name.lower() for p in _only):
            print(f"   {name}: skipped (not in ONLY_PLATFORMS)")
            continue
        try:
            fn(*args)
        except Exception as e:
            print(f"⚠️  {name} failed: {e}")

    # Clean up reel temp file
    if reel_path and os.path.exists(reel_path):
        os.remove(reel_path)

    print(f"\n✅ Done! '{content['title']}'")

if __name__ == "__main__":
    main()
