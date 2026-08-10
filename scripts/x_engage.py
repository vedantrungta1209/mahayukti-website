#!/usr/bin/env python3
"""
MahaYukti X Engagement Loop — runs every 3 hours.
Finds high-relevance India tweets, generates a sharp reply, posts it.
Falls back to quote-tweet when the author has restricted replies.
"""

import os, json, datetime, requests, time
from pathlib import Path

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "x_engage_log.json"
MAX_LOG   = 500
MAX_REPLIES_PER_RUN = 2
MIN_LIKES           = 2   # lowered from 5 — new account, targets are not viral

# Prioritise tweets from known high-follower handles so we borrow their audience
HIGH_VALUE_HANDLES = [
    "ANI", "ndtv", "TOIIndiaNews", "HTTweets", "IndianExpress",
    "the_hindu", "ZeeNews", "republic", "timesofindia",
    "PIB_India", "MEAIndia", "PMOIndia", "adgpi",
]

# Search queries — rotate hourly
SEARCH_QUERIES = [
    '(from:ANI OR from:ndtv OR from:TOIIndiaNews OR from:HTTweets) (parliament OR "lok sabha" OR "rajya sabha") lang:en -is:retweet -is:reply',
    '(from:PIB_India OR from:MEAIndia OR from:PMOIndia OR from:adgpi) lang:en -is:retweet -is:reply',
    '("india economy" OR "india gdp" OR "rbi india" OR "budget india") lang:en -is:retweet -is:reply',
    '(ISRO OR "india defence" OR "india security" OR "make in india") lang:en -is:retweet -is:reply',
    '("india china" OR "india pakistan" OR "india diplomacy" OR "india geopolit") lang:en -is:retweet -is:reply',
    '("digital india" OR "india startup" OR "india tech" OR "india infrastructure") lang:en -is:retweet -is:reply',
    '("india 2047" OR "amrit kaal" OR "viksit bharat" OR "new india") lang:en -is:retweet -is:reply',
]

BLOCKED_TERMS = [
    "bjp4india", "incIndia", "aap party", "aam aadmi party",
    "anti-modi", "anti-india",
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
    hour = datetime.datetime.now(datetime.timezone.utc).hour
    return SEARCH_QUERIES[hour % len(SEARCH_QUERIES)]


def search_tweets(query: str) -> list[dict]:
    auth = _oauth()
    r = requests.get(
        "https://api.twitter.com/2/tweets/search/recent",
        params={
            "query":        query,
            "max_results":  20,
            "tweet.fields": "public_metrics,author_id,created_at,text",
            "expansions":   "author_id",
            "user.fields":  "username,verified,public_metrics",
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
            "id":        t["id"],
            "text":      t["text"],
            "username":  user.get("username", ""),
            "followers": user.get("public_metrics", {}).get("followers_count", 0),
            "likes":     metrics.get("like_count", 0),
            "retweets":  metrics.get("retweet_count", 0),
            "replies":   metrics.get("reply_count", 0),
        })

    # Sort: high-value handles first, then by engagement
    def _score(t):
        handle_bonus = 1000 if t["username"] in HIGH_VALUE_HANDLES else 0
        return handle_bonus + t["likes"] + t["retweets"] * 2

    results.sort(key=_score, reverse=True)
    return results


def _is_safe(tweet: dict) -> bool:
    text_lower   = tweet["text"].lower()
    handle_lower = tweet["username"].lower()
    if handle_lower == "wearemahayukti":
        return False
    if any(b in text_lower or b in handle_lower for b in BLOCKED_TERMS):
        return False
    if tweet["likes"] < MIN_LIKES:
        return False
    return True


def generate_reply(tweet: dict) -> str:
    system = """\
You are a founding member of Mahayukti engaging on X as @wearemahayukti.
Movement: Make India Greatest. Positive, warm, India-first.

HARD RULES:
- Never attack any politician, party, minister, or official
- PM Modi, President Murmu, constitutional bodies — always respectful
- No religious or caste angle
- Never cynical or despairing — always constructive
- Do not promote Mahayukti unless it genuinely fits
- Sound like a real, well-read Indian — not a brand bot

STYLE:
- Max 240 characters — must work as a standalone post if needed (not just as a reply)
- Direct, specific to the topic — not generic
- Add perspective or forward-looking India context, not just agreement
- Contractions: "isn't", "we've", "can't"
- NEVER: "Great point!", "Indeed", "Absolutely", "Totally agree", "Well said"
- 1-2 relevant hashtags are OK for standalone posts
- One emoji max if it genuinely fits; skip otherwise

Respond with ONLY the post text. Nothing else."""

    prompt = f"""Write a post engaging with this topic raised by @{tweet['username']} ({tweet['followers']:,} followers):

"{tweet['text']}"

Your perspective on this. Specific, forward-looking, India-first. Must make sense as a standalone post even without context. Under 240 chars."""

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
                    "model":     "claude-sonnet-4-6",
                    "max_tokens": 100,
                    "system":     system,
                    "messages":  [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"].strip().strip('"')
            if len(text) > 250:
                text = text[:247] + "..."
            return text
        except Exception as e:
            print(f"  Generation attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(5)
    return ""


def post_engagement(tweet_id: str, reply_text: str) -> bool:
    """
    Try reply → quote-tweet → standalone post.
    New accounts are restricted from replying/quoting; standalone posts always work.
    """
    auth = _oauth()

    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": reply_text, "reply": {"in_reply_to_tweet_id": tweet_id}},
        auth=auth,
        timeout=30,
    )
    if r.ok:
        new_id = r.json().get("data", {}).get("id", "")
        print(f"  ✅ Replied: https://x.com/wearemahayukti/status/{new_id}")
        return True

    if r.status_code == 403:
        print(f"  Reply restricted — trying quote-tweet...")
        r2 = requests.post(
            "https://api.twitter.com/2/tweets",
            json={"text": reply_text, "quote_tweet_id": tweet_id},
            auth=auth,
            timeout=30,
        )
        if r2.ok:
            new_id = r2.json().get("data", {}).get("id", "")
            print(f"  ✅ Quote-tweeted: https://x.com/wearemahayukti/status/{new_id}")
            return True

        if r2.status_code == 403:
            print(f"  Quote also restricted — posting as standalone original tweet...")
            r3 = requests.post(
                "https://api.twitter.com/2/tweets",
                json={"text": reply_text},
                auth=auth,
                timeout=30,
            )
            if r3.ok:
                new_id = r3.json().get("data", {}).get("id", "")
                print(f"  ✅ Standalone posted: https://x.com/wearemahayukti/status/{new_id}")
                return True
            print(f"  ❌ Standalone also failed ({r3.status_code}): {r3.text[:200]}")
            return False

        print(f"  ❌ Quote-tweet failed ({r2.status_code}): {r2.text[:200]}")
        return False

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

    engaged = 0
    for tweet in tweets:
        if engaged >= MAX_REPLIES_PER_RUN:
            break
        if tweet["id"] in seen:
            continue
        if not _is_safe(tweet):
            continue

        print(f"\n→ @{tweet['username']} ({tweet['likes']} likes, {tweet['followers']:,} followers): {tweet['text'][:100]}...")
        reply = generate_reply(tweet)
        if not reply:
            continue

        print(f"  Text ({len(reply)} chars): {reply}")
        if post_engagement(tweet["id"], reply):
            seen.add(tweet["id"])
            engaged += 1
            time.sleep(8)

    _save_log(seen)
    print(f"\n✅ Done — {engaged} engagement{'s' if engaged != 1 else ''} posted")
    if engaged == 0:
        print("  (nothing suitable found this run)")


if __name__ == "__main__":
    main()
