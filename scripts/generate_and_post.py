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
LINKEDIN_ACCESS_TOKEN     = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN       = os.environ.get("LINKEDIN_AUTHOR_URN", "")
MAKE_LINKEDIN_WEBHOOK_URL = os.environ.get("MAKE_LINKEDIN_WEBHOOK_URL", "")  # Make.com fallback
IMGBB_API_KEY             = os.environ.get("IMGBB_API_KEY", "")              # for public image URLs
FB_PAGE_ACCESS_TOKEN  = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID            = os.environ.get("FB_PAGE_ID", "")
IG_USER_ID            = os.environ.get("IG_USER_ID", "")
YOUTUBE_TOKEN_JSON    = os.environ.get("YOUTUBE_TOKEN_JSON", "")
X_API_KEY             = os.environ.get("X_API_KEY", "")
X_API_SECRET          = os.environ.get("X_API_SECRET", "")
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID   = os.environ.get("TELEGRAM_CHANNEL_ID", "")
X_ACCESS_TOKEN        = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

# ── Brand ──────────────────────────────────────────────────────────────────
# Editorial identity — NOT corporate navy/gold
CHARCOAL = (12,  12,  12)   # near-black background
SAFFRON  = (228, 71,  26)   # India saffron — single accent, used minimally
WHITE    = (255, 255, 255)
MUTED    = (160, 160, 155)  # secondary text
OFFWHITE = (235, 232, 226)  # warm off-white for body text

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
You are a founding member of Mahayukti. You're building a movement — not just a business.

THE MOVEMENT:
Mahayukti is part of a larger mission: Make India the Greatest. Not a slogan. A direction.
India has produced world-class minds in law, finance, technology, medicine, intelligence, security.
But those minds are scattered, inaccessible, and disconnected from the people and problems that need them most.
Mahayukti is the infrastructure of this movement — connecting India's best experts with the people who need them, and with each other.
Every post is a step in this campaign. Every post should make someone feel: India is rising. I want to be part of this.

WHAT MAHAYUKTI DOES:
For clients: Describe your problem at mahayukti.com → get matched to the exact verified specialist → get the outcome you needed.
For experts: Apply at mahayukti.com → get vetted → get introduced to clients who need exactly your expertise.
Never call it a "marketplace", "platform", "app", or "firm". It's a network. A movement. A community.

TONE — THE MOST IMPORTANT THING:
Warm. Positive. Energising. We celebrate India's potential — we don't complain about its problems.
We support our leaders' vision of a stronger India. We bring people in, not call people out.
We speak to the masses — the student, the entrepreneur, the professional, the homemaker — not just the elite.
We want people to feel: this movement is for me, I belong here, I want to share this.

WHAT KILLS THIS TONE — never do these:
- No cynicism. No "India is broken." No pointing fingers at systems or institutions.
- Never attack any politician, party, government body, or official. Ever.
- No religious, caste, or regional framing. India is one.
- No AI phrases: "It's important to note", "In today's world", "Navigate", "Landscape", "Robust", "Tapestry", "Shed light on", "Pivotal", "In conclusion", "Delve". Instant giveaways.
- No "Imagine this:" — banned. No "Who do you call" — banned.
- Don't sound like a PR agency. Sound like a passionate Indian who means it.

WRITING CRAFT:
- Specific over general. A CFO in Pune, not "a business leader". A startup in Bengaluru, not "companies".
- Vary sentence length. Short sentences hit. Long ones build.
- Contractions always. "doesn't" not "does not".
- LinkedIn: short paragraphs, no bullets, max 3 hashtags, one open question at end, first line stops the scroll.
- Each platform gets its own voice — don't resize, rewrite.
- Make it shareable. Make it feel like something worth passing on.

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
  "linkedin_text": "LinkedIn post (180-220 words). FIRST LINE must be a scroll-stopper stat or provocative truth about {subdomain} in India — NOT 'I' and NOT generic. Short paragraphs (1-2 lines, lots of white space). Explain the gap Mahayukti fills. End with a genuine question inviting comments. CTA: 'Describe your problem at mahayukti.com'. Use max 3 hashtags at end. Sound like a real founding team member sharing a genuine observation — not a brand.",
  "instagram_caption": "Instagram caption — BBC reel style. First line: 3-5 word scroll-stopping hook (no greeting, no 'we', just the truth). Then 3-4 SHORT punchy lines (5-8 words each, one idea per line). Then one line: Register at mahayukti.com. Then handle line: @wearemahayukti. Then 10 dots on separate lines to push hashtags below fold. Then hashtags: #India #Mahayukti #Advisory #ExpertAdvice #IndiaFirst #MahayuktiAdvisory and 4 domain-specific ones. Total under 220 words. NO corporate language. NO emojis except at very end if needed.",
  "facebook_text": "Facebook post (120-160 words). Conversational and relatable. Specific Indian scenario. Explain what Mahayukti does. End with: Find us on X @wearemahayukti | linkedin.com/company/mahayukti | facebook.com/MahaYuktiAdvisory | mahayukti.com.",
  "twitter_text": "X post (200-500 chars, Premium long-form). Punchy and human — a real observation about {subdomain} in India and how Mahayukti fixes the gap. End with mahayukti.com or linkedin.com/company/mahayukti. Max 2 hashtags.",
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
  "linkedin_text": "LinkedIn post (180-220 words). FIRST LINE must be an identity-affirming truth or uncomfortable observation about being a top {subdomain} professional in India — NOT 'I' and NOT generic. Short paragraphs, lots of white space. End with a question that makes {subdomain} professionals want to comment. CTA: 'Apply to join at mahayukti.com'. Max 3 hashtags. Sound like a respected peer sharing a real insight.",
  "instagram_caption": "Instagram caption — BBC reel style. First line: 3-5 word identity-affirming hook aimed at {subdomain} professionals (no 'we', no greeting, just the truth they feel). Then 3-4 SHORT punchy lines (5-8 words each). Then: Apply at mahayukti.com. Then @wearemahayukti. Then 10 dots on separate lines to push hashtags below fold. Then hashtags: #India #Mahayukti #Advisory #ExpertNetwork #IndiaFirst and 5 domain-specific ones. NO corporate language. NO emojis. Sound like a person, not a brand.",
  "facebook_text": "Facebook post (120-160 words). Community feel — belonging and opportunity. Specific to {subdomain}. Explain Mahayukti clearly. End with: Find us on X @wearemahayukti | linkedin.com/company/mahayukti | facebook.com/MahaYuktiAdvisory | mahayukti.com.",
  "twitter_text": "X post (200-500 chars, Premium long-form). Identity-affirming and human — speaks directly to a {subdomain} professional's reality. What Mahayukti means for them. End with mahayukti.com or linkedin.com/company/mahayukti. Max 2 hashtags.",
  "image_headline": "Bold image headline (max 7 words, speaks to the professional — identity-affirming)",
  "image_subtext": "One supporting line (max 10 words, includes mahayukti.com)",
  "post_type": "member",
  "domain": "{domain}",
  "subdomain": "{subdomain}"
}}"""

    import time as _t
    for _attempt in range(5):
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
        if r.status_code in (429, 529) and _attempt < 4:
            wait = 30 * (2 ** _attempt)  # 30s, 60s, 120s, 240s
            print(f"   Anthropic API overloaded ({r.status_code}), retrying in {wait}s…")
            _t.sleep(wait)
            continue
        r.raise_for_status()
        break
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
_DOMAIN_PROMPTS_IMG = {
    "Legal & Judiciary":         "supreme court india law books scales justice dark navy dramatic cinematic no text no people",
    "Finance & Banking":         "india stock exchange financial charts dark dramatic cinematic no text no people",
    "Technology":                "server room data center blue neon india tech futuristic dark cinematic no text no people",
    "Cybersecurity":             "cyber security dark matrix red neon threat intelligence india cinematic no text no people",
    "Medicine & Healthcare":     "modern hospital india medical laboratory dark cinematic no text no people",
    "Intelligence & Research":   "intelligence analysis dark room india map geopolitical dramatic cinematic no text no people",
    "Crisis Management":         "crisis boardroom india corporate dramatic tension dark cinematic no text no people",
    "Senior Lawyers & Advocates": "supreme court advocate india law dark dramatic cinematic no text no people",
    "Finance & Banking Professionals": "chartered accountant office india finance dark cinematic no text no people",
    "Technology Leaders":        "tech leader india digital transformation dark dramatic cinematic no text no people",
    "Cybersecurity Experts":     "ciso security expert india dark cyber operations cinematic no text no people",
    "Medical & Healthcare Professionals": "senior doctor specialist india hospital dark cinematic no text no people",
    "Intelligence & Research Professionals": "intelligence analyst india research dark dramatic cinematic no text no people",
}


def _fetch_pollinations_img(domain_key: str, post_id: str, width: int, height: int):
    import hashlib, io as _io
    from urllib.parse import quote as _quote
    prompt = _DOMAIN_PROMPTS_IMG.get(
        domain_key,
        "professional india advisory network dark dramatic cinematic no text no people",
    )
    orientation = "vertical portrait" if height > width else "horizontal landscape"
    prompt = f"{prompt} {orientation}"
    seed = int(hashlib.md5(f"{domain_key}:{post_id}".encode()).hexdigest()[:8], 16) % 1_000_000
    url = f"https://image.pollinations.ai/prompt/{_quote(prompt)}?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=50)
            if r.status_code == 200:
                img = Image.open(_io.BytesIO(r.content)).convert("RGB")
                return img.resize((width, height), Image.LANCZOS)
        except Exception as e:
            print(f"  Pollinations img attempt {attempt+1}: {e}")
            import time as _time
            if attempt < 2: _time.sleep(3)
    return None


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_px: int, draw) -> list[str]:
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textbbox((0, 0), test, font=font)[2] > max_px and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def generate_image(content, width, height, filepath):
    """
    Editorial design — clean charcoal, saffron accent, left-aligned.
    Typography-first. No gold bars, no navy overlay, no ALL CAPS, no pills.
    """
    domain_key = content.get("domain", domain)

    # ── Background: clean charcoal + very faint Pollinations texture ──────
    img = Image.new("RGB", (width, height), CHARCOAL)

    bg_photo = _fetch_pollinations_img(domain_key, POST_ID, width, height)
    if bg_photo:
        # Blend photo in at low opacity — texture not template
        dark = Image.new("RGB", (width, height), CHARCOAL)
        img = Image.blend(dark, bg_photo, alpha=0.18)

    draw = ImageDraw.Draw(img)

    # ── Single saffron left border — the only decoration ──────────────────
    border_w = max(6, int(width * 0.006))
    draw.rectangle([(0, 0), (border_w, height)], fill=SAFFRON)

    # ── Font scale (proportional to image height) ─────────────────────────
    pad_l  = border_w + int(width * 0.055)   # left margin after border
    pad_r  = int(width * 0.06)               # right margin
    max_w  = width - pad_l - pad_r

    f_wordmark = _load_font(int(height * 0.038), bold=True)
    f_domain   = _load_font(int(height * 0.026), bold=False)
    f_headline = _load_font(int(height * 0.082), bold=True)
    f_body     = _load_font(int(height * 0.040), bold=False)
    f_url      = _load_font(int(height * 0.030), bold=True)

    # ── Wordmark — top left ───────────────────────────────────────────────
    wm_y = int(height * 0.055)
    draw.text((pad_l, wm_y), "MAHAYUKTI", fill=WHITE, font=f_wordmark)

    # Domain / category — top right, saffron, small
    dom_text = domain_key.upper()
    dom_bbox = draw.textbbox((0, 0), dom_text, font=f_domain)
    dom_x = width - pad_r - (dom_bbox[2] - dom_bbox[0])
    dom_y = wm_y + (draw.textbbox((0, 0), "MAHAYUKTI", font=f_wordmark)[3] - (dom_bbox[3] - dom_bbox[1])) // 2
    draw.text((dom_x, dom_y), dom_text, fill=SAFFRON, font=f_domain)

    # ── Thin saffron rule under wordmark ─────────────────────────────────
    rule_y = wm_y + int(height * 0.065)
    draw.rectangle([(pad_l, rule_y), (pad_l + int(width * 0.07), rule_y + 2)], fill=SAFFRON)

    # ── Headline — large, sentence case, left-aligned ────────────────────
    headline = content["image_headline"]   # sentence case — NOT uppercased
    h_lines  = _wrap_text(headline, f_headline, max_w, draw)

    h_line_h = int(height * 0.095)
    h_y      = int(height * 0.24)

    for ln in h_lines[:3]:   # cap at 3 lines
        draw.text((pad_l, h_y), ln, fill=WHITE, font=f_headline)
        h_y += h_line_h

    # ── Thin saffron accent after headline ───────────────────────────────
    draw.rectangle([(pad_l, h_y + 10), (pad_l + int(width * 0.12), h_y + 13)], fill=SAFFRON)
    h_y += int(height * 0.055)

    # ── Body subtext — left-aligned, muted ───────────────────────────────
    subtext = content.get("image_subtext", "")
    b_lines = _wrap_text(subtext, f_body, max_w, draw)
    b_line_h = int(height * 0.052)

    for ln in b_lines[:3]:
        draw.text((pad_l, h_y), ln, fill=OFFWHITE, font=f_body)
        h_y += b_line_h

    # ── Footer — mahayukti.com bottom-left in saffron ────────────────────
    url_y = height - int(height * 0.075)
    draw.text((pad_l, url_y), "mahayukti.com", fill=SAFFRON, font=f_url)

    # Date — bottom right, muted
    d_bbox = draw.textbbox((0, 0), DATE_STR, font=f_domain)
    draw.text((width - pad_r - (d_bbox[2] - d_bbox[0]), url_y + 4), DATE_STR, fill=MUTED, font=f_domain)

    img.save(filepath, "JPEG", quality=95)
    print(f"✅ Image: {filepath}")

# ══════════════════════════════════════════════════════════════════════════
# STEP 3 — Upload image to GitHub (serves as CDN)
# ══════════════════════════════════════════════════════════════════════════
def upload_image(filepath, filename):
    repo    = "vedantrungta1209/mahayukti-website"
    api_url = f"https://api.github.com/repos/{repo}/contents/images/{filename}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    for attempt in range(3):
        try:
            with open(filepath, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            check = requests.get(api_url, headers=headers, timeout=15)
            sha   = check.json().get("sha") if check.status_code == 200 else None
            payload = {"message": f"Image: {filename}", "content": encoded, "branch": "main"}
            if sha: payload["sha"] = sha
            r = requests.put(api_url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            url = f"https://mahayukti.com/images/{filename}"
            print(f"✅ Uploaded: {url}")
            return url
        except Exception as e:
            print(f"⚠️  Image upload attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                import time; time.sleep(5)
    print(f"⚠️  Image upload failed after 3 attempts — social posts will use local file where possible")
    return None

# ══════════════════════════════════════════════════════════════════════════
# STEP 4 — Update blog-data.json
# ══════════════════════════════════════════════════════════════════════════
def update_blog(content, image_filename):
    repo    = "vedantrungta1209/mahayukti-website"
    api_url = f"https://api.github.com/repos/{repo}/contents/blog-data.json"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    try:
        r        = requests.get(api_url, headers=headers, timeout=15); r.raise_for_status()
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
        blog_db["posts"] = blog_db["posts"][:180]

        updated = base64.b64encode(
            json.dumps(blog_db, indent=2, ensure_ascii=False).encode()
        ).decode()

        r2 = requests.put(api_url, headers=headers, timeout=30, json={
            "message": f"[{POST_TYPE.upper()}] {content['title']} [{DATE_STR}]",
            "content": updated, "sha": sha, "branch": "main"
        })
        r2.raise_for_status()
        print("✅ Blog updated → Cloudflare deploying...")
    except Exception as e:
        print(f"⚠️  Blog update failed (non-fatal): {e}")

# ══════════════════════════════════════════════════════════════════════════
# STEP 5 — Direct social posting (no Make.com)
# ══════════════════════════════════════════════════════════════════════════

_LI_HEADERS = lambda: {
    "Authorization":            f"Bearer {LINKEDIN_ACCESS_TOKEN}",
    "LinkedIn-Version":         "202310",
    "X-Restli-Protocol-Version":"2.0.0",
    "Content-Type":             "application/json",
}


def _upload_image_imgbb(image_path: str) -> str | None:
    """Upload image to imgbb and return public URL. Free, no account needed beyond API key."""
    if not IMGBB_API_KEY:
        return None
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": img_b64},
        timeout=30,
    )
    if r.ok:
        return r.json()["data"]["url"]
    print(f"  imgbb upload failed: {r.status_code} {r.text[:200]}")
    return None


def _post_linkedin_via_make(content: dict, image_url: str | None) -> bool:
    """Post to LinkedIn via Make.com webhook scenario."""
    if not MAKE_LINKEDIN_WEBHOOK_URL:
        return False
    payload = {
        "linkedin_text": content["linkedin_text"],
        "title":         content.get("title", ""),
        "image_url":     image_url or "",
    }
    r = requests.post(MAKE_LINKEDIN_WEBHOOK_URL, json=payload, timeout=30)
    if r.ok:
        print("✅ LinkedIn posted via Make.com webhook")
        return True
    print(f"⚠️  Make.com webhook failed ({r.status_code}): {r.text[:200]}")
    return False


def _post_linkedin_direct(content: dict, sq_path: str) -> bool:
    """Post to LinkedIn directly via REST API (requires approved app + valid token)."""
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_AUTHOR_URN:
        return False
    try:
        init = requests.post(
            "https://api.linkedin.com/rest/images?action=initializeUpload",
            headers=_LI_HEADERS(),
            json={"initializeUploadRequest": {"owner": LINKEDIN_AUTHOR_URN}},
        )
        init.raise_for_status()
        val        = init.json()["value"]
        upload_url = val["uploadUrl"]
        image_urn  = val["image"]

        with open(sq_path, "rb") as f:
            requests.put(
                upload_url, data=f,
                headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                         "Content-Type": "application/octet-stream"},
            ).raise_for_status()

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
        print("✅ LinkedIn posted via direct API")
        return True
    except Exception as e:
        print(f"⚠️  LinkedIn direct API failed: {e}")
        return False


def post_to_linkedin(content, sq_path, sq_cdn_url: str = ""):
    # Path 1: Make.com webhook (works while LinkedIn API app is under review)
    if MAKE_LINKEDIN_WEBHOOK_URL:
        # Use CDN URL directly if available (avoids needing IMGBB_API_KEY)
        image_url = sq_cdn_url or _upload_image_imgbb(sq_path)
        if _post_linkedin_via_make(content, image_url):
            return

    # Path 2: Direct LinkedIn REST API (once app is approved)
    if _post_linkedin_direct(content, sq_path):
        return

    print("⚠️  LinkedIn skipped — set MAKE_LINKEDIN_WEBHOOK_URL or LINKEDIN_ACCESS_TOKEN+LINKEDIN_AUTHOR_URN")


def post_to_facebook(content, sq_path_or_url):
    """Post photo to Facebook Page. Uploads binary directly — avoids Cloudflare URL blocks."""
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️  Facebook credentials missing — skipping")
        return

    import os as _os
    # Try binary upload first (most reliable — bypasses any CDN/bot-protection on the URL)
    local_path = sq_path_or_url if _os.path.exists(str(sq_path_or_url)) else None
    if not local_path:
        # sq_path_or_url is a CDN URL — derive the local /tmp path
        fname = sq_path_or_url.split("/")[-1]
        candidate = f"/tmp/{fname}"
        local_path = candidate if _os.path.exists(candidate) else None

    if local_path:
        # Compress to ≤800KB for Facebook's binary upload limit
        import io as _io
        img_obj = Image.open(local_path).convert("RGB")
        img_obj.thumbnail((1080, 1080), Image.LANCZOS)
        buf = _io.BytesIO()
        img_obj.save(buf, "JPEG", quality=82, optimize=True)
        buf.seek(0)
        r = requests.post(
            f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos",
            files={"source": ("photo.jpg", buf, "image/jpeg")},
            data={
                "caption":      content["facebook_text"],
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
        )
    else:
        # Fallback: URL-based (may fail if Cloudflare blocks Facebook's crawler)
        r = requests.post(
            f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos",
            data={
                "url":          sq_path_or_url,
                "caption":      content["facebook_text"],
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
        )

    if not r.ok:
        err = r.json().get("error", {}) if r.headers.get("content-type","").startswith("application/json") else {}
        print(f"⚠️  Facebook photo failed ({r.status_code}): code={err.get('code')} subcode={err.get('error_subcode')} msg={err.get('message', r.text[:200])}")
        return
    print("✅ Facebook photo posted")


def post_to_facebook_reel(content, reel_url):
    """Post reel to Facebook Page using the video_reels endpoint (v22.0+)."""
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️  Facebook credentials missing — skipping reel")
        return

    # Step 1: initialise upload session
    init = requests.post(
        f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/video_reels",
        data={
            "upload_phase":  "start",
            "access_token":  FB_PAGE_ACCESS_TOKEN,
        },
    )
    if not init.ok:
        err = init.json().get("error", {}) if init.headers.get("content-type","").startswith("application/json") else {}
        print(f"⚠️  Facebook Reel init failed ({init.status_code}): code={err.get('code')} msg={err.get('message', init.text[:200])}")
        # Fallback: legacy /videos with file_url
        r2 = requests.post(
            f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/videos",
            data={
                "file_url":     reel_url,
                "description":  content["facebook_text"],
                "published":    "true",
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
        )
        if r2.ok:
            print("✅ Facebook Reel posted (legacy endpoint)")
        else:
            err2 = r2.json().get("error", {}) if r2.headers.get("content-type","").startswith("application/json") else {}
            print(f"⚠️  Facebook Reel fallback also failed ({r2.status_code}): code={err2.get('code')} msg={err2.get('message', r2.text[:200])}")
        return

    video_id   = init.json().get("video_id")
    upload_url = init.json().get("upload_url")

    if not upload_url or not video_id:
        print(f"⚠️  Facebook Reel init returned unexpected response: {init.text[:200]}")
        return

    # Step 2: upload the video bytes
    try:
        vid_bytes = requests.get(reel_url, timeout=120).content
    except Exception as e:
        print(f"⚠️  Could not download reel for Facebook upload: {e}")
        return

    up = requests.post(
        upload_url,
        headers={
            "Authorization":   f"OAuth {FB_PAGE_ACCESS_TOKEN}",
            "offset":          "0",
            "file_size":       str(len(vid_bytes)),
        },
        data=vid_bytes,
        timeout=300,
    )
    if not up.ok:
        print(f"⚠️  Facebook Reel upload failed ({up.status_code}): {up.text[:200]}")
        return

    # Step 3: publish — description capped at 500 chars (Graph API errors on large payloads)
    reel_desc = content["facebook_text"][:500].strip()
    pub = requests.post(
        f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/video_reels",
        data={
            "video_id":     video_id,
            "upload_phase": "finish",
            "video_state":  "PUBLISHED",
            "description":  reel_desc,
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
    )
    if pub.ok:
        print("✅ Facebook Reel posted")
    else:
        err = pub.json().get("error", {}) if pub.headers.get("content-type","").startswith("application/json") else {}
        print(f"⚠️  Facebook Reel publish failed ({pub.status_code}): code={err.get('code')} msg={err.get('message', pub.text[:200])}")


def _ig_publish_with_retry(container_id, initial_wait=15, max_attempts=8, retry_wait=30):
    """Publish an IG container, retrying while it's still processing."""
    import time as _t
    _t.sleep(initial_wait)
    for attempt in range(max_attempts):
        pub = requests.post(
            f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media_publish",
            data={"creation_id": container_id, "access_token": FB_PAGE_ACCESS_TOKEN},
        )
        data = pub.json()
        if pub.status_code == 200:
            return
        err     = data.get("error", {})
        subcode = err.get("error_subcode")
        # 2207025 / 2207006 = container still processing — retry
        if subcode in (2207025, 2207006) and attempt < max_attempts - 1:
            print(f"   Container still processing (attempt {attempt+1}), retrying in {retry_wait}s…")
            _t.sleep(retry_wait)
            continue
        pub.raise_for_status()
    raise RuntimeError("Instagram container never became ready for publishing")


def post_to_instagram_image(content, sq_url):
    if not FB_PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("⚠️  Instagram credentials missing — skipping")
        return
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media",
        data={
            "image_url":    sq_url,
            "caption":      content["instagram_caption"],
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
    )
    r.raise_for_status()
    cid = r.json()["id"]
    _ig_publish_with_retry(cid, initial_wait=15, max_attempts=4, retry_wait=20)
    print("✅ Instagram image posted")


def post_to_instagram_reel(content, reel_url):
    if not FB_PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("⚠️  Instagram credentials missing — skipping reel")
        return
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media",
        data={
            "media_type":   "REELS",
            "video_url":    reel_url,
            "caption":      content["instagram_caption"],
            "access_token": FB_PAGE_ACCESS_TOKEN,
        },
    )
    r.raise_for_status()
    cid = r.json()["id"]
    # Reels take longer to process — start checking after 2 min, retry every 30s up to 8 min
    _ig_publish_with_retry(cid, initial_wait=120, max_attempts=12, retry_wait=30)
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
# X (Twitter)
# ══════════════════════════════════════════════════════════════════════════

def _x_oauth() -> "OAuth1 | None":
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        return None
    try:
        from requests_oauthlib import OAuth1
        return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    except ImportError:
        print("⚠️  requests-oauthlib not installed — X post skipped")
        return None


def _x_upload_media(image_path: str, auth) -> str | None:
    """Upload image via Twitter v1.1 media/upload and return media_id_string."""
    with open(image_path, "rb") as f:
        data = f.read()
    r = requests.post(
        "https://upload.twitter.com/1.1/media/upload.json",
        files={"media": data},
        auth=auth,
        timeout=60,
    )
    if r.ok:
        return r.json().get("media_id_string")
    print(f"  X media upload failed ({r.status_code}): {r.text[:200]}")
    return None


def post_to_twitter(content: dict, sq_path: str):
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        print("⚠️  X credentials missing — skipping")
        return
    auth = _x_oauth()
    if auth is None:
        return

    tweet_text = content.get("twitter_text", "")
    # Hard-trim to 280 chars as a safety net
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    payload: dict = {"text": tweet_text}

    media_id = _x_upload_media(sq_path, auth)
    if media_id:
        payload["media"] = {"media_ids": [media_id]}

    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
        auth=auth,
        timeout=30,
    )
    if r.ok:
        tweet_id = r.json().get("data", {}).get("id", "")
        print(f"✅ X posted: https://x.com/i/web/status/{tweet_id}")
    else:
        print(f"⚠️  X post failed ({r.status_code}): {r.text[:200]}")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    import time
    print(f"\n{'🌅' if POST_TYPE=='morning' else '🌆'} MahaYukti {POST_TYPE.upper()} Post — {DATE_STR}")
    print(f"🎯 Audience: {'Potential Clients' if POST_TYPE=='morning' else 'Member Enrolment'}")
    print(f"📌 Domain: {domain} → {subdomain}\n")

    # Claude with retry — transient API errors shouldn't kill the whole post
    content = None
    for attempt in range(3):
        try:
            content = generate_content()
            break
        except Exception as e:
            print(f"⚠️  Content generation attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                import time; time.sleep(10)
    if content is None:
        print("❌ Content generation failed after 3 attempts — aborting")
        sys.exit(1)

    # Landscape image — kept for blog thumbnail
    land_name = f"post-{POST_ID}-land.png"
    land_path = f"/tmp/{land_name}"
    try:
        generate_image(content, 1200, 627, land_path)
        upload_image(land_path, land_name)
    except Exception as e:
        print(f"⚠️  Landscape image failed (non-fatal): {e}")

    # Square JPEG — used for all social platforms
    sq_name = f"post-{POST_ID}-sq.jpg"
    sq_path = f"/tmp/{sq_name}"
    sq_url  = None
    try:
        generate_image(content, 1080, 1080, sq_path)
        sq_url = upload_image(sq_path, sq_name)
    except Exception as e:
        print(f"⚠️  Square image failed (non-fatal): {e}")

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
    # Telegram — fire-and-forget, no CDN wait needed (binary upload)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID:
        try:
            import sys as _sys; _sys.path.insert(0, str(Path(__file__).parent))
            from telegram_post import post_photo as tg_photo
            os.environ["TELEGRAM_BOT_TOKEN"]  = TELEGRAM_BOT_TOKEN
            os.environ["TELEGRAM_CHANNEL_ID"] = TELEGRAM_CHANNEL_ID
            tg_caption = f"<b>{content['title']}</b>\n\n{content['excerpt']}\n\nmahayukti.com"
            if sq_path and os.path.exists(sq_path):
                tg_photo(tg_caption, sq_path)
        except Exception as e:
            print(f"⚠️  Telegram failed (non-fatal): {e}")

    for name, fn, args in [
        ("LinkedIn",          post_to_linkedin,        (content, sq_path, sq_url)),
        ("Facebook photo",    post_to_facebook,        (content, sq_path)),   # binary upload — no CDN issues
        ("Facebook Reel",     post_to_facebook_reel,   (content, reel_url) if reel_url else None),
        ("Instagram image",   post_to_instagram_image, (content, sq_url)),
        ("Instagram Reel",    post_to_instagram_reel,  (content, reel_url) if reel_url else None),
        ("X (Twitter)",       post_to_twitter,         (content, sq_path)),
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
