#!/usr/bin/env python3
"""
MahaYukti X Engagement Loop — runs every 3 hours.
Finds high-relevance India tweets, generates a sharp reply, posts it.
Builds organic reach without paid promotion.
"""

import os, json, hashlib, datetime, requests, sys, time
from pathlib import Path

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "x_engage_log.json"
MAX_LOG   = 500
MAX_REPLIES_PER_RUN = 2     # stay within reasonable rate limits
MIN_LIKES           = 5     # only reply to tweets with some traction

# Search queries — rotate so we cover different topics each run
SEARCH_QUERIES = [
    '(parliament OR "lok sabha" OR "rajya sabha" OR sansad) lang:en -is:retweet -is:reply',
    '("pm modi" OR "prime minister india" OR PMOIndia) lang:en -is:retweet -is:reply',
    '("india economy" OR "india gdp" OR "rbi india" OR "budget india") lang:en -is:retweet -is:reply',
    '(ISRO OR "india defence" OR "india security" OR "make in india") lang:en -is:retweet -is:reply',
    '("india china" OR "india pakistan" OR "india diplomacy" OR "india geopolit") lang:en -is:retweet -is:reply',
    '("digital india" OR "india startup" OR "india tech" OR "india infrastructure") lang:en -is:retweet -is:reply',
    '("india 2047" OR "amrit kaal" OR "viksit bharat" OR "new india") lang:en -is:retweet -is:reply',
]

# Never reply to these (political parties, divisive handles)
BLOCKED_TERMS = [
    "bjp", "congress", "aap party", "aam aadmi party",
    "opposition", "ruling party", "anti-modi", "anti-india",
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


def _pick_query(seen: set) -> str:
    # Rotate through queries based on current hour
    hour = datetime.datetime.now(datetime.timezone.utc).hour
    return SEARCH_QUERIES[hour % len(SEARCH_QUERIES)]


def search_tweets(query: str) -> list[dict]:
    auth = _oauth()
    r = requests.get(
        "https://api.twitter.com/2/tweets/search/recent",
        params={
            "query":       query,
            "max_results": 20,
            "tweet.fields": "public_metrics,author_id,created_at,text",
            "expansions":  "author_id",
            "user.fields": "username,verified,public_metrics",
        },
        auth=auth,
        timeout=30,
    )
    if not r.ok:
        print(f"  Search failed ({r.status_code}): {r.text[:300]}")
        return []

    data  = r.json()
    tweets = data.get("data", [])
    users  = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

    results = []
    for t in tweets:
        uid     = t.get("author_id", "")
        user    = users.get(uid, {})
        metrics = t.get("public_metrics", {})
        results.append({
            "id":       t["id"],
            "text":     t["text"],
            "username": user.get("username", ""),
            "likes":    metrics.get("like_count", 0),
            "retweets": metrics.get("retweet_count", 0),
            "replies":  metrics.get("reply_count", 0),
        })

    results.sort(key=lambda x: x["likes"] + x["retweets"] * 2, reverse=True)
    return results


def _is_safe(tweet: dict) -> bool:
    text_lower = tweet["text"].lower()
    handle_lower = tweet["username"].lower()
    # Skip our own tweets
    if handle_lower == "wearemahayukti":
        return False
    # Skip tweets with party/divisive terms
    if any(b in text_lower or b in handle_lower for b in BLOCKED_TERMS):
        return False
    # Skip low-engagement tweets
    if tweet["likes"] < MIN_LIKES:
        return False
    return True


def generate_reply(tweet: dict) -> str:
    system = """\
You are a founding member of Mahayukti replying on X as @wearemahayukti.
Movement: Make India Greatest. Positive, warm, India-first.

HARD RULES:
- Never attack any politician, party, minister, or official
- PM Modi, President Murmu, constitutional bodies — always respectful
- No religious or caste angle
- Never cynical or despairing — always constructive
- Do not promote Mahayukti unless it genuinely fits
- Sound like a real, well-read Indian — not a brand bot

REPLY STYLE:
- Max 200 characters (this is a reply, not a thread)
- Direct, specific to what they said — not generic
- Add perspective, not just agreement
- Contractions: "isn't", "we've", "can't"
- NEVER: "Great point!", "Indeed", "Absolutely", "Totally agree", "Well said"
- No hashtags in replies (looks spammy)
- No emojis unless one genuinely fits

Respond with ONLY the reply text. Nothing else."""

    prompt = f"""Reply to this tweet by @{tweet['username']}:

"{tweet['text']}"

Add genuine perspective. Be specific to what they said. Under 200 chars."""

    for attempt in range(2):
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
                    "max_tokens": 100,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"].strip().strip('"')
            if len(text) > 250:
                text = text[:247] + "..."
            return text
        except Exception as e:
            print(f"  Reply generation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(5)
    return ""


def post_reply(tweet_id: str, reply_text: str) -> bool:
    auth = _oauth()
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={
            "text":  reply_text,
            "reply": {"in_reply_to_tweet_id": tweet_id},
        },
        auth=auth,
        timeout=30,
    )
    if r.ok:
        new_id = r.json().get("data", {}).get("id", "")
        print(f"  ✅ Replied: https://x.com/wearemahayukti/status/{new_id}")
        return True
    print(f"  ❌ Reply failed ({r.status_code}): {r.text[:300]}")
    return False


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n💬 MahaYukti X Engagement — {now}")

    seen   = _load_log()
    query  = _pick_query(seen)
    print(f"Query: {query}")

    tweets = search_tweets(query)
    print(f"Found {len(tweets)} tweets")

    replied = 0
    for tweet in tweets:
        if replied >= MAX_REPLIES_PER_RUN:
            break
        if tweet["id"] in seen:
            continue
        if not _is_safe(tweet):
            continue

        print(f"\n→ @{tweet['username']} ({tweet['likes']} likes): {tweet['text'][:100]}...")
        reply = generate_reply(tweet)
        if not reply:
            continue

        print(f"  Reply ({len(reply)} chars): {reply}")
        if post_reply(tweet["id"], reply):
            seen.add(tweet["id"])
            replied += 1
            time.sleep(8)  # brief pause between replies

    _save_log(seen)
    print(f"\n✅ Done — {replied} repl{'y' if replied == 1 else 'ies'} posted")
    if replied == 0:
        print("  (nothing suitable found this run — normal)")


if __name__ == "__main__":
    main()
