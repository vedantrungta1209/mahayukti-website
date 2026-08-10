#!/usr/bin/env python3
"""
MahaYukti X News Pulse — Hourly reactive posting
Monitors Indian news, Parliament, PM/President comms and posts balanced commentary.
Neither left nor right. India first. No political allegiance.
"""

import os, json, re, hashlib, datetime, requests, sys, xml.etree.ElementTree as ET
from pathlib import Path
from requests_oauthlib import OAuth1

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID   = os.environ.get("TELEGRAM_CHANNEL_ID", "")

_SCRIPTS_DIR   = Path(__file__).parent
_LOG_FILE      = _SCRIPTS_DIR / "x_news_pulse_log.json"
_HEARTBEAT     = _SCRIPTS_DIR / "x_news_pulse_heartbeat.txt"
MAX_LOG        = 200   # keep last N posted story IDs
MIN_SCORE    = 6     # minimum relevance score to post
MAX_AGE_HRS  = 3     # only consider stories from last N hours

# ── News sources ───────────────────────────────────────────────────────────
SOURCES = [
    # Wire services
    ("ANI",             "https://www.aninews.in/rss/"),
    ("NDTV Top",        "https://feeds.feedburner.com/ndtvnews-top-stories"),
    ("NDTV India",      "https://feeds.feedburner.com/ndtvnews-india-news"),
    # National newspapers
    ("The Hindu",       "https://www.thehindu.com/news/national/feeder/default.rss"),
    ("TOI India",       "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"),
    ("HT India",        "https://www.hindustantimes.com/rss/india/rssfeed.xml"),
    ("The Print",       "https://theprint.in/feed/"),
    ("Indian Express",  "https://indianexpress.com/section/india/feed/"),
    # TV channels
    ("Republic World",  "https://www.republicworld.com/rss.xml"),
    ("India TV",        "https://www.indiatvnews.com/rss.xml"),
    ("Zee News",        "https://zeenews.india.com/rss/india-national-news.xml"),
    # Business
    ("Economic Times",  "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
    ("Mint",            "https://www.livemint.com/rss/news"),
    # Government / Parliament
    ("PIB",             "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"),
    ("PMO India",       "https://www.pmindia.gov.in/en/feed/"),
    ("PRS India",       "https://prsindia.org/feed"),
]

# ── Relevance scoring keywords ─────────────────────────────────────────────
HIGH_WEIGHT = [
    "parliament", "lok sabha", "rajya sabha", "sansad", "session",
    "pm modi", "prime minister", "president murmu", "president of india",
    "pmo", "cabinet", "supreme court", "india", "bharat",
    "economy", "gdp", "inflation", "rbi", "rupee",
    "border", "security", "defence", "army", "navy", "air force",
    "china", "pakistan", "geopolitics", "diplomacy",
    "bill passed", "amendment", "legislation", "budget",
    "cyber", "digital india", "startup india", "make in india",
    "infrastructure", "highway", "railway", "airport",
    "health", "education", "agriculture", "farmer",
    "election commission", "constitutional",
]
MED_WEIGHT = [
    "government", "minister", "policy", "scheme", "yojana",
    "rupees", "crore", "investment", "foreign", "trade",
    "state", "chief minister", "high court", "tribunal",
    "technology", "space", "isro", "drdo", "startup",
    "protest", "strike", "demand", "reform",
]
LOW_WEIGHT = [
    # hyper-local or entertainment — downgrade
    "bollywood", "cricket score", "ipl", "celebrity", "wedding",
    "accident", "fire", "flood local", "murder",
]

# ── Domain hashtags ───────────────────────────────────────────────────────
DOMAIN_HASHTAGS = {
    "legal":       ["#LokSabha", "#IndiaLaw", "#Parliament"],
    "finance":     ["#IndiaEconomy", "#Budget", "#RBI"],
    "technology":  ["#DigitalIndia", "#TechIndia", "#ISRO"],
    "security":    ["#NationalSecurity", "#IndiaDefence"],
    "geopolitics": ["#IndiaFirst", "#Geopolitics", "#BharatMatters"],
    "crisis":      ["#IndiaResilient", "#CrisisManagement"],
    "governance":  ["#GoodGovernance", "#NewIndia", "#Bharat"],
}

# ── Handles to tag by domain (official/verified only — no politicians) ─────
DOMAIN_HANDLES = {
    "legal":       ["@LokSabhaSectt", "@RajyaSabha", "@SupremeCourtofIndia"],
    "finance":     ["@RBI", "@FinMinIndia", "@PIB_India"],
    "technology":  ["@isro", "@MeitY_India", "@_DPIIT"],
    "security":    ["@SpokespersonMoD", "@PIB_India"],
    "geopolitics": ["@MEAIndia", "@PIB_India"],
    "crisis":      ["@NDRFHQ", "@PIB_India"],
    "governance":  ["@PMOIndia", "@rashtrapatibhvn", "@PIB_India"],
}

# ── Cross-post footer (rotates) ────────────────────────────────────────────
LINKEDIN_URL  = "linkedin.com/company/mahayukti"
INSTAGRAM_URL = "instagram.com/mahayukti.advisory"
FACEBOOK_URL  = "facebook.com/MahaYuktiAdvisory"
WEBSITE_URL   = "mahayukti.com"

FOOTER_LINKS = [
    f"\n\nJoin the movement: {WEBSITE_URL}",
    f"\n\nFollow us on LinkedIn: {LINKEDIN_URL}",
    f"\n\nIndia's expert network: {WEBSITE_URL} | LinkedIn: {LINKEDIN_URL}",
    f"\n\nConnect with India's best: {WEBSITE_URL}",
    f"\n\nFollow our journey: {LINKEDIN_URL}",
    f"\n\nFind us on Instagram: {INSTAGRAM_URL}",
    f"\n\nFind us on Facebook: {FACEBOOK_URL}",
    f"\n\n{WEBSITE_URL} | Instagram: {INSTAGRAM_URL} | Facebook: {FACEBOOK_URL}",
]

# ── Mahayukti domain tags ──────────────────────────────────────────────────
DOMAIN_MAP = {
    "legal":       ["supreme court", "high court", "tribunal", "law", "bill", "legislation", "judiciary", "constitutional", "lok sabha", "rajya sabha", "parliament"],
    "finance":     ["rbi", "gdp", "economy", "budget", "rupee", "inflation", "bank", "nbfc", "sebi", "investment", "market", "sensex", "nifty"],
    "technology":  ["digital", "isro", "ai", "startup", "cyber", "5g", "tech", "software", "space", "drdo"],
    "security":    ["border", "army", "navy", "air force", "defence", "terror", "cyber attack", "intelligence", "security"],
    "geopolitics": ["china", "pakistan", "diplomacy", "foreign", "g20", "united nations", "sanctions", "geopolit"],
    "crisis":      ["crisis", "disaster", "flood", "earthquake", "emergency", "pandemic", "outbreak"],
    "governance":  ["pm modi", "prime minister", "president", "cabinet", "pmo", "scheme", "policy", "yojana"],
}


def _score_story(title: str, desc: str) -> tuple[int, str]:
    text = (title + " " + desc).lower()
    score = 0
    for kw in HIGH_WEIGHT:
        if kw in text:
            score += 3
    for kw in MED_WEIGHT:
        if kw in text:
            score += 1
    for kw in LOW_WEIGHT:
        if kw in text:
            score -= 4

    domain = "governance"
    for d, keywords in DOMAIN_MAP.items():
        if any(kw in text for kw in keywords):
            domain = d
            break
    return score, domain


def _parse_date(date_str: str) -> datetime.datetime | None:
    if not date_str:
        return None
    fmts = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return None


def _story_id(title: str, link: str) -> str:
    return hashlib.md5((title + link).encode()).hexdigest()[:12]


def _load_log() -> set:
    if _LOG_FILE.exists():
        try:
            return set(json.loads(_LOG_FILE.read_text()))
        except Exception:
            pass
    return set()


def _save_log(seen: set):
    items = list(seen)[-MAX_LOG:]
    _LOG_FILE.write_text(json.dumps(items))


def fetch_stories() -> list[dict]:
    stories = []
    cutoff  = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=MAX_AGE_HRS)

    for source_name, url in SOURCES:
        try:
            r = requests.get(url, timeout=12, headers={"User-Agent": "MahaYuktiBot/1.0"})
            if not r.ok:
                continue
            root = ET.fromstring(r.content)
            ns   = {"atom": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)
            for item in items[:8]:
                def txt(tag):
                    el = item.find(tag)
                    return (el.text or "").strip() if el is not None else ""

                title = txt("title") or txt("atom:title")
                link  = txt("link")  or txt("atom:id")
                desc  = re.sub(r"<[^>]+>", "", txt("description") or txt("atom:summary"))
                date  = txt("pubDate") or txt("atom:published") or txt("atom:updated")

                if not title:
                    continue

                pub = _parse_date(date)
                if pub and pub < cutoff:
                    continue

                score, domain = _score_story(title, desc)
                stories.append({
                    "id":      _story_id(title, link),
                    "source":  source_name,
                    "title":   title,
                    "desc":    desc[:300],
                    "link":    link,
                    "score":   score,
                    "domain":  domain,
                    "pub":     date,
                })
        except Exception as e:
            print(f"  [{source_name}] fetch failed: {e}")
            continue

    stories.sort(key=lambda s: s["score"], reverse=True)
    return stories


def pick_story(stories: list[dict], seen: set) -> dict | None:
    # First pass: fresh story above relevance threshold
    for s in stories:
        if s["id"] not in seen and s["score"] >= MIN_SCORE:
            return s
    # Fallback: best unposted story regardless of score (never skip a run)
    for s in stories:
        if s["id"] not in seen:
            print(f"  ⚠️  No high-score story found — falling back to best available (score: {s['score']})")
            return s
    # All fetched stories already posted — temporarily lower age window and rescan
    print("  ⚠️  All recent stories already posted — picking least-recently-seen story as backup")
    if stories:
        return stories[0]
    return None


_TRENDING_CACHE: list[str] = []
_TRENDING_FETCHED_AT: datetime.datetime | None = None

def _fetch_trending_hashtags() -> list[str]:
    """Get real-time trending hashtags for India. Cached for 1h per process."""
    global _TRENDING_CACHE, _TRENDING_FETCHED_AT
    now = datetime.datetime.now(datetime.timezone.utc)
    if _TRENDING_FETCHED_AT and (now - _TRENDING_FETCHED_AT).seconds < 3600 and _TRENDING_CACHE:
        return _TRENDING_CACHE
    try:
        auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
        r = requests.get(
            "https://api.twitter.com/1.1/trends/place.json",
            params={"id": 23424848},  # India WOEID
            auth=auth, timeout=10,
        )
        if r.ok:
            trends = r.json()[0].get("trends", [])
            tags = [t["name"] for t in trends if t["name"].startswith("#")]
            # Prefer India-relevant tags but always return something
            india_tags = [h for h in tags if any(
                kw in h.lower() for kw in [
                    "india", "bharat", "modi", "lok", "rajya", "parliament", "sansad",
                    "session", "fcra", "viksit", "isro", "rbi", "defence", "amrit",
                    "pakistan", "china", "startup", "budget", "rupee", "monsoon",
                    "national", "independence", "digital", "make", "swachh",
                ]
            )]
            result = india_tags[:2] if india_tags else tags[:2]
            _TRENDING_CACHE = result
            _TRENDING_FETCHED_AT = now
            print(f"  Trending tags: {result}")
            return result
    except Exception as e:
        print(f"  Trending fetch skipped: {e}")
    return []


def _build_footer(story: dict, post_count: int) -> str:
    domain_tags = DOMAIN_HASHTAGS.get(story["domain"], ["#India", "#Bharat"])[:2]
    trending    = _fetch_trending_hashtags()
    # 1 trending tag + 2 domain tags, always at least 3 hashtags total
    combined = list(dict.fromkeys(trending[:1] + domain_tags + ["#India"]))[:3]
    hashtags = " ".join(combined) + " #Mahayukti"
    handles  = DOMAIN_HANDLES.get(story["domain"], [])
    handle_str = " ".join(handles[:2]) if handles else ""
    footer_link = FOOTER_LINKS[post_count % len(FOOTER_LINKS)]
    parts = [footer_link]
    if handle_str:
        parts.append(f"\n{handle_str}")
    parts.append(f"\n{hashtags}")
    return "".join(parts)


def generate_post(story: dict, post_count: int = 0) -> str:
    system = """\
You are a founding member of Mahayukti posting on X as @wearemahayukti.
You're part of a movement — Make India Greatest. Positive. Energising. Deeply Indian.

THE SPIRIT:
India is rising. Every post should reinforce that feeling — not through empty cheerleading, but through genuine insight that makes the reader feel informed, proud, and connected to something bigger.
You support India's leaders and their vision. You bring people in — the student, the entrepreneur, the professional, the curious citizen. You speak to the masses, not just the elite.
Make people want to share this. Make them feel: I'm glad I follow this account.

WHO YOU ARE:
A real Indian. Well-read, passionate about this country, genuinely invested in its future.
Not a reporter summarising news. A fellow citizen reacting to it honestly.

HARD RULES — never break:
- No political party, politician, minister, or official is attacked or mocked. Ever.
- PM Modi, President Murmu, constitutional institutions — always respectful. Engage with vision, not politics.
- No religious, caste, or regional angle. India is one.
- Constructive always. Never cynical. Never despairing.

THE FIRST LINE IS EVERYTHING:
X is a scroll. You have 0.3 seconds. If the first line doesn't stop the thumb, nobody reads the rest.
Proven first-line patterns:
- Data bomb: "India just crossed [X]. It took China [Y] years. It took us [Z]."
- Counterintuitive: "Everyone is calling [X] a [Y]. They're looking at it wrong."
- Incomplete tension: "The [topic] story isn't about [obvious thing]. It's about [hidden thing]."
- Stark contrast: "[Situation in 2014]. [Situation now]. That's not [word]. That's [stronger word]."
NEVER start with: "India's", "The government", "Today", "Breaking", "Important update", or any news-anchor opener.

WRITING — what makes it human and shareable:
- VARY length. Sometimes 3 punchy sentences. Sometimes 500 words. Match what the story deserves.
- VARY structure. Sometimes mid-thought. Sometimes a question. Sometimes just a sharp reaction.
- USE contractions. "isn't", "we've", "can't" — always.
- HAVE a point of view. Not partisan, but not a weather report either.
- OCCASIONALLY use "I" — it makes it human.
- SHORT SENTENCES when something matters. Long ones when building.
- NEVER: "It's important to note", "In conclusion", "Let's delve", "Navigate", "Landscape", "Robust", "Tapestry", "Shed light", "Pivotal", "In today's world". Instant AI giveaways.
- DON'T over-explain. Trust the reader.
- END with a statement, not always a question.
- Mahayukti: only when it genuinely fits. Never as an ad.

Respond with ONLY the post text. Nothing else.\
"""

    prompt = f"""React to this news story as @wearemahayukti:

Source: {story['source']}
Headline: {story['title']}
Context: {story['desc']}
Domain: {story['domain']}

Write what a sharp, genuine Indian would actually say about this — not a summary, not a lesson. A real take."""

    footer = _build_footer(story, post_count)

    for attempt in range(3):
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1500,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            r.raise_for_status()
            body = r.json()["content"][0]["text"].strip()
            return body + footer
        except Exception as e:
            print(f"  Generation attempt {attempt+1}/3 failed: {e}")
            if attempt < 2:
                import time; time.sleep(10)
    return ""


def post_to_x(text: str) -> bool:
    try:
        from requests_oauthlib import OAuth1
    except ImportError:
        print("❌ requests-oauthlib not installed")
        return False

    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text},
        auth=auth,
        timeout=30,
    )
    if r.ok:
        tweet_id = r.json().get("data", {}).get("id", "")
        print(f"✅ Posted: https://x.com/wearemahayukti/status/{tweet_id}")
        return True
    print(f"❌ X post failed ({r.status_code}): {r.text[:300]}")
    return False


def _write_heartbeat():
    """Write current UTC timestamp so the guardian can detect stale runs."""
    _HEARTBEAT.write_text(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))


def main():
    print(f"\n📡 MahaYukti News Pulse — {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    print("Fetching stories...")
    stories = fetch_stories()
    print(f"  {len(stories)} stories fetched, top score: {stories[0]['score'] if stories else 0}")

    seen = _load_log()
    post_count = len(seen)
    story = pick_story(stories, seen)

    _write_heartbeat()

    if not story:
        print("⚠️  No stories fetched at all (RSS outage?) — skipping this run.")
        sys.exit(0)

    print(f"\n📰 Selected: [{story['source']}] {story['title']} (score: {story['score']}, domain: {story['domain']})")

    text = generate_post(story, post_count)
    if not text:
        print("❌ Content generation failed — skipping.")
        sys.exit(1)

    print(f"\nPost preview ({len(text)} chars):\n{text[:500]}{'...' if len(text) > 500 else ''}\n")

    if post_to_x(text):
        seen.add(story["id"])
        _save_log(seen)
        # Mirror to Telegram (plain text, no image)
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID:
            try:
                import sys as _sys; _sys.path.insert(0, str(Path(__file__).parent))
                from telegram_post import post_text as tg_text
                tg_text(text[:4096])
            except Exception as e:
                print(f"⚠️  Telegram mirror failed (non-fatal): {e}")


if __name__ == "__main__":
    main()
