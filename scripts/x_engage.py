#!/usr/bin/env python3
"""
MahaYukti X Engagement Loop — runs every 3 hours.
News discovery: free RSS feeds + Claude API (zero X API read credits).
Posting: X API write only.
"""

import os, json, datetime, requests, time, xml.etree.ElementTree as ET
from pathlib import Path

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "x_engage_log.json"
MAX_LOG        = 500
POSTS_PER_RUN  = 2   # posts per 3-hour run = ~16/day
MAX_AGE_HOURS  = 18  # ignore articles older than this

# Free RSS feeds — no API key, no credits
RSS_FEEDS = [
    # Major Indian news
    "https://feeds.feedburner.com/ndtvnews-india-news",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://economictimes.indiatimes.com/rssfeeds/1977021501.cms",
    # Government / official
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
    # Google News topic clusters (free, no key)
    "https://news.google.com/rss/search?q=india+defence+military+ISRO&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+economy+RBI+budget+manufacturing&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+china+pakistan+geopolitics+diplomacy&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=viksit+bharat+make+in+india+PLI+startup&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=Jaishankar+MEA+india+foreign+policy&hl=en-IN&gl=IN&ceid=IN:en",
]

SKIP_DOMAINS = ["thewire.in", "scroll.in", "theprint.in/opinion"]


def _oauth():
    from requests_oauthlib import OAuth1
    return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)


def _load_log() -> dict:
    if _LOG_FILE.exists():
        try:
            data = json.loads(_LOG_FILE.read_text())
            if isinstance(data, dict):
                return data
            # Old format was a bare list of tweet IDs — discard, start fresh
        except Exception:
            pass
    return {"posted_urls": [], "posted_texts": []}


def _save_log(log: dict):
    log["posted_urls"]  = log["posted_urls"][-MAX_LOG:]
    log["posted_texts"] = log["posted_texts"][-MAX_LOG:]
    _LOG_FILE.write_text(json.dumps(log))


def _parse_rfc2822(date_str: str):
    """Parse RSS pubDate to datetime (best-effort)."""
    import email.utils
    try:
        return datetime.datetime(*email.utils.parsedate(date_str)[:6],
                                  tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def fetch_headlines() -> list[dict]:
    """Pull recent headlines from all RSS feeds."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=MAX_AGE_HOURS)
    seen_titles: set[str] = set()
    articles: list[dict] = []

    for url in RSS_FEEDS:
        try:
            r = requests.get(url, timeout=12,
                             headers={"User-Agent": "Mozilla/5.0 (Mahayukti RSS reader)"})
            if not r.ok:
                print(f"  RSS {url[:60]}... → {r.status_code}")
                continue
            root = ET.fromstring(r.content)
            ns   = {"atom": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)
            for item in items:
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link")  or "").strip()
                desc  = (item.findtext("description") or "").strip()
                pub   = item.findtext("pubDate") or item.findtext("atom:published", namespaces=ns) or ""

                if not title or title.lower() in seen_titles:
                    continue
                if any(d in link for d in SKIP_DOMAINS):
                    continue

                pub_dt = _parse_rfc2822(pub)
                if pub_dt and pub_dt < cutoff:
                    continue

                seen_titles.add(title.lower())
                articles.append({
                    "title": title,
                    "link":  link,
                    "desc":  desc[:300],
                    "pub":   pub,
                })
        except Exception as e:
            print(f"  RSS error ({url[:60]}...): {e}")

    print(f"  Fetched {len(articles)} fresh headlines from RSS")
    return articles


def generate_posts(articles: list[dict], n: int, already_posted: list[str]) -> list[str]:
    """Ask Claude to pick n engaging topics and write one post each."""
    if not articles:
        return []

    headline_block = "\n".join(
        f"{i+1}. {a['title']}" + (f" — {a['desc'][:120]}" if a['desc'] else "")
        for i, a in enumerate(articles[:40])
    )

    posted_block = ""
    if already_posted:
        posted_block = "\n\nALREADY POSTED TODAY (do not repeat these topics):\n" + \
                       "\n".join(f"- {t}" for t in already_posted[-10:])

    system = """\
You are a sharp India analyst posting as @wearemahayukti on X.
Mission: Make India Greatest. India-first, constructive, globally literate.

HARD RULES:
- Never attack any politician, party, minister, or official by name
- PM Modi, President Murmu, constitutional bodies — always respectful
- No religious, caste, or communal angle
- Never cynical or despairing — always forward-looking
- Sound like a credible, well-read Indian — not a PR bot

POST STYLE (each post must follow this exactly):
- 200-230 characters of substance + hashtags at the end
- Take a clear position or add a specific insight — not just restating the headline
- Add a number, comparison, or forward-looking point when the topic allows
- Contractions: "isn't", "we've", "India's"
- AVOID: "Great!", "Indeed", "Absolutely", "Well said", "Impressive"
- One emoji max if it adds energy — skip otherwise
- MANDATORY: End with exactly 2-3 hashtags. Always #India + 1-2 topic-specific.
  Pool: #India #Bharat #ViksitBharat #IndiaRising #IndiaEconomy #IndiaDefence
        #DigitalIndia #IndiaGeopolitics #MakeIndiaGreatest #ISRO #MakeInIndia
        #IndiaManufacturing #IndiaFirst #IndiaLeads #Sansad

OUTPUT FORMAT — return ONLY a JSON array of strings, one per post, no commentary:
["post text here", "post text here"]"""

    prompt = f"""Here are today's top India headlines:\n\n{headline_block}{posted_block}

Pick the {n} most engaging topics for an India-forward audience.
Write one sharp, original post for each — NOT just the headline reworded.
Return as a JSON array of {n} strings."""

    for attempt in range(2):
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":           ANTHROPIC_API_KEY,
                    "anthropic-version":   "2023-06-01",
                    "content-type":        "application/json",
                },
                json={
                    "model":      "claude-sonnet-4-6",
                    "max_tokens": 600,
                    "system":     system,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            raw = r.json()["content"][0]["text"].strip()
            # Extract JSON array even if Claude wraps it in markdown
            start, end = raw.find("["), raw.rfind("]")
            if start != -1 and end != -1:
                posts = json.loads(raw[start:end+1])
                return [p.strip().strip('"')[:280] for p in posts if p.strip()]
        except Exception as e:
            print(f"  Generation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(5)
    return []


def post_tweet(text: str) -> bool:
    """Post as standalone original tweet — X write API only."""
    auth = _oauth()
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text},
        auth=auth,
        timeout=30,
    )
    if r.ok:
        new_id = r.json().get("data", {}).get("id", "")
        print(f"  ✅ Posted: https://x.com/wearemahayukti/status/{new_id}")
        return True
    print(f"  ❌ Post failed ({r.status_code}): {r.text[:300]}")
    return False


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n📰 MahaYukti X Engagement — {now}")
    print("  [News via RSS — zero X read credits used]")

    log = _load_log()

    articles = fetch_headlines()
    if not articles:
        print("  No fresh headlines found — exiting")
        return

    posts = generate_posts(articles, POSTS_PER_RUN, log["posted_texts"])
    if not posts:
        print("  No posts generated — exiting")
        return

    posted = 0
    for text in posts:
        if text in log["posted_texts"]:
            print(f"  Skipping duplicate post")
            continue
        print(f"\n→ ({len(text)} chars): {text}")
        if post_tweet(text):
            log["posted_texts"].append(text)
            posted += 1
            time.sleep(10)

    _save_log(log)
    print(f"\n✅ Done — {posted} post{'s' if posted != 1 else ''} published")


if __name__ == "__main__":
    main()
