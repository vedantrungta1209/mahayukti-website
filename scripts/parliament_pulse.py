#!/usr/bin/env python3
"""
MahaYukti Parliament Pulse — runs every 2h during session hours (9AM–7PM IST).
Monitors official Sansad/govt handles for live events, then posts ORIGINAL
commentary tweets (not replies/QTs — new account restriction on both).
Original posts get full impressions vs buried replies.
"""

import os, json, datetime, requests, time
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
    "#TribunalReformsBill", "#MakeIndiGreatest",
]


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


def _search_handles(handles: list[str], extra_filter: str = "", sort_by_recency: bool = True) -> list[dict]:
    auth = _oauth()
    handles_q = " OR ".join(f"from:{h}" for h in handles)
    query = f"({handles_q}) {extra_filter} -is:retweet lang:en".strip()

    r = requests.get(
        "https://api.twitter.com/2/tweets/search/recent",
        params={
            "query":        query,
            "max_results":  15,
            "tweet.fields": "public_metrics,author_id,created_at,text",
            "expansions":   "author_id",
            "user.fields":  "username,public_metrics",
        },
        auth=auth,
        timeout=30,
    )
    if not r.ok:
        print(f"  Search failed ({r.status_code}): {r.text[:300]}")
        return []

    data   = r.json()
    tweets = data.get("data", [])
    users  = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

    results = []
    for t in tweets:
        uid     = t.get("author_id", "")
        user    = users.get(uid, {})
        metrics = t.get("public_metrics", {})
        results.append({
            "id":         t["id"],
            "text":       t["text"],
            "username":   user.get("username", ""),
            "likes":      metrics.get("like_count", 0),
            "retweets":   metrics.get("retweet_count", 0),
            "created_at": t.get("created_at", ""),
        })

    if sort_by_recency:
        results.sort(key=lambda x: x["created_at"], reverse=True)
    else:
        results.sort(key=lambda x: x["likes"] + x["retweets"] * 2, reverse=True)
    return results


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
- This is a standalone original tweet (280 chars max)
- Must read as YOUR original perspective, not a news summary
- Frame through India 2047 / long-term development lens
- Sharp, specific, well-read Indian analyst voice — not PR bot
- NEVER start with: "Great", "Important", "Crucial", "Today", "Breaking"
- Can use 1-2 hashtags from: {' '.join(HASHTAG_POOL)}
- One relevant emoji max (skip if forced)
- Contractions are fine; don't be stiff
- Make it punchy enough to stop a scroll

Respond with ONLY the tweet text. Nothing else."""

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

    # Gather live context from official handles
    print("\nFetching official handle tweets...")
    official = _search_handles(OFFICIAL_HANDLES, sort_by_recency=True)
    print(f"Found {len(official)} official tweets")

    # Also grab media parliament coverage for added context
    print("Fetching media parliament coverage...")
    media = _search_handles(
        MEDIA_HANDLES,
        extra_filter='(parliament OR "lok sabha" OR "rajya sabha" OR monsoon)',
        sort_by_recency=False,
    )
    print(f"Found {len(media)} media tweets")

    # Combine: official first (freshest), media by engagement
    source_pool = official[:8] + media[:4]

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
