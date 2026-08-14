#!/usr/bin/env python3
"""
MahaYukti X Reply Growth — 3× daily (9 AM, 3 PM, 9 PM IST).
Finds fresh tweets from high-follower India accounts via Nitter RSS,
generates substantive replies via Claude, posts via X write API.
No X read API credits used — Nitter RSS only.
Goal: borrow reach from established accounts to grow @wearemahayukti from 0.
"""

import os, json, re, datetime, requests, time, xml.etree.ElementTree as ET
from pathlib import Path
from requests_oauthlib import OAuth1

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "x_reply_growth_log.json"
MAX_LOG         = 1000   # keep last N replied tweet IDs
REPLIES_PER_RUN = 3      # max replies per run (3 runs × 3 replies = 9/day)
MAX_AGE_HOURS   = 6      # only reply to tweets newer than this

# Nitter instances for RSS (used in order, first one that works wins)
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacyredirect.com",
    "https://nitter.net",
    "https://nitter.1d4.us",
    "https://nitter.tiekoetter.com",
]

# High-follower India accounts to engage with
# weight = how often to target (higher = more likely to be selected this run)
TARGET_ACCOUNTS = [
    # Official government & policy
    {"handle": "DrSJaishankar",  "niche": "foreign_policy",  "weight": 10},
    {"handle": "MEAIndia",       "niche": "foreign_policy",  "weight": 8},
    {"handle": "isro",           "niche": "science_tech",    "weight": 8},
    {"handle": "FinMinIndia",    "niche": "economy",         "weight": 7},
    {"handle": "RBI",            "niche": "economy",         "weight": 7},
    {"handle": "PIBIndia",       "niche": "governance",      "weight": 6},
    {"handle": "makeinindia",    "niche": "economy",         "weight": 7},
    {"handle": "DigitalIndia",   "niche": "technology",      "weight": 6},
    {"handle": "narendramodi",   "niche": "governance",      "weight": 8},
    {"handle": "PMOIndia",       "niche": "governance",      "weight": 7},
    # Business & economy news (large India audiences)
    {"handle": "EconomicTimes",  "niche": "business",        "weight": 5},
    {"handle": "livemint",       "niche": "business",        "weight": 5},
    {"handle": "bsindia",        "niche": "business",        "weight": 4},
    # Policy think tanks & analysts
    {"handle": "ORF_online",     "niche": "policy",          "weight": 6},
    {"handle": "BrookingsIndia", "niche": "policy",          "weight": 5},
    # Tech & startup
    {"handle": "nasscom",        "niche": "technology",      "weight": 5},
    {"handle": "StartupIndia",   "niche": "technology",      "weight": 5},
]

NICHE_CONTEXT = {
    "foreign_policy": "India's strategic interests, diplomacy, and global positioning",
    "science_tech":   "India's science, space, and technology achievements",
    "economy":        "India's economic trajectory, growth, and financial policy",
    "governance":     "India's governance, development, and policy direction",
    "business":       "India's business environment, markets, and entrepreneurship",
    "policy":         "India's domestic and foreign policy landscape",
    "technology":     "India's digital transformation and tech ecosystem",
}


def _oauth() -> OAuth1:
    return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)


def _load_log() -> dict:
    if _LOG_FILE.exists():
        try:
            data = json.loads(_LOG_FILE.read_text())
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {"replied_ids": [], "replied_handles": []}


def _save_log(log: dict):
    log["replied_ids"]     = log["replied_ids"][-MAX_LOG:]
    log["replied_handles"] = log["replied_handles"][-MAX_LOG:]
    _LOG_FILE.write_text(json.dumps(log, indent=2))


def _parse_date(date_str: str) -> datetime.datetime | None:
    import email.utils
    try:
        return datetime.datetime(*email.utils.parsedate(date_str)[:6],
                                  tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def fetch_nitter_rss(handle: str) -> list[dict]:
    """Fetch recent tweets for a handle from Nitter RSS. Returns list of {id, text, url, published}."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=MAX_AGE_HOURS)

    for instance in NITTER_INSTANCES:
        rss_url = f"{instance}/{handle}/rss"
        try:
            r = requests.get(rss_url, timeout=12,
                             headers={"User-Agent": "Mozilla/5.0 (Mahayukti feed reader)"})
            if not r.ok:
                continue

            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            results = []

            for item in items:
                title   = (item.findtext("title") or "").strip()
                link    = (item.findtext("link")  or "").strip()
                desc    = (item.findtext("description") or "").strip()
                pub_raw = (item.findtext("pubDate") or "").strip()

                pub_dt = _parse_date(pub_raw)
                if pub_dt and pub_dt < cutoff:
                    continue

                # Extract tweet ID from Nitter URL: /handle/status/ID#m
                m = re.search(r'/status/(\d+)', link)
                if not m:
                    continue
                tweet_id = m.group(1)

                # Clean up description (strip HTML tags)
                clean = re.sub(r'<[^>]+>', ' ', desc).strip()
                clean = re.sub(r'\s+', ' ', clean)

                # Skip retweets (Nitter marks them with RT @)
                if title.startswith("RT @"):
                    continue

                results.append({
                    "id":        tweet_id,
                    "text":      title or clean[:280],
                    "full_text": clean[:500],
                    "url":       f"https://x.com/{handle}/status/{tweet_id}",
                    "published": pub_dt,
                })

            if results:
                print(f"  [{handle}] {len(results)} tweets from {instance.split('//')[1]}")
                return results

        except Exception as e:
            print(f"  Nitter {instance.split('//')[1]} error for @{handle}: {e}")
            continue

    print(f"  [{handle}] All Nitter instances failed")
    return []


def select_accounts(log: dict, n: int) -> list[dict]:
    """Pick n target accounts, weighted, avoiding recently replied handles."""
    recent_handles = set(log["replied_handles"][-20:])
    pool = [a for a in TARGET_ACCOUNTS if a["handle"] not in recent_handles]
    if not pool:
        pool = TARGET_ACCOUNTS[:]

    # Weighted random selection without replacement
    import random
    weights = [a["weight"] for a in pool]
    selected = []
    pool_copy = pool[:]
    weight_copy = weights[:]

    while len(selected) < n and pool_copy:
        total = sum(weight_copy)
        r = random.uniform(0, total)
        cumulative = 0
        for i, (acc, w) in enumerate(zip(pool_copy, weight_copy)):
            cumulative += w
            if r <= cumulative:
                selected.append(acc)
                pool_copy.pop(i)
                weight_copy.pop(i)
                break

    return selected


def generate_reply(tweet_text: str, handle: str, niche: str) -> str | None:
    """Generate a substantive, India-forward reply using Claude."""
    context = NICHE_CONTEXT.get(niche, "India's development and strategic affairs")

    system = f"""\
You are replying on X as @wearemahayukti — a sharp India-first expert advisory account.
Your area: {context}.
Mission: Make India Greatest.

REPLY RULES (non-negotiable):
- 200-240 characters TOTAL including hashtags
- Add genuine insight, data, or a forward-looking point NOT in the original tweet
- Constructive and respectful — never critical of government or officials by name
- Sound like a credible Indian analyst, not a fan or a bot
- If the original is about an achievement: acknowledge briefly + add strategic implication
- If it's a policy announcement: add a specific sector/number it will impact
- If it's geopolitics: add a named country or alliance angle
- No filler words: "Great!", "Indeed", "Well said", "Impressive", "Absolutely"
- End with exactly 1-2 hashtags from: #India #Bharat #ViksitBharat #IndiaRising
  #IndiaEconomy #IndiaDefence #IndiaGeopolitics #MakeInIndia #ISRO #IndiaFirst
- Do NOT start with "@{handle}" — X adds that automatically for replies

OUTPUT: Return ONLY the reply text. No quotes, no commentary."""

    prompt = f"""Original tweet by @{handle}:
"{tweet_text}"

Write a sharp 200-240 character reply that adds real insight."""

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
                "max_tokens": 150,
                "system":     system,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=25,
        )
        r.raise_for_status()
        reply = r.json()["content"][0]["text"].strip().strip('"')
        if len(reply) > 280:
            reply = reply[:277] + "..."
        return reply
    except Exception as e:
        print(f"  Claude error: {e}")
        return None


def post_reply(tweet_id: str, reply_text: str, handle: str) -> bool:
    """Post reply to tweet_id via X write API."""
    auth = _oauth()
    payload = {
        "text":  reply_text,
        "reply": {"in_reply_to_tweet_id": tweet_id},
    }
    try:
        r = requests.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            auth=auth,
            timeout=30,
        )
        if r.ok:
            new_id = r.json().get("data", {}).get("id", "")
            print(f"  ✅ Replied to @{handle}: https://x.com/wearemahayukti/status/{new_id}")
            return True
        print(f"  ❌ Reply failed ({r.status_code}): {r.text[:300]}")
        return False
    except Exception as e:
        print(f"  ❌ Reply error: {e}")
        return False


def main():
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n💬 MahaYukti X Reply Growth — {now_str}")

    log = _load_log()
    replied_ids = set(log["replied_ids"])

    # Select target accounts for this run
    accounts_to_check = select_accounts(log, min(REPLIES_PER_RUN * 2, len(TARGET_ACCOUNTS)))
    print(f"  Checking {len(accounts_to_check)} accounts for fresh tweets...")

    candidates = []  # (account, tweet)
    for acc in accounts_to_check:
        tweets = fetch_nitter_rss(acc["handle"])
        for tweet in tweets:
            if tweet["id"] in replied_ids:
                continue
            candidates.append((acc, tweet))
            break  # one fresh tweet per account

    if not candidates:
        print("  No fresh tweets found to reply to — exiting")
        return

    print(f"  {len(candidates)} reply candidates found")

    posted = 0
    for acc, tweet in candidates[:REPLIES_PER_RUN]:
        print(f"\n→ @{acc['handle']}: {tweet['text'][:100]}...")
        reply = generate_reply(tweet["text"], acc["handle"], acc["niche"])
        if not reply:
            continue

        print(f"  Reply ({len(reply)} chars): {reply}")
        if post_reply(tweet["id"], reply, acc["handle"]):
            log["replied_ids"].append(tweet["id"])
            log["replied_handles"].append(acc["handle"])
            posted += 1
            time.sleep(15)  # space out replies

    _save_log(log)
    print(f"\n✅ Done — {posted} repl{'ies' if posted != 1 else 'y'} posted")


if __name__ == "__main__":
    main()
