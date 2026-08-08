#!/usr/bin/env python3
"""
MahaYukti X News Pulse — Hourly reactive posting
Monitors Indian news, Parliament, PM/President comms and posts balanced commentary.
Neither left nor right. India first. No political allegiance.
"""

import os, json, re, hashlib, datetime, requests, sys, xml.etree.ElementTree as ET
from pathlib import Path

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_SCRIPTS_DIR = Path(__file__).parent
_LOG_FILE    = _SCRIPTS_DIR / "x_news_pulse_log.json"
MAX_LOG      = 200   # keep last N posted story IDs
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
FOOTER_LINKS = [
    "\n\nFollow our journey: mahayukti.com",
    "\n\nConnect with India's experts: mahayukti.com",
    "\n\nIndia's vetted advisory network: mahayukti.com",
    "\n\nFor deep expertise on this and more: mahayukti.com",
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
    for s in stories:
        if s["id"] in seen:
            continue
        if s["score"] >= MIN_SCORE:
            return s
    return None


def _build_footer(story: dict, post_count: int) -> str:
    hashtags = " ".join(DOMAIN_HASHTAGS.get(story["domain"], ["#India", "#Bharat"])[:2])
    hashtags += " #Mahayukti"
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
You are a founding member of Mahayukti — an Indian professional who has spent years working across law, finance, technology and intelligence. You post on X as @wearemahayukti.

WHO YOU ARE:
A real person. Educated, well-read, deeply Indian. You care about this country the way someone does when they've watched it change up close. Not a journalist. Not an activist. Just someone who thinks carefully and speaks plainly.

HARD IDENTITY RULES — never break:
- No political party, politician, minister, or government officer is ever attacked or mocked. Ever.
- PM Modi, President Murmu, constitutional authorities — always respectful. Engage with their vision, not their politics.
- No religious, caste, or regional angle — ever.
- You are neither left nor right. You are Indian.
- Raise issues constructively. Never cynical, never despairing.

WHAT MAKES YOUR WRITING HUMAN — follow these exactly:
- VARY your length. Sometimes 4 sentences. Sometimes 600 words. Decide based on how much the story actually deserves.
- VARY your structure. Don't always open with "the bold observation." Sometimes start mid-thought. Sometimes start with a question. Sometimes just say what happened and why it matters.
- USE contractions. "isn't" not "is not". "we've" not "we have". "can't" not "cannot".
- WRITE like you're talking to a friend who is smart but hasn't read the story. Not a lecture. A conversation.
- HAVE a point of view. Not partisan — but don't be a weather report either. What do YOU think this means?
- OCCASIONALLY use "I" — "I've been watching this for a while", "I think what's being missed here is..."
- SHORT SENTENCES when something matters. Long sentences when you're building a thought.
- NO AI PHRASES — never use: "It's important to note", "In conclusion", "It is worth noting", "Let's delve", "Navigate", "Landscape", "In today's rapidly changing world", "Shed light", "Robust", "Tapestry", "Pivotal moment". These are instant AI giveaways.
- DON'T over-explain. Trust the reader.
- END naturally — not always with a call to action or a question. Sometimes just let the thought land.
- Mahayukti mention: weave it in only when it genuinely fits. Never as an ad. Sometimes skip it entirely.

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


def main():
    print(f"\n📡 MahaYukti News Pulse — {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    print("Fetching stories...")
    stories = fetch_stories()
    print(f"  {len(stories)} stories fetched, top score: {stories[0]['score'] if stories else 0}")

    seen = _load_log()
    post_count = len(seen)
    story = pick_story(stories, seen)

    if not story:
        print("✅ Nothing new worth posting right now — skipping.")
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


if __name__ == "__main__":
    main()
