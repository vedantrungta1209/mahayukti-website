#!/usr/bin/env python3
"""
MahaYukti Viral Thread Engine — runs 2× daily at peak India hours.
Fetches real-time trending hashtags from X, picks a hot India topic,
generates a 5-7 tweet tweetstorm, and posts it as a proper thread.

Threads are the #1 growth format on India X. Single posts die alone.
"""

import os, json, datetime, requests, time, re, xml.etree.ElementTree as ET
from pathlib import Path
from requests_oauthlib import OAuth1

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "x_viral_thread_log.json"
MAX_LOG   = 100

# ── Thread topic seeds — rotate + supplement with live news ────────────────
# These are evergreen angles that do well on India X regardless of news cycle
THREAD_SEEDS = [
    {
        "angle": "geopolitical",
        "prompt_seed": "India's strategic neighborhood — Pakistan, China, and the emerging trilateral alignments reshaping India's security calculus in 2026.",
    },
    {
        "angle": "economic",
        "prompt_seed": "India's manufacturing renaissance — how India is quietly replacing China in global supply chains and what sectors are leading the charge.",
    },
    {
        "angle": "parliament",
        "prompt_seed": "The Monsoon Session 2026 bills that will define India's next decade — Tribunal Reforms, FCRA Amendment, Delimitation. What each one actually means for citizens.",
    },
    {
        "angle": "tech",
        "prompt_seed": "India's digital public infrastructure — UPI, ONDC, DigiLocker, Aadhaar. Why this stack is a bigger geopolitical asset than most people realise.",
    },
    {
        "angle": "defence",
        "prompt_seed": "India's defence indigenisation push — Tejas Mk2, INS Vikrant, DRDO breakthroughs. What India's military-industrial complex looks like in 2026.",
    },
    {
        "angle": "economy_data",
        "prompt_seed": "India's GDP trajectory — specific milestone data points, manufacturing PMI, export figures, and what the 2047 Viksit Bharat numbers actually require.",
    },
    {
        "angle": "diplomacy",
        "prompt_seed": "India's Neighbourhood First 2.0 — how India's foreign policy has shifted from reactive to assertive in its immediate region.",
    },
]

NEWS_SOURCES = [
    ("PIB",            "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"),
    ("The Hindu",      "https://www.thehindu.com/news/national/feeder/default.rss"),
    ("TOI India",      "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"),
    ("Economic Times", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
    ("The Print",      "https://theprint.in/feed/"),
]


def _oauth():
    return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)


def _load_log() -> dict:
    if _LOG_FILE.exists():
        try:
            return json.loads(_LOG_FILE.read_text())
        except Exception:
            pass
    return {"threads_posted": [], "last_angle": ""}


def _save_log(log: dict):
    log["threads_posted"] = log["threads_posted"][-MAX_LOG:]
    _LOG_FILE.write_text(json.dumps(log))


def fetch_trending_hashtags() -> list[str]:
    """Get India trending topics via Google Trends RSS — zero X API credits."""
    try:
        r = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN",
            timeout=12, headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.ok:
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")
            india_kw = [
                "india", "bharat", "modi", "parliament", "sansad", "isro", "rbi",
                "rupee", "budget", "defence", "pakistan", "china", "viksit",
                "startup", "manufacturing", "digital", "monsoon",
            ]
            tags: list[str] = []
            for item in items[:30]:
                title = (item.findtext("title") or "").strip()
                if not title:
                    continue
                if any(kw in title.lower() for kw in india_kw):
                    tag = "#" + "".join(w.capitalize() for w in title.split()[:3])
                    tags.append(tag)
                if len(tags) >= 4:
                    break
            if tags:
                print(f"  Trending (Google): {tags}")
                return tags
    except Exception as e:
        print(f"  Trending fetch skipped: {e}")
    return []


def fetch_top_news() -> list[dict]:
    """Pull top 5 headlines from RSS for live context injection."""
    stories = []
    for name, url in NEWS_SOURCES:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(r.content)
            channel = root.find("channel")
            if channel is None:
                continue
            for item in channel.findall("item")[:2]:
                title = (item.findtext("title") or "").strip()
                if title:
                    stories.append({"source": name, "title": title})
        except Exception:
            continue
    return stories[:8]


def _pick_angle(log: dict) -> dict:
    """Pick the next thread angle, avoiding the last one used."""
    last = log.get("last_angle", "")
    for seed in THREAD_SEEDS:
        if seed["angle"] != last:
            return seed
    return THREAD_SEEDS[0]


def generate_thread(seed: dict, trending: list[str], news: list[dict]) -> list[str]:
    """Generate a 5-7 tweet tweetstorm. Returns list of tweet texts."""

    trending_str = ", ".join(trending[:5]) if trending else "#India #MonsoonSession2026"
    news_str = "\n".join(f"- [{s['source']}] {s['title']}" for s in news[:5])

    # Take top trending hashtags — don't over-filter, any trending tag gets discovery
    # Prefer India-relevant ones but fall back to top trending if none match
    india_hashtags = [h for h in trending if any(
        kw in h.lower() for kw in [
            "india", "bharat", "lok", "rajya", "modi", "parliament", "sansad",
            "monsoon", "session", "fcra", "viksit", "isro", "rbi", "rupee",
            "budget", "defence", "pakistan", "china", "amrit", "kaal",
            "startup", "digital", "make", "national", "independence",
        ]
    )]
    # Always have at least 3 hashtags — use trending if available, else topic defaults
    trending_tags = (india_hashtags[:2] or trending[:2] or [])
    topic_tags = {
        "geopolitical": ["#India", "#IndiaGeopolitics"],
        "economic":     ["#IndiaEconomy", "#ViksitBharat"],
        "parliament":   ["#MonsoonSession2026", "#LokSabha"],
        "tech":         ["#DigitalIndia", "#TechIndia"],
        "defence":      ["#IndiaDefence", "#MakeInIndia"],
        "economy_data": ["#IndiaGDP", "#ViksitBharat"],
        "diplomacy":    ["#IndiaForeignPolicy", "#India"],
    }.get(seed["angle"], ["#India", "#Bharat"])
    all_tags = list(dict.fromkeys(trending_tags + topic_tags))  # deduplicate, trending first
    # Distribute across thread: tweet1 gets 1, tweets 3+5 get 1 each, tweet6 gets 2
    tag1  = all_tags[0] if len(all_tags) > 0 else "#India"
    tag3  = all_tags[1] if len(all_tags) > 1 else "#Bharat"
    tag5  = all_tags[2] if len(all_tags) > 2 else "#ViksitBharat"
    tags6 = " ".join(all_tags[3:5]) if len(all_tags) > 3 else " ".join(all_tags[:2])
    if not tags6:
        tags6 = "#India #MakeIndiaGreatest"

    system = """\
You are a founding member of Mahayukti writing a viral tweetstorm as @wearemahayukti.
Movement: Make India Greatest. Passionate, data-driven, India-first.

HARD RULES:
- Never attack any politician, party, minister, or official. PM Modi, President Murmu — always respectful.
- No religious or caste angle. India is one.
- No partisan politics. Policy yes, parties no.
- Never cynical — always constructive and forward-looking.
- FACTUAL ACCURACY IS NON-NEGOTIABLE: Only cite facts you are highly confident about.
  Use well-known, widely-reported facts. For specific numbers (trade figures, weapons transfers,
  project counts) use approximate round figures or skip the number. NEVER fabricate statistics,
  weapon system names, or specific project counts. If unsure, say "significantly" not a made-up figure.

THREAD FORMAT (this is a tweetstorm, not a single post):
You must write a numbered thread of exactly 6 tweets.

Tweet 1 — THE HOOK (most important):
- The VERY FIRST SENTENCE must be a jaw-dropper that stops a scroll cold.
- Proven patterns:
  * Stark contrast: "[X in 2014]. [X in 2026]. That's not progress. That's a different country."
  * Counterintuitive: "Everyone reads [X] as [Y]. The real story is the opposite."
  * Uncomfortable truth: "India is the only [category] in the world doing [X]. And most people don't realise the full weight of that."
  * Incomplete reveal: "The [topic] shift nobody's connecting the dots on. Here's the full picture. 🧵"
- End with 🧵
- Include {tag1} somewhere in tweet 1

Tweets 2-5 — THE BODY:
- Tweet 2: The evidence. Concrete, verifiable, broad strokes (not made-up specifics).
- Tweet 3: The angle others miss. Include {tag3} at the end.
- Tweet 4: India's strategic response or opportunity.
- Tweet 5: The counterargument addressed + India's structural advantage. Include {tag5} at the end.
- Each tweet should stand alone if someone quotes it.
- Short punchy sentences. No filler.

Tweet 6 — THE CLOSE:
- Land the argument with a strong declarative statement, not a question.
- End with: {tags6}
- Do NOT use "Watch this space" or "The journey has just begun" or similar clichés.

FORMAT YOUR RESPONSE EXACTLY AS:
TWEET1: [text]
TWEET2: [text]
TWEET3: [text]
TWEET4: [text]
TWEET5: [text]
TWEET6: [text]

Each tweet must be under 280 characters. No exceptions."""

    prompt = f"""Write a viral tweetstorm thread on this angle:

TOPIC: {seed['prompt_seed']}

LIVE INDIA NEWS CONTEXT (weave in if relevant — only if confident the fact is accurate):
{news_str}

CURRENTLY TRENDING IN INDIA (context only):
{trending_str}

Hashtags to distribute across the thread as instructed: {tag1} {tag3} {tag5} {tags6}

Write the 6-tweet thread now. Make tweet 1's first sentence impossible to scroll past."""

    for attempt in range(2):
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":         ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type":      "application/json",
                },
                json={
                    "model":      "claude-sonnet-4-6",
                    "max_tokens":  2000,
                    "system":      system,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            r.raise_for_status()
            raw = r.json()["content"][0]["text"].strip()
            tweets = _parse_thread(raw)
            if tweets:
                return tweets
        except Exception as e:
            print(f"  Generation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(8)
    return []


def _parse_thread(raw: str) -> list[str]:
    """Parse TWEET1: ... TWEET6: ... format into a list."""
    tweets = []
    pattern = re.compile(r'TWEET\d+:\s*(.+?)(?=TWEET\d+:|$)', re.DOTALL)
    matches = pattern.findall(raw)
    for m in matches:
        text = m.strip()
        if len(text) > 280:
            text = text[:277] + "..."
        if text:
            tweets.append(text)
    return tweets


def post_thread(tweets: list[str]) -> bool:
    """Post a thread by replying each tweet to the previous one."""
    auth = _oauth()
    prev_id = None
    posted_ids = []

    for i, text in enumerate(tweets):
        payload = {"text": text}
        if prev_id:
            payload["reply"] = {"in_reply_to_tweet_id": prev_id}

        r = requests.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            auth=auth,
            timeout=30,
        )
        if r.ok:
            tweet_id = r.json().get("data", {}).get("id", "")
            print(f"  ✅ Tweet {i+1}/{len(tweets)}: https://x.com/wearemahayukti/status/{tweet_id}")
            prev_id = tweet_id
            posted_ids.append(tweet_id)
            if i < len(tweets) - 1:
                time.sleep(3)
        else:
            print(f"  ❌ Tweet {i+1} failed ({r.status_code}): {r.text[:300]}")
            # If even the first tweet fails, abort
            if i == 0:
                return False
            # Partial thread is still valuable — return True
            break

    return len(posted_ids) > 0


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n🔥 MahaYukti Viral Thread Engine — {now}")

    log = _load_log()

    print("\nFetching trending hashtags...")
    trending = fetch_trending_hashtags()

    print("Fetching top India news...")
    news = fetch_top_news()
    print(f"Found {len(news)} headlines")

    seed = _pick_angle(log)
    print(f"\nThread angle: [{seed['angle']}] {seed['prompt_seed'][:80]}...")

    print("\nGenerating thread...")
    tweets = generate_thread(seed, trending, news)

    if not tweets:
        print("❌ Thread generation failed")
        return

    print(f"\nThread preview ({len(tweets)} tweets):")
    for i, t in enumerate(tweets, 1):
        print(f"  {i}. ({len(t)} chars) {t[:120]}...")

    print("\nPosting thread...")
    if post_thread(tweets):
        log["last_angle"] = seed["angle"]
        log["threads_posted"].append({
            "angle":   seed["angle"],
            "time":    now,
            "preview": tweets[0][:100],
        })
        _save_log(log)
        print(f"\n✅ Thread posted — {len(tweets)} tweets live")
    else:
        print("\n❌ Thread posting failed")


if __name__ == "__main__":
    main()
