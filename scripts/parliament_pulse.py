#!/usr/bin/env python3
"""
MahaYukti Parliament Pulse — runs every 2h during session hours (9AM–7PM IST).
Monitors official Sansad/government handles and high-engagement media accounts.
Quote-tweets with constructive India-first commentary.
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
MAX_PER_RUN = 2

# Official government and Sansad handles — always priority
OFFICIAL_HANDLES = [
    "PIB_India", "mpa_india", "LokSabhaSectt", "SansadTV",
    "MEAIndia", "PMOIndia", "rashtrapatibhvn", "MIB_India",
]

# High-reach media handles for parliament coverage
MEDIA_HANDLES = [
    "ANI", "ndtv", "TOIIndiaNews", "HTTweets", "IndianExpress",
    "the_hindu", "ZeeNews", "republic", "DDNewslive",
]

SESSION_CONTEXT = """\
India Parliament Monsoon Session 2026 (July 20 – August 13, 2026).
Bills in focus: Tribunal Reforms Bill, Mines & Minerals (D&R) Amendment,
Kerala (Alteration of Name) Bill, Bankers' Books Evidence Bill,
FCRA Amendment Bill (debate Aug 12), Delimitation Bill.
Session is in its final days — high legislative intensity.
Mahayukti believes: strong democratic institutions + legislative ambition = India's greatest decade ahead.
"""


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


def _search(query: str, sort_by_recency: bool = False) -> list[dict]:
    auth = _oauth()
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
            "followers":  user.get("public_metrics", {}).get("followers_count", 0),
            "likes":      metrics.get("like_count", 0),
            "retweets":   metrics.get("retweet_count", 0),
            "created_at": t.get("created_at", ""),
        })

    if sort_by_recency:
        results.sort(key=lambda x: x["created_at"], reverse=True)
    else:
        results.sort(key=lambda x: x["likes"] + x["retweets"] * 2, reverse=True)
    return results


def get_official_tweets() -> list[dict]:
    query = "(" + " OR ".join(f"from:{h}" for h in OFFICIAL_HANDLES) + ") -is:retweet lang:en"
    return _search(query, sort_by_recency=True)


def get_media_parliament_tweets() -> list[dict]:
    handles_q = " OR ".join(f"from:{h}" for h in MEDIA_HANDLES)
    query = f"({handles_q}) (parliament OR \"lok sabha\" OR \"rajya sabha\" OR \"monsoon session\" OR #MonsoonSession2026) -is:retweet lang:en"
    return _search(query, sort_by_recency=False)


def generate_commentary(tweet: dict, is_official: bool) -> str:
    source_type = "official government/Sansad account" if is_official else "media account"
    system = f"""\
You are a founding member of Mahayukti posting on X as @wearemahayukti.
Movement: "Make India Greatest" — positive, constructive, India-first.

Parliament context:
{SESSION_CONTEXT}

HARD RULES:
- Never attack any politician, party, minister, or official
- PM Modi, President Murmu, Lok Sabha Speaker Om Birla, Rajya Sabha Chairman — always respectful
- No religious or caste angle
- Never cynical — always constructive and forward-looking
- Frame through India 2047 lens: what does this bill/development mean long-term?

STYLE (this will be a quote-tweet of a {source_type}):
- Max 230 characters (tweet attachment uses extra space)
- Add genuine insight or historical/policy context — not cheerleading
- Can use 1-2 hashtags from: #MonsoonSession2026 #LokSabha #RajyaSabha #ViksitBharat #India2047 #FCRABill
- Sound like a sharp, well-read Indian policy analyst
- NEVER start with "Great", "Important", "Crucial", "Key"
- Contractions are fine; don't be stiff

Respond with ONLY the commentary text. Nothing else."""

    prompt = f"""Quote-tweet this post from @{tweet['username']}:

"{tweet['text']}"

Add insight or context specific to this. Frame through India's long-term development. Under 230 chars."""

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
                    "max_tokens":  120,
                    "system":      system,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"].strip().strip('"')
            if len(text) > 260:
                text = text[:257] + "..."
            return text
        except Exception as e:
            print(f"  Commentary generation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(5)
    return ""


def post_quote_tweet(tweet_id: str, text: str) -> bool:
    auth = _oauth()
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text, "quote_tweet_id": tweet_id},
        auth=auth,
        timeout=30,
    )
    if r.ok:
        new_id = r.json().get("data", {}).get("id", "")
        print(f"  ✅ Quote-tweeted: https://x.com/wearemahayukti/status/{new_id}")
        return True
    print(f"  ❌ Quote-tweet failed ({r.status_code}): {r.text[:300]}")
    return False


def _process_batch(tweets: list[dict], seen: set, posted: int, is_official: bool, min_likes: int = 0) -> tuple[set, int]:
    for tweet in tweets:
        if posted >= MAX_PER_RUN:
            break
        if tweet["id"] in seen:
            continue
        if tweet["username"].lower() == "wearemahayukti":
            continue
        if tweet["likes"] < min_likes:
            continue

        print(f"\n→ @{tweet['username']} ({tweet['likes']} likes): {tweet['text'][:100]}...")
        commentary = generate_commentary(tweet, is_official=is_official)
        if not commentary:
            continue
        print(f"  Commentary: {commentary}")
        if post_quote_tweet(tweet["id"], commentary):
            seen.add(tweet["id"])
            posted += 1
            time.sleep(10)

    return seen, posted


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n🏛️  MahaYukti Parliament Pulse — {now}")

    seen   = _load_log()
    posted = 0

    # Priority 1: Official government/Sansad handles (no min_likes — authority matters more than engagement)
    print("\nSearching official government/Sansad handles...")
    official = get_official_tweets()
    print(f"Found {len(official)} official tweets")
    seen, posted = _process_batch(official, seen, posted, is_official=True, min_likes=0)

    # Priority 2: High-engagement media parliament tweets
    if posted < MAX_PER_RUN:
        print("\nSearching media parliament coverage...")
        media = get_media_parliament_tweets()
        print(f"Found {len(media)} media tweets")
        seen, posted = _process_batch(media, seen, posted, is_official=False, min_likes=15)

    _save_log(seen)
    print(f"\n✅ Done — {posted} quote-tweet{'s' if posted != 1 else ''} posted")
    if posted == 0:
        print("  (no new tweets to quote this run)")


if __name__ == "__main__":
    main()
