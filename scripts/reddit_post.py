#!/usr/bin/env python3
"""
MahaYukti Reddit — Posts insightful India-topic content to relevant subreddits.
Drives organic reach. Never promotional spam — always genuine value-add posts.

Subreddits: r/india, r/IndiaTech, r/IndiaInvestments, r/geopolitics, r/IndiaOpen
Strategy: Post as a knowledgeable Indian, reference Mahayukti only if directly relevant.
"""

import os, json, hashlib, datetime, requests, sys, time
from pathlib import Path

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
REDDIT_CLIENT_ID  = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SECRET     = os.environ["REDDIT_SECRET"]
REDDIT_USERNAME   = os.environ["REDDIT_USERNAME"]
REDDIT_PASSWORD   = os.environ["REDDIT_PASSWORD"]
REDDIT_USER_AGENT = "MahayuktiBot/1.0 by u/MahayuktiAdvisory"

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "reddit_post_log.json"
MAX_LOG   = 300

# Subreddits and their content focus
SUBREDDITS = [
    {
        "name":    "india",
        "focus":   "General India news, policy, society",
        "tone":    "Balanced, informative. Indians of all walks of life.",
        "flair":   None,
        "max_week": 3,
    },
    {
        "name":    "IndiaTech",
        "focus":   "Indian tech, startups, digital India, ISRO, AI",
        "tone":    "Technical but accessible. Startup/professional crowd.",
        "flair":   None,
        "max_week": 2,
    },
    {
        "name":    "IndiaInvestments",
        "focus":   "Indian markets, economy, RBI, budget, sectors",
        "tone":    "Data-driven, practical, no hype.",
        "flair":   None,
        "max_week": 2,
    },
    {
        "name":    "geopolitics",
        "focus":   "India's strategic position, China/Pakistan/global dynamics",
        "tone":    "Academic and analytical. Global audience.",
        "flair":   None,
        "max_week": 1,
    },
]

# Source topics — rotated based on day of week
TOPIC_POOLS = {
    "monday":    ["Indian economy outlook", "RBI policy", "Make in India sectors"],
    "tuesday":   ["India-China dynamics", "India defence", "border infrastructure"],
    "wednesday": ["Indian startups", "ISRO / space", "digital India progress"],
    "thursday":  ["Parliament session", "Indian legislation", "governance reform"],
    "friday":    ["India trade", "foreign investment", "India global standing"],
    "saturday":  ["Indian geopolitics", "India's 2047 vision", "Amrit Kaal"],
    "sunday":    ["India agriculture", "health policy", "education reform"],
}


def _reddit_auth() -> str | None:
    r = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(REDDIT_CLIENT_ID, REDDIT_SECRET),
        data={"grant_type": "password", "username": REDDIT_USERNAME, "password": REDDIT_PASSWORD},
        headers={"User-Agent": REDDIT_USER_AGENT},
        timeout=20,
    )
    if r.ok:
        token = r.json().get("access_token")
        print(f"  Reddit auth OK")
        return token
    print(f"  Reddit auth failed ({r.status_code}): {r.text[:200]}")
    return None


def _load_log() -> dict:
    if _LOG_FILE.exists():
        try:
            return json.loads(_LOG_FILE.read_text())
        except Exception:
            pass
    return {"posted": [], "weekly_counts": {}}


def _save_log(log: dict):
    log["posted"] = log["posted"][-MAX_LOG:]
    _LOG_FILE.write_text(json.dumps(log, indent=2))


def _week_key() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-W%W")


def _posts_this_week(log: dict, subreddit: str) -> int:
    key = f"{_week_key()}:{subreddit}"
    return log.get("weekly_counts", {}).get(key, 0)


def _increment_week(log: dict, subreddit: str):
    key = f"{_week_key()}:{subreddit}"
    log.setdefault("weekly_counts", {})[key] = log["weekly_counts"].get(key, 0) + 1


def _pick_topic() -> str:
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%A").lower()
    pool = TOPIC_POOLS.get(day, TOPIC_POOLS["monday"])
    hour = datetime.datetime.now(datetime.timezone.utc).hour
    return pool[hour % len(pool)]


def generate_post(topic: str, subreddit: dict) -> dict | None:
    system = f"""\
You are a knowledgeable Indian professional writing a Reddit post for r/{subreddit['name']}.

THIS SUBREDDIT: {subreddit['focus']}
AUDIENCE TONE: {subreddit['tone']}

RULES — critical:
- Write as a thoughtful Indian expert, NOT as a brand or company
- Do NOT mention Mahayukti unless it directly answers a question in the post
- No promotional language, no "check us out", no links to mahayukti.com in the post body
- Provide GENUINE VALUE — analysis, data, insight, perspective
- Reddit readers are intelligent and will downvote anything that feels like an ad
- Post must stand on its own merits as a contribution to the community
- Be direct. Reddit hates corporate speak.

POST FORMAT:
- Title: Compelling, specific, no clickbait (max 200 chars)
- Body: 200-600 words of genuine insight. Use Reddit markdown (##, **, -, etc.)
- End with an open question to spark discussion
- No hashtags — this is Reddit, not Twitter

Respond with JSON only:
{{"title": "...", "body": "..."}}"""

    prompt = f"Write a Reddit post for r/{subreddit['name']} about: {topic}"

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": 1000, "system": system,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=40,
    )
    if not r.ok:
        print(f"  Generation failed: {r.status_code}")
        return None
    text = r.json()["content"][0]["text"].strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except Exception as e:
        print(f"  JSON parse failed: {e}\n  Raw: {text[:200]}")
        return None


def submit_post(token: str, subreddit: str, title: str, body: str) -> str | None:
    r = requests.post(
        "https://oauth.reddit.com/api/submit",
        headers={"Authorization": f"Bearer {token}", "User-Agent": REDDIT_USER_AGENT},
        data={
            "sr":       subreddit,
            "kind":     "self",
            "title":    title[:300],
            "text":     body,
            "nsfw":     False,
            "spoiler":  False,
            "resubmit": True,
        },
        timeout=30,
    )
    if r.ok:
        data   = r.json()
        errors = data.get("json", {}).get("errors", [])
        if errors:
            print(f"  Reddit submit errors: {errors}")
            return None
        url = data.get("json", {}).get("data", {}).get("url", "")
        print(f"  ✅ Posted to r/{subreddit}: {url}")
        return url
    print(f"  ❌ Submit failed ({r.status_code}): {r.text[:300]}")
    return None


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n📋 MahaYukti Reddit — {now}")

    log   = _load_log()
    token = _reddit_auth()
    if not token:
        sys.exit(1)

    topic = _pick_topic()
    print(f"Topic: {topic}")

    posted = 0
    for sub in SUBREDDITS:
        week_count = _posts_this_week(log, sub["name"])
        if week_count >= sub["max_week"]:
            print(f"  r/{sub['name']}: weekly limit reached ({week_count}/{sub['max_week']}) — skipping")
            continue

        print(f"\n→ r/{sub['name']} ({week_count}/{sub['max_week']} this week)")
        post = generate_post(topic, sub)
        if not post:
            continue

        print(f"  Title: {post['title']}")
        url = submit_post(token, sub["name"], post["title"], post["body"])
        if url:
            _increment_week(log, sub["name"])
            log["posted"].append({
                "id":        hashlib.md5(url.encode()).hexdigest()[:8],
                "subreddit": sub["name"],
                "title":     post["title"],
                "url":       url,
                "ts":        now,
            })
            posted += 1
            time.sleep(10)  # Reddit rate limiting — be polite
        break  # one subreddit per run to stay well within rate limits

    _save_log(log)
    print(f"\n✅ Done — {posted} post{'s' if posted != 1 else ''} submitted")


if __name__ == "__main__":
    main()
