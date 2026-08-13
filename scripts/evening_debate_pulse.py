#!/usr/bin/env python3
"""
MahaYukti Evening Debate Pulse — runs daily at 9 PM IST.
Reads what India is actually talking about at prime time (Google Trends + RSS),
picks the sharpest India-relevant topic, and posts one crisp take.
Captures debate-hour audience without partisan alignment.
"""

import os, json, datetime, requests, sys, xml.etree.ElementTree as ET
from pathlib import Path
from requests_oauthlib import OAuth1

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "evening_debate_log.json"
_DAILY    = _DIR / "evening_debate_daily.txt"
MAX_LOG   = 200

# Feeds checked at debate hour
DEBATE_HOUR_FEEDS = [
    # Google News — top India stories right now
    ("GoogleNews", "https://news.google.com/rss/search?q=india+breaking+news+today&hl=en-IN&gl=IN&ceid=IN:en"),
    ("GoogleNews", "https://news.google.com/rss/search?q=india+geopolitics+economy+security+2026&hl=en-IN&gl=IN&ceid=IN:en"),
    ("GoogleNews", "https://news.google.com/rss/search?q=india+pakistan+china+russia+US+today&hl=en-IN&gl=IN&ceid=IN:en"),
    # Wire services — freshest headlines
    ("NDTV",       "https://feeds.feedburner.com/ndtvnews-india-news"),
    ("ET",         "https://economictimes.indiatimes.com/rssfeeds/1977021501.cms"),
    ("Hindu",      "https://www.thehindu.com/news/national/feeder/default.rss"),
    # Google Trends India — what people are actually searching
    ("Trends",     "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN"),
]

# Topics that fit the Mahayukti India-first voice
INDIA_KEYWORDS = [
    "india", "bharat", "modi", "parliament", "supreme court", "rbi", "sebi",
    "rupee", "isro", "drdo", "defence", "border", "china", "pakistan",
    "economy", "gdp", "budget", "startup", "manufacturing", "election",
    "bilateral", "treaty", "sanctions", "geopolit", "diplomacy",
    "infrastructure", "highway", "railway", "port", "energy", "solar",
    "space", "missile", "navy", "army", "airforce", "security",
]

# Hard skip — partisan, tabloid, or off-brand
SKIP_TERMS = [
    "cricket", "ipl", "bollywood", "celebrity", "film", "actor", "actress",
    "rape", "murder", "accident", "flood", "earthquake",  # too tragedy-heavy for our voice
    "bjp", "congress", "aap", "aam aadmi", "sonia", "rahul",  # partisan
    "kejriwal", "yogi", "mamata",  # individual politicians
]


def _oauth():
    return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)


def _load_log() -> set:
    if _LOG_FILE.exists():
        try:
            return set(json.loads(_LOG_FILE.read_text()))
        except Exception:
            pass
    return set()


def _save_log(seen: set):
    _LOG_FILE.write_text(json.dumps(list(seen)[-MAX_LOG:]))


def _posted_today() -> bool:
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
    return _DAILY.exists() and _DAILY.read_text().strip() == today


def _mark_today():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
    _DAILY.write_text(today)


def fetch_topics() -> list[dict]:
    """Pull headlines + trends from all feeds, score and deduplicate."""
    seen_titles: set[str] = set()
    topics: list[dict] = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=6)

    for source, url in DEBATE_HOUR_FEEDS:
        try:
            r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0 (MahaYukti)"})
            if not r.ok:
                continue
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")
            for item in items[:15]:
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()[:200]
                tl    = title.lower()

                if not title or tl in seen_titles:
                    continue
                if any(s in tl for s in SKIP_TERMS):
                    continue

                score = sum(1 for kw in INDIA_KEYWORDS if kw in tl or kw in desc.lower())
                if score == 0:
                    continue

                seen_titles.add(tl)
                topics.append({"title": title, "desc": desc, "source": source, "score": score})
        except Exception as e:
            print(f"  Feed error ({source}): {e}")

    topics.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Fetched {len(topics)} India-relevant topics")
    return topics[:15]


def fetch_trending_tags() -> list[str]:
    """Google Trends India — used as hashtag signal, not for riding partisan tags."""
    try:
        r = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN",
            timeout=10, headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.ok:
            root  = ET.fromstring(r.content)
            tags  = []
            for item in root.findall(".//item")[:20]:
                title = (item.findtext("title") or "").strip()
                tl    = title.lower()
                if any(kw in tl for kw in INDIA_KEYWORDS) and not any(s in tl for s in SKIP_TERMS):
                    tag = "#" + "".join(w.capitalize() for w in title.split()[:3])
                    tags.append(tag)
                if len(tags) >= 2:
                    break
            return tags
    except Exception:
        pass
    return []


def generate_post(topics: list[dict], trending_tags: list[str], seen: set) -> tuple[str, str]:
    """Ask Claude to pick the sharpest topic and write one debate-hour post."""
    topic_block = "\n".join(
        f"{i+1}. [{t['source']}] {t['title']}" + (f" — {t['desc'][:100]}" if t['desc'] else "")
        for i, t in enumerate(topics)
    )
    tags_hint = " ".join(trending_tags) if trending_tags else "#India #IndiaRising"

    already = list(seen)[-5:]
    already_block = ("\n\nRECENTLY POSTED (avoid these topics):\n" + "\n".join(f"- {t}" for t in already)) if already else ""

    system = """\
You are a sharp, credible India analyst posting as @wearemahayukti at 9 PM IST — prime debate hour.
Mission: Make India Greatest. India-first, constructive, non-partisan.

HARD RULES:
- Never name any politician, party, or minister — not even positively
- No religious, caste, or regional framing
- Never cynical — always forward-looking and constructive
- Do NOT ride Arnab/Republic/NDTV specific hashtags — use topic hashtags
- Sound like a sharp Indian who reads deeply — not a TV anchor

DEBATE-HOUR STYLE:
- 200-240 characters of sharp substance + hashtags
- Take ONE clear position — not a summary, a TAKE
- Specific: name a number, a country, a policy, a consequence
- The kind of post someone shares while watching the debate
- Contractions: "isn't", "India's", "we've"
- AVOID: "Great!", "Indeed", "Important", "Crucial"
- One emoji max — skip if forced
- END with 2-3 hashtags: always #India + 1-2 topic-specific
  Pool: #India #Bharat #ViksitBharat #IndiaRising #IndiaEconomy #IndiaDefence
        #IndiaGeopolitics #MakeIndiaGreatest #ISRO #IndiaFirst #IndiaLeads

OUTPUT: Return JSON with two keys:
{
  "topic_id": "first 40 chars of the headline you chose",
  "post": "the post text including hashtags"
}"""

    prompt = f"""India's top stories at 9 PM tonight:\n\n{topic_block}{already_block}

Trending signals (for context only, do NOT use these exact tags): {tags_hint}

Pick the ONE topic that will resonate most with an India-first, policy-aware audience at debate hour.
Write a sharp, confident take. 200-240 chars + 2-3 hashtags."""

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
                    "max_tokens": 300,
                    "system":     system,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            raw  = r.json()["content"][0]["text"].strip()
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(raw[start:end+1])
                return data.get("post", "").strip(), data.get("topic_id", "unknown")
        except Exception as e:
            print(f"  Generation attempt {attempt+1} failed: {e}")
            import time; time.sleep(5)
    return "", ""


def post_tweet(text: str) -> bool:
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text[:280]},
        auth=_oauth(),
        timeout=30,
    )
    if r.ok:
        tid = r.json().get("data", {}).get("id", "")
        print(f"  ✅ Posted: https://x.com/wearemahayukti/status/{tid}")
        return True
    print(f"  ❌ Failed ({r.status_code}): {r.text[:300]}")
    return False


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n🔥 MahaYukti Evening Debate Pulse — {now}")

    if _posted_today():
        print("⏸️  Already posted today — skipping.")
        return

    topics = fetch_topics()
    if not topics:
        print("⚠️  No India-relevant topics found — skipping.")
        return

    trending = fetch_trending_tags()
    seen = _load_log()

    post_text, topic_id = generate_post(topics, trending, seen)
    if not post_text:
        print("❌ Generation failed.")
        return

    print(f"\n→ Topic: {topic_id}")
    print(f"  Post ({len(post_text)} chars): {post_text}")

    if post_tweet(post_text):
        seen.add(topic_id)
        _save_log(seen)
        _mark_today()

        # Cross-post to LinkedIn via Make.com webhook (non-fatal)
        make_url = os.environ.get("MAKE_WEBHOOK_URL", "")
        if make_url:
            try:
                li_text = (
                    f"Tonight's take:\n\n"
                    f"{post_text.split('#')[0].strip()}\n\n"
                    f"— @wearemahayukti | India's geopolitical reality, decoded.\n\n"
                    f"#India #IndiaFirst #HybridWarfare #NationalSecurity #Mahayukti"
                )
                r = requests.post(make_url, json={"content": li_text[:3000]}, timeout=15)
                print(f"  LinkedIn: {'✅ posted' if r.ok else f'⚠️ failed ({r.status_code})'}")
            except Exception as e:
                print(f"  LinkedIn: ⚠️ {e}")

        print("✅ Done")


if __name__ == "__main__":
    main()
