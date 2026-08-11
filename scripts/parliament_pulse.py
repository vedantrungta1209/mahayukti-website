#!/usr/bin/env python3
"""
MahaYukti Parliament Pulse — runs every 2h during session hours (9AM–7PM IST).
Monitors official Sansad/govt handles for live events, then posts ORIGINAL
commentary tweets (not replies/QTs — new account restriction on both).
Original posts get full impressions vs buried replies.
"""

import os, json, datetime, requests, time, xml.etree.ElementTree as ET
from pathlib import Path

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "parliament_pulse_log.json"
MAX_LOG   = 300
MAX_PER_RUN = 1   # 1 original post per 2h run — quality over volume

OFFICIAL_HANDLES = [
    "PIB_India", "mpa_india", "LokSabhaSectt", "SansadTV",
    "MEAIndia", "PMOIndia", "rashtrapatibhvn", "MIB_India",
]

MEDIA_HANDLES = [
    "ANI", "ndtv", "TOIIndiaNews", "HTTweets", "IndianExpress",
    "the_hindu", "ZeeNews", "republic", "DDNewslive",
]

SESSION_CONTEXT = """\
India Parliament Monsoon Session 2026 (July 20 – August 13, 2026) — final days.
Bills passed/in-progress: Tribunals Reforms Bill (just passed Lok Sabha today),
Mines & Minerals (D&R) Amendment, Kerala (Alteration of Name) Bill,
Bankers' Books Evidence Bill, FCRA Amendment Bill (debate Aug 12),
Delimitation Bill.
Mahayukti believes: strong democratic institutions + legislative ambition = India's greatest decade.
"""

HASHTAG_POOL = [
    "#MonsoonSession2026", "#LokSabha", "#RajyaSabha",
    "#ViksitBharat", "#India2047", "#FCRABill",
    "#TribunalReformsBill", "#MakeIndiaGreatest", "#India", "#Bharat",
]

ALWAYS_HASHTAGS = "#MonsoonSession2026 #India"  # guaranteed in every parliament post


def _oauth():
    from requests_oauthlib import OAuth1
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


PARLIAMENT_RSS_FEEDS = [
    # Official government press releases
    ("PIB",        "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"),
    # Google News: parliament + legislation
    ("GoogleNews", "https://news.google.com/rss/search?q=india+parliament+lok+sabha+rajya+sabha+bill&hl=en-IN&gl=IN&ceid=IN:en"),
    # Google News: India governance & policy
    ("GoogleNews", "https://news.google.com/rss/search?q=india+government+policy+legislation+2026&hl=en-IN&gl=IN&ceid=IN:en"),
]

def _fetch_parliament_news() -> list[dict]:
    """Fetch latest parliament/governance headlines via free RSS — zero X credits."""
    cutoff  = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12)
    seen_t: set[str] = set()
    articles: list[dict] = []

    for source, url in PARLIAMENT_RSS_FEEDS:
        try:
            r = requests.get(url, timeout=12,
                             headers={"User-Agent": "Mozilla/5.0 (Mahayukti)"})
            if not r.ok:
                continue
            root  = ET.fromstring(r.content)
            items = root.findall(".//item")
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                if not title or title.lower() in seen_t:
                    continue
                seen_t.add(title.lower())
                articles.append({
                    "id":       title[:40],   # fingerprint for dedup
                    "text":     f"{title}. {desc[:200]}".strip(),
                    "username": source,
                    "likes":    0,
                    "retweets": 0,
                    "created_at": "",
                })
        except Exception as e:
            print(f"  RSS error ({source}): {e}")

    print(f"  Fetched {len(articles)} parliament/governance headlines via RSS")
    return articles[:12]


def generate_original_post(source_tweets: list[dict]) -> str:
    """Generate a standalone original tweet informed by live parliament events."""
    context_snippets = "\n".join(
        f"- @{t['username']}: {t['text'][:200]}"
        for t in source_tweets[:5]
    )

    system = f"""\
You are a founding member of Mahayukti posting on X as @wearemahayukti.
Movement: "Make India Greatest" — positive, constructive, India-first.

Parliament context:
{SESSION_CONTEXT}

HARD RULES:
- Never attack any politician, party, minister, official, or party by name
- PM Modi, President Murmu, Lok Sabha Speaker, Rajya Sabha Chairman — always respectful
- No religious or caste angle
- Never cynical — always constructive and forward-looking
- Do NOT directly quote or attribute the source tweets — write as original thought

POST STYLE:
- This is a standalone original tweet (max 260 chars so hashtags fit)
- Must read as YOUR original perspective, not a news summary
- Frame through India 2047 / long-term development lens
- Sharp, specific, well-read Indian analyst voice — not PR bot
- NEVER start with: "Great", "Important", "Crucial", "Today", "Breaking"
- One relevant emoji max (skip if forced)
- Contractions are fine; don't be stiff
- Make it punchy enough to stop a scroll
- MANDATORY: End the tweet with exactly: {ALWAYS_HASHTAGS}
  You may also add 1 more relevant hashtag from: {' '.join(HASHTAG_POOL[:6])}

Respond with ONLY the tweet text (including the mandatory hashtags). Nothing else."""

    prompt = f"""These are live parliament/India events happening right now:

{context_snippets}

Write ONE original tweet (your own voice and perspective) informed by these events.
Frame it around what this means for India's future. Under 280 chars."""

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
                    "max_tokens":  150,
                    "system":      system,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"].strip().strip('"')
            if len(text) > 280:
                text = text[:277] + "..."
            return text
        except Exception as e:
            print(f"  Generation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(5)
    return ""


def post_tweet(text: str) -> bool:
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


def _make_batch_key(tweets: list[dict]) -> str:
    """Fingerprint a batch of source tweets so we don't re-generate for same content."""
    ids = sorted(t["id"] for t in tweets[:5])
    return "batch_" + "_".join(ids)


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n🏛️  MahaYukti Parliament Pulse — {now}")

    seen = _load_log()

    # Gather live parliament/governance context via RSS (zero X read credits)
    print("\nFetching parliament headlines via RSS...")
    source_pool = _fetch_parliament_news()

    if not source_pool:
        print("No source tweets found — skipping this run")
        _save_log(seen)
        return

    batch_key = _make_batch_key(source_pool)
    if batch_key in seen:
        print("Same parliament events as last run — skipping to avoid repetition")
        _save_log(seen)
        return

    print(f"\nGenerating original post from {len(source_pool)} source tweets...")
    tweet_text = generate_original_post(source_pool)
    if not tweet_text:
        print("Generation failed")
        _save_log(seen)
        return

    print(f"  Post ({len(tweet_text)} chars): {tweet_text}")
    if post_tweet(tweet_text):
        seen.add(batch_key)

    _save_log(seen)
    print("\n✅ Done")


if __name__ == "__main__":
    main()
