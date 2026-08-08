#!/usr/bin/env python3
"""
One-off: long-form X post (Premium, no image) — geo/strategic awareness theme.
Same depth as LinkedIn but written natively for X long-form.
"""

import os, requests

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]


def generate():
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 2000,
            "messages": [{
                "role": "user",
                "content": """Write a long-form X (Twitter) post for @wearemahayukti on the theme of information warfare and how nations are destabilised from within before a single shot is fired.

VOICE & IDENTITY:
- We are Indians. Not left. Not right. No political allegiance.
- We do not attack any political party, politician, or government officer — ever.
- We highlight patterns, raise awareness, and think about India's future.
- The tone is: a sharp, thoughtful Indian who has read deeply and is speaking plainly to fellow citizens.
- "Make India stronger" — constructive, not cynical.
- Medium tone. Not aggressive. Not passive. Analytical with purpose.

WHAT MAHAYUKTI IS (weave in naturally at the end, don't advertise):
Mahayukti is India's vetted professional advisory network — intelligence analysts, geopolitical experts, crisis managers, cybersecurity professionals, lawyers, finance specialists. The connection: India needs its sharpest minds connected and accessible.

FORMAT FOR X LONG-FORM:
- No bullet points with dashes. Use numbered observations or plain prose.
- Short punchy paragraphs — 1 to 3 lines each.
- Lots of white space between paragraphs.
- No hashtags at all — Premium long-form doesn't need them, they look cheap.
- No "Thread:" or "1/" notation — this is a single long-form post.
- 600 to 900 words. Enough to develop the thought fully.
- Open with one sentence that stops the scroll — a truth, a pattern, an observation.
- End with a question or a call to awareness — not anger, not despair, possibility.

Write ONLY the post text. Nothing else."""
            }]
        },
        timeout=60,
    )
    r.raise_for_status()
    text = r.json()["content"][0]["text"].strip()
    print(f"Generated ({len(text)} chars):\n\n{text}\n")
    return text


def post(text):
    from requests_oauthlib import OAuth1
    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text},
        auth=auth,
        timeout=30,
    )
    if r.ok:
        tweet_id = r.json().get("data", {}).get("id", "")
        print(f"\n✅ Posted: https://x.com/wearemahayukti/status/{tweet_id}")
    else:
        print(f"\n❌ Failed ({r.status_code}): {r.text}")


if __name__ == "__main__":
    text = generate()
    post(text)
