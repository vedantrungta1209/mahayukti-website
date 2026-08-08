#!/usr/bin/env python3
"""
MahaYukti Afternoon Geopolitical Awareness Post
Daily at 2 PM IST — Intelligence & Strategic Awareness series
"""

import os, json, datetime, requests, sys, base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
GH_TOKEN              = os.environ["GH_TOKEN"]
ONLY_PLATFORMS        = os.environ.get("ONLY_PLATFORMS", "")

MAKE_LINKEDIN_WEBHOOK_URL = os.environ.get("MAKE_LINKEDIN_WEBHOOK_URL", "")
LINKEDIN_ACCESS_TOKEN     = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN       = os.environ.get("LINKEDIN_AUTHOR_URN", "")
IMGBB_API_KEY             = os.environ.get("IMGBB_API_KEY", "")
FB_PAGE_ACCESS_TOKEN      = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID                = os.environ.get("FB_PAGE_ID", "")
IG_USER_ID                = os.environ.get("IG_USER_ID", "")
X_API_KEY                 = os.environ.get("X_API_KEY", "")
X_API_SECRET              = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN            = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET     = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

NAVY  = (11, 27, 58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (6, 15, 35)
RED   = (180, 30, 30)

TODAY    = datetime.date.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
POST_ID  = TODAY.strftime("%Y%m%d") + "_geo"

_SCRIPTS_DIR  = Path(__file__).parent
_COUNTER_FILE = _SCRIPTS_DIR / "topic_counter_geo.txt"

# ── Rotating themes (12-day cycle) ────────────────────────────────────────
GEO_THEMES = [
    {
        "name": "information_warfare",
        "title": "The War You Don't See",
        "angle": (
            "Information warfare: how narratives are engineered to make a population distrust its own "
            "institutions before any physical conflict begins. Cover: manufactured outrage, "
            "algorithmic amplification, AI-generated content, and how pattern-recognition is the "
            "citizen's best defence. Connect to Mahayukti's intelligence and geopolitical risk experts "
            "who advise on exactly this."
        ),
    },
    {
        "name": "economic_pressure",
        "title": "When the Economy Becomes a Weapon",
        "angle": (
            "Economic warfare: sanctions, currency attacks, supply chain disruption, and credit rating "
            "manipulation as instruments of geopolitical pressure. Show how pain is engineered and "
            "then blamed on the target government. Connect to Mahayukti's finance and intelligence "
            "professionals who read these patterns early."
        ),
    },
    {
        "name": "fault_line_exploitation",
        "title": "Every Nation Has Cracks",
        "angle": (
            "How external actors study and weaponise a nation's internal fault lines — religion, "
            "caste, language, region, class. The goal is not to create division but to deepen what "
            "already exists. Show how this has played out historically. Connect to Mahayukti's "
            "crisis management and intelligence experts who map and monitor these fault lines."
        ),
    },
    {
        "name": "institutional_capture",
        "title": "The Slow Hollowing of Institutions",
        "angle": (
            "Institutional capture: how courts, media, academia, and civil society can be gradually "
            "shifted — not through force but through funding, placement, and narrative. Show the "
            "difference between legitimate critique and coordinated delegitimisation. Connect to "
            "Mahayukti's legal, intelligence, and policy research professionals."
        ),
    },
    {
        "name": "proxy_actors",
        "title": "Who Funds the Voice You Trust?",
        "angle": (
            "Proxy actors in information warfare: activists, influencers, student groups, and NGOs "
            "that become — knowingly or unknowingly — amplifiers of foreign-directed narratives. "
            "Show how to identify the difference between organic dissent and orchestrated pressure. "
            "Connect to Mahayukti's corporate intelligence and OSINT professionals."
        ),
    },
    {
        "name": "cyber_warfare",
        "title": "The Battlefield Is Your Screen",
        "angle": (
            "Cyberattacks on critical infrastructure, state systems, and public institutions as "
            "a tool of geopolitical pressure. Cover: how cyber operations prepare the ground for "
            "political destabilisation. Connect to Mahayukti's cybersecurity experts — CISOs, "
            "incident responders, and threat intelligence analysts."
        ),
    },
    {
        "name": "border_proxy",
        "title": "Neighbours as Instruments",
        "angle": (
            "How adversaries use unstable neighbours, border provocations, and proxy conflicts to "
            "stretch a government's attention and resources. Show the coordinated nature of "
            "simultaneous pressure from multiple directions. Connect to Mahayukti's defence, "
            "geopolitical, and strategic affairs advisors."
        ),
    },
    {
        "name": "media_manipulation",
        "title": "The Story Is the Strategy",
        "angle": (
            "How international media can be used as an instrument of geopolitical pressure — "
            "selective amplification, decontextualised footage, coordinated framing of domestic "
            "events for foreign audiences. Show how India enters the 'global courtroom' without "
            "choosing to. Connect to Mahayukti's media intelligence and crisis communication experts."
        ),
    },
    {
        "name": "elite_fracture",
        "title": "When the Top Breaks First",
        "angle": (
            "Elite fracture: how a coordinated destabilisation effort targets senior officials, "
            "business leaders, and institution heads — resignations, defections, and 'preparing "
            "for after'. Show how this signals the final phase of a regime change operation. "
            "Connect to Mahayukti's corporate intelligence and crisis management professionals."
        ),
    },
    {
        "name": "morale_collapse",
        "title": "Making Defeat Feel Inevitable",
        "angle": (
            "Manufactured hopelessness: how populations are told their country is finished, their "
            "institutions are broken, and their only option is emigration or surrender. Show how "
            "this is a deliberate psychological operation — and how awareness is the antidote. "
            "Connect to Mahayukti as the network where India's strategic minds stay connected."
        ),
    },
    {
        "name": "historical_pattern",
        "title": "The Script Has Run Before",
        "angle": (
            "Historical case studies of regime change operations: the colour revolutions, the Arab "
            "Spring, and other documented playbooks. Show the common pattern across different "
            "countries, cultures, and decades. Connect to Mahayukti's geopolitical analysts and "
            "policy researchers who study these patterns professionally."
        ),
    },
    {
        "name": "citizens_defence",
        "title": "Pattern Recognition Is a Skill",
        "angle": (
            "What the aware citizen can actually do: media literacy, source verification, "
            "understanding funding trails, recognising coordinated inauthentic behaviour. "
            "Not paranoia — discipline. Show how Mahayukti's intelligence and research network "
            "exists precisely to give India's decision-makers and citizens access to this depth."
        ),
    },
]


def _get_theme():
    count = int(_COUNTER_FILE.read_text().strip()) if _COUNTER_FILE.exists() else 0
    _COUNTER_FILE.write_text(str(count + 1))
    return GEO_THEMES[count % len(GEO_THEMES)]


theme = _get_theme()


# ══════════════════════════════════════════════════════════════════════════
# STEP 1 — Generate content
# ══════════════════════════════════════════════════════════════════════════
def generate_content():
    print(f"Generating geo post | Theme: {theme['name']}")

    system = """\
You are a founding member of Mahayukti writing the daily strategic awareness post.
This series is part of the Make India Greatest movement — awareness that empowers, not fear that paralyzes.

THE SPIRIT:
India is rising. Our leaders are building. Our people are capable of extraordinary things.
But a strong India needs informed citizens who understand the world around them.
Every post should leave the reader feeling: I'm glad I know this. India has what it takes.
Warm. Positive in direction. Serious when it needs to be — never alarming.

WHO YOU ARE:
A real Indian. Educated, deeply read, genuinely passionate about this country.
Not a journalist filing a report. A fellow citizen sharing something worth knowing.

HARD RULES — never break:
- No political party, politician, minister, or government officer is attacked or named negatively. Ever.
- PM Modi, President Murmu, constitutional institutions — always respectful and constructive. Support their vision.
- No religious or caste framing. India is one.
- No speculation presented as fact.
- Positive in direction even when the topic is serious.

WRITING — what makes it human:
- Never use: "It's important to note", "Let's delve", "In today's world", "Navigate", "Landscape", "Tapestry", "Shed light", "Robust", "Pivotal", "In conclusion"
- Don't always open with THE bold statement. Vary it.
- Vary paragraph length. Don't explain everything — trust the reader.
- Contractions always. Short sentences when something matters.
- Mahayukti: mention when it genuinely fits — India's experts are in this network. Never an ad.

Respond ONLY with valid JSON. No markdown. No preamble.\
"""

    prompt = f"""Write today's strategic awareness post for Mahayukti.

Theme: {theme['title']}
What to cover: {theme['angle']}

Write each platform version in its own genuine voice — not the same content resized.
LinkedIn readers want depth. Instagram wants one sharp feeling. X wants a real human thought.
Facebook wants to feel like someone in your network shared something worth reading.

Cross-platform link strategy — follow this exactly:
- LinkedIn: end with mahayukti.com only. Professional audience, no social cross-links.
- Instagram: end with "Follow us on X @wearemahayukti | linkedin.com/company/mahayukti" — drive to stronger platforms.
- Facebook: end with "Find us on X @wearemahayukti | linkedin.com/company/mahayukti" — same logic.
- X: end with mahayukti.com or linkedin.com/company/mahayukti — rotate naturally.

Return this exact JSON:
{{
  "linkedin_text": "LinkedIn post 180-240 words. Conversational and real — like a smart colleague sharing something worth knowing. Short paragraphs, varied length. No bullet points. Specific India context. End with mahayukti.com. Max 2 hashtags.",
  "instagram_caption": "Instagram caption 70-90 words. One punchy hook. 3-4 short sentences — one clear thought, not a lecture. End with: Follow us on X @wearemahayukti | linkedin.com/company/mahayukti | mahayukti.com. 5-6 hashtags.",
  "facebook_text": "Facebook post 100-140 words. Feels like someone in your network shared something worth reading. Warm, grounded, not preachy. End with: Find us on X @wearemahayukti | linkedin.com/company/mahayukti | mahayukti.com.",
  "twitter_text": "X post — genuine thought, 200-600 chars (Premium long-form). Real and specific. End with mahayukti.com or linkedin.com/company/mahayukti — whichever fits. 1-2 hashtags max or none.",
  "image_headline": "5-6 words max. The one thing to remember. Not a tagline — a thought.",
  "image_subtext": "One line under 10 words. Specific, includes mahayukti.com"
}}"""

    import time as _t
    for attempt in range(5):
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 3000,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        if r.status_code in (429, 529) and attempt < 4:
            wait = 30 * (2 ** attempt)
            print(f"   API overloaded, retrying in {wait}s...")
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
    import re as _re
    m = _re.search(r'\{.*\}', raw, _re.DOTALL)
    if m:
        raw = m.group(0)
    content = json.loads(raw.strip())
    print("✅ Content generated")
    return content


# ══════════════════════════════════════════════════════════════════════════
# STEP 2 — Generate image
# ══════════════════════════════════════════════════════════════════════════
def generate_image(content, width, height, filepath):
    img = Image.new("RGB", (width, height), NAVY)
    draw = ImageDraw.Draw(img)

    # Dark gradient
    for y in range(height):
        t = y / height
        r = int(NAVY[0] + (DARK[0] - NAVY[0]) * t)
        g = int(NAVY[1] + (DARK[1] - NAVY[1]) * t)
        b = int(NAVY[2] + (DARK[2] - NAVY[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Brand bars — red accent for this series
    draw.rectangle([(0, 0), (width, 6)], fill=RED)
    draw.rectangle([(0, height - 6), (width, height)], fill=RED)
    draw.rectangle([(0, 0), (5, height)], fill=RED)

    def font(size, bold=False):
        paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        ]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default()

    # Header
    draw.rectangle([(0, 6), (width, int(height * 0.18))], fill=(6, 15, 35))
    draw.rectangle([(0, int(height * 0.18) - 3), (width, int(height * 0.18))], fill=RED)
    draw.text((40, int(height * 0.025)), "MAHAYUKTI", fill=GOLD, font=font(int(height * 0.04), bold=True))
    draw.text((40, int(height * 0.080)), "Strategic Intelligence Series", fill=LIGHT, font=font(int(height * 0.028)))

    # Series badge
    badge = "AWARENESS"
    b_font = font(int(height * 0.026), bold=True)
    b_bbox = draw.textbbox((0, 0), badge, font=b_font)
    bw, bh = b_bbox[2] - b_bbox[0] + 28, b_bbox[3] - b_bbox[1] + 14
    bx = width - 40 - bw
    by = int(height * 0.22)
    draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=bh // 2, fill=RED)
    draw.text((bx + 14, by + 7), badge, fill=WHITE, font=b_font)

    # Headline
    headline_text = content["image_headline"].upper()
    h_font = font(int(height * 0.082), bold=True)
    words = headline_text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=h_font)
        if bbox[2] - bbox[0] > width - 100 and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)

    y = int(height * 0.40)
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=h_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), ln, fill=(0, 0, 0), font=h_font)
        draw.text((x, y), ln, fill=WHITE, font=h_font)
        y += int(height * 0.105)

    # Red rule
    draw.rectangle([(width // 2 - 60, y + 12), (width // 2 + 60, y + 16)], fill=RED)
    y += 40

    # Subtext
    subtext = content["image_subtext"]
    s_font = font(int(height * 0.038))
    sub_words = subtext.split()
    sub_lines, sub_line = [], ""
    for word in sub_words:
        test = (sub_line + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=s_font)
        if bbox[2] - bbox[0] > width - 100 and sub_line:
            sub_lines.append(sub_line)
            sub_line = word
        else:
            sub_line = test
    if sub_line:
        sub_lines.append(sub_line)

    for ln in sub_lines:
        bbox = draw.textbbox((0, 0), ln, font=s_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), ln, fill=LIGHT, font=s_font)
        y += int(height * 0.060)

    # Footer
    footer_y = height - int(height * 0.06)
    draw.text((40, footer_y), "mahayukti.com", fill=GOLD, font=font(int(height * 0.030), bold=True))
    rb = draw.textbbox((0, 0), DATE_STR, font=font(int(height * 0.028)))
    draw.text((width - 40 - (rb[2] - rb[0]), footer_y), DATE_STR, fill=LIGHT, font=font(int(height * 0.028)))

    img.save(filepath, "JPEG", quality=95)
    print(f"✅ Image: {filepath}")


# ══════════════════════════════════════════════════════════════════════════
# STEP 3 — Upload image to GitHub CDN
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
            if sha:
                payload["sha"] = sha
            r = requests.put(api_url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            url = f"https://mahayukti.com/images/{filename}"
            print(f"✅ Uploaded: {url}")
            return url
        except Exception as e:
            print(f"⚠️  Upload attempt {attempt+1}/3: {e}")
            if attempt < 2:
                import time; time.sleep(5)
    return None


# ══════════════════════════════════════════════════════════════════════════
# STEP 4 — Post to platforms (reuse patterns from generate_and_post.py)
# ══════════════════════════════════════════════════════════════════════════
_LI_HEADERS = lambda: {
    "Authorization":             f"Bearer {LINKEDIN_ACCESS_TOKEN}",
    "LinkedIn-Version":          "202310",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type":              "application/json",
}


def post_to_linkedin(content, sq_path, sq_cdn_url=""):
    if MAKE_LINKEDIN_WEBHOOK_URL:
        image_url = sq_cdn_url or _upload_imgbb(sq_path)
        payload = {
            "linkedin_text": content["linkedin_text"],
            "title":         theme["title"],
            "image_url":     image_url or "",
        }
        r = requests.post(MAKE_LINKEDIN_WEBHOOK_URL, json=payload, timeout=30)
        if r.ok:
            print("✅ LinkedIn posted via Make.com")
            return
        print(f"⚠️  Make.com failed ({r.status_code}): {r.text[:200]}")
    print("⚠️  LinkedIn skipped — no credentials")


def _upload_imgbb(image_path):
    if not IMGBB_API_KEY:
        return None
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    r = requests.post("https://api.imgbb.com/1/upload",
                      data={"key": IMGBB_API_KEY, "image": img_b64}, timeout=30)
    return r.json()["data"]["url"] if r.ok else None


def post_to_facebook(content, sq_path):
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️  Facebook credentials missing — skipping")
        return
    import io as _io
    img_obj = Image.open(sq_path).convert("RGB")
    img_obj.thumbnail((1080, 1080), Image.LANCZOS)
    buf = _io.BytesIO()
    img_obj.save(buf, "JPEG", quality=82, optimize=True)
    buf.seek(0)
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos",
        files={"source": ("photo.jpg", buf, "image/jpeg")},
        data={"caption": content["facebook_text"], "access_token": FB_PAGE_ACCESS_TOKEN},
    )
    if r.ok:
        print("✅ Facebook posted")
    else:
        err = r.json().get("error", {}) if r.headers.get("content-type","").startswith("application/json") else {}
        print(f"⚠️  Facebook failed ({r.status_code}): {err.get('message', r.text[:200])}")


def _ig_publish_with_retry(container_id, initial_wait=15, max_attempts=6, retry_wait=20):
    import time as _t
    _t.sleep(initial_wait)
    for attempt in range(max_attempts):
        pub = requests.post(
            f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media_publish",
            data={"creation_id": container_id, "access_token": FB_PAGE_ACCESS_TOKEN},
        )
        if pub.status_code == 200:
            return
        subcode = pub.json().get("error", {}).get("error_subcode")
        if subcode in (2207025, 2207006) and attempt < max_attempts - 1:
            print(f"   IG container processing, retrying in {retry_wait}s...")
            _t.sleep(retry_wait)
            continue
        pub.raise_for_status()


def post_to_instagram(content, sq_url):
    if not FB_PAGE_ACCESS_TOKEN or not IG_USER_ID or not sq_url:
        print("⚠️  Instagram credentials/URL missing — skipping")
        return
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media",
        data={"image_url": sq_url, "caption": content["instagram_caption"],
              "access_token": FB_PAGE_ACCESS_TOKEN},
    )
    r.raise_for_status()
    cid = r.json()["id"]
    _ig_publish_with_retry(cid)
    print("✅ Instagram posted")


def post_to_twitter(content, sq_path):
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]):
        print("⚠️  X credentials missing — skipping")
        return
    try:
        from requests_oauthlib import OAuth1
    except ImportError:
        print("⚠️  requests-oauthlib not installed — skipping X")
        return
    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)

    tweet_text = content.get("twitter_text", "")
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    # Upload image
    media_id = None
    try:
        with open(sq_path, "rb") as f:
            r = requests.post("https://upload.twitter.com/1.1/media/upload.json",
                              files={"media": f}, auth=auth, timeout=60)
        if r.ok:
            media_id = r.json().get("media_id_string")
    except Exception as e:
        print(f"  X media upload failed: {e}")

    payload = {"text": tweet_text}
    if media_id:
        payload["media"] = {"media_ids": [media_id]}

    r = requests.post("https://api.twitter.com/2/tweets", json=payload, auth=auth, timeout=30)
    if r.ok:
        tweet_id = r.json().get("data", {}).get("id", "")
        print(f"✅ X posted: https://x.com/wearemahayukti/status/{tweet_id}")
    else:
        print(f"⚠️  X failed ({r.status_code}): {r.text[:200]}")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    import time
    print(f"\n🌐 MahaYukti Strategic Awareness Post — {DATE_STR}")
    print(f"📌 Theme: {theme['title']}\n")

    content = None
    for attempt in range(3):
        try:
            content = generate_content()
            break
        except Exception as e:
            print(f"⚠️  Content generation attempt {attempt+1}/3: {e}")
            if attempt < 2:
                time.sleep(10)
    if content is None:
        print("❌ Content generation failed — aborting")
        sys.exit(1)

    sq_name = f"geo-{POST_ID}-sq.jpg"
    sq_path = f"/tmp/{sq_name}"
    sq_url  = None
    try:
        generate_image(content, 1080, 1080, sq_path)
        sq_url = upload_image(sq_path, sq_name)
    except Exception as e:
        print(f"⚠️  Image failed (non-fatal): {e}")

    print("\n⏳ Waiting 120s for CDN propagation...")
    time.sleep(120)

    _only = [p.strip().lower() for p in ONLY_PLATFORMS.split(",") if p.strip()]
    print("\n📣 Posting..." + (f" (only: {', '.join(_only)})" if _only else ""))

    for name, fn, args in [
        ("LinkedIn",     post_to_linkedin,  (content, sq_path, sq_url)),
        ("Facebook",     post_to_facebook,  (content, sq_path)),
        ("Instagram",    post_to_instagram, (content, sq_url)),
        ("X (Twitter)",  post_to_twitter,   (content, sq_path)),
    ]:
        if _only and not any(p in name.lower() for p in _only):
            print(f"   {name}: skipped")
            continue
        try:
            fn(*args)
        except Exception as e:
            print(f"⚠️  {name} failed: {e}")

    print(f"\n✅ Done! '{theme['title']}'")


if __name__ == "__main__":
    main()
