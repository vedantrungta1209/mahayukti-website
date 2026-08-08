#!/usr/bin/env python3
"""
MahaYukti Weekly Analytics — runs every Monday 9 AM IST.
Pulls @wearemahayukti X metrics from last 7 days and creates a GitHub issue with the report.
"""

import os, json, datetime, requests
from pathlib import Path

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]
GH_TOKEN              = os.environ.get("GH_TOKEN", "")
REPO                  = os.environ.get("GITHUB_REPOSITORY", "vedantrungta1209/mahayukti-website")

X_HANDLE = "wearemahayukti"


def _oauth():
    from requests_oauthlib import OAuth1
    return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)


def get_user_id() -> str | None:
    auth = _oauth()
    r = requests.get(
        f"https://api.twitter.com/2/users/by/username/{X_HANDLE}",
        params={"user.fields": "public_metrics"},
        auth=auth, timeout=20,
    )
    if r.ok:
        data = r.json().get("data", {})
        print(f"Account: @{X_HANDLE} — followers: {data.get('public_metrics', {}).get('followers_count', '?')}")
        return data.get("id")
    print(f"Failed to get user ID: {r.status_code} {r.text[:200]}")
    return None


def get_recent_tweets(user_id: str) -> list[dict]:
    auth  = _oauth()
    start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = requests.get(
        f"https://api.twitter.com/2/users/{user_id}/tweets",
        params={
            "max_results":   100,
            "start_time":    start,
            "tweet.fields":  "public_metrics,created_at,text",
            "exclude":       "replies",
        },
        auth=auth, timeout=30,
    )
    if not r.ok:
        print(f"Tweet fetch failed: {r.status_code} {r.text[:200]}")
        return []
    data   = r.json()
    tweets = data.get("data", [])
    print(f"Fetched {len(tweets)} tweets from last 7 days")
    return tweets


def summarise(tweets: list[dict], followers: int) -> dict:
    if not tweets:
        return {}
    total_impressions = sum(t.get("public_metrics", {}).get("impression_count", 0) for t in tweets)
    total_likes       = sum(t.get("public_metrics", {}).get("like_count", 0) for t in tweets)
    total_retweets    = sum(t.get("public_metrics", {}).get("retweet_count", 0) for t in tweets)
    total_replies     = sum(t.get("public_metrics", {}).get("reply_count", 0) for t in tweets)
    total_bookmarks   = sum(t.get("public_metrics", {}).get("bookmark_count", 0) for t in tweets)
    engagements       = total_likes + total_retweets + total_replies + total_bookmarks

    top = sorted(tweets, key=lambda t: t.get("public_metrics", {}).get("impression_count", 0), reverse=True)[0]
    top_m = top.get("public_metrics", {})

    return {
        "tweet_count":       len(tweets),
        "total_impressions": total_impressions,
        "total_likes":       total_likes,
        "total_retweets":    total_retweets,
        "total_replies":     total_replies,
        "total_bookmarks":   total_bookmarks,
        "total_engagements": engagements,
        "eng_rate_pct":      round(engagements / max(total_impressions, 1) * 100, 2),
        "top_tweet_text":    top["text"][:200],
        "top_tweet_impressions": top_m.get("impression_count", 0),
        "top_tweet_likes":   top_m.get("like_count", 0),
        "top_tweet_id":      top["id"],
        "followers":         followers,
    }


def generate_insight(stats: dict) -> str:
    if not stats:
        return "No data available this week."
    prompt = f"""You are analysing the weekly X performance for @wearemahayukti — Mahayukti's India expert advisory account.

Stats this week:
- Tweets posted: {stats['tweet_count']}
- Total impressions: {stats['total_impressions']:,}
- Likes: {stats['total_likes']:,} | Retweets: {stats['total_retweets']:,} | Replies: {stats['total_replies']:,} | Bookmarks: {stats['total_bookmarks']:,}
- Engagement rate: {stats['eng_rate_pct']}%
- Top tweet ({stats['top_tweet_impressions']:,} impressions, {stats['top_tweet_likes']} likes): "{stats['top_tweet_text']}"

Write 3-4 bullet points of genuine insight:
- What worked (and why it likely landed)
- What to do more/less of next week
- One specific content idea for next week based on what performed well

Be direct and specific. No filler. Sound like a smart social media analyst, not a corporate report."""

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": 400,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"].strip()


def post_github_issue(stats: dict, insight: str):
    if not GH_TOKEN:
        print("No GH_TOKEN — printing report instead")
        return

    week_end   = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    week_start = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    title      = f"📊 Weekly X Analytics: {week_start} → {week_end}"

    if stats:
        top_url = f"https://x.com/wearemahayukti/status/{stats['top_tweet_id']}"
        body = f"""## @wearemahayukti — Weekly Performance Report

**Period:** {week_start} → {week_end}

### Numbers

| Metric | Value |
|--------|-------|
| Tweets posted | {stats['tweet_count']} |
| Total impressions | {stats['total_impressions']:,} |
| Likes | {stats['total_likes']:,} |
| Retweets | {stats['total_retweets']:,} |
| Replies | {stats['total_replies']:,} |
| Bookmarks | {stats['total_bookmarks']:,} |
| Engagement rate | {stats['eng_rate_pct']}% |
| Followers | {stats['followers']:,} |

### Top Tweet
> {stats['top_tweet_text']}

[View tweet]({top_url}) — {stats['top_tweet_impressions']:,} impressions · {stats['top_tweet_likes']} likes

### Insights
{insight}

---
*Auto-generated by Mahayukti analytics pipeline. Close this issue when reviewed.*"""
    else:
        body = f"No tweet data available for {week_start} → {week_end}. Check X API credentials."

    r = requests.post(
        f"https://api.github.com/repos/{REPO}/issues",
        headers={"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"},
        json={"title": title, "body": body, "labels": ["analytics"]},
        timeout=30,
    )
    if r.ok:
        print(f"✅ GitHub issue created: {r.json()['html_url']}")
    else:
        print(f"⚠️  Issue creation failed: {r.status_code} {r.text[:200]}")
        print("\n--- REPORT ---")
        print(body)


def main():
    print(f"\n📊 MahaYukti Analytics — {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    uid = get_user_id()
    if not uid:
        print("Could not get X user ID — aborting")
        return

    # Get follower count
    auth = _oauth()
    r = requests.get(f"https://api.twitter.com/2/users/{uid}", params={"user.fields": "public_metrics"}, auth=auth, timeout=20)
    followers = r.json().get("data", {}).get("public_metrics", {}).get("followers_count", 0) if r.ok else 0

    tweets = get_recent_tweets(uid)
    stats  = summarise(tweets, followers)
    insight = generate_insight(stats) if stats else "No tweets to analyse."
    print(f"\nInsight:\n{insight}")
    post_github_issue(stats, insight)


if __name__ == "__main__":
    main()
