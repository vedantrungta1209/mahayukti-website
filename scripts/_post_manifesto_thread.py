#!/usr/bin/env python3
"""
One-time script: post the Mahayukti founding manifesto as a 15-tweet thread.
Run once — idempotency guard prevents re-posting.
"""

import os, json, time, requests
from pathlib import Path
from requests_oauthlib import OAuth1

X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

GUARD = Path(__file__).parent / "_manifesto_thread_posted.txt"

THREAD = [
    # 1 — Hook
    """\
If an enemy wanted regime change in India, it wouldn't invade our borders first.

It would enter your mind.
And make you believe India must be saved from itself.

This is not theory. This is a documented playbook.

Read carefully. 🧵""",

    # 2 — The method
    """\
I'll speak in coded language so this reaches you.

Somewhere, a geopolitical actor is studying Bharat.
Its faultlines. Its weaknesses. Its demography.

Their objective: make Indians turn against their own state.

That is how regime change begins. Not with armies. With ideas.""",

    # 3 — The weapon: narrative
    """\
Regime change in India will not begin with tanks.

It will begin with a story.

A story that makes you distrust your country —
and thank the people trying to break it.

Here is the full 12-step playbook. Recognise every step.""",

    # 4 — Steps 1-2
    """\
Step 1: Weaken the economy.
Sanctions. Supply shocks. Currency pressure.
Make life hurt.

Step 2: Blame every hardship on the government.
Not one policy. The entire system.

The goal: make citizens feel the state itself is the enemy — not the actors engineering the pain.""",

    # 5 — Steps 3-4
    """\
Step 3: Find a wound.
Jobs. Exams. Farmers. Religion. Caste.

The playbook doesn't create wounds — it finds them, widens them, and ensures they never heal.

Step 4: Find faces for the anger.
Activists. Influencers. Students.

Some are driven by genuine conviction.
Some are very well trained.""",

    # 6 — Step 5
    """\
Step 5: Weaponise social media.

Algorithmic manipulation. AI-generated videos. Coordinated amplification.

Bots make whispers look like revolution.

10,000 accounts repeating one narrative makes it feel like "what everyone thinks."

You don't realise you're inside the operation.""",

    # 7 — Steps 6-7
    """\
Step 6: Merge unrelated protests.
Farmers + students + minorities + unemployed youth — different grievances, one enemy.

Step 7: Wait for a spark.
A clash. An arrest. A death.

Nobody asks who lit the match.
Everyone watches the fire.

Outrage consumes the oxygen. Analysis dies.""",

    # 8 — Step 8
    """\
Step 8: Internationalise the outrage.

Failures amplified. Successes buried. Context erased entirely.

Foreign governments "express concern."
Foreign-funded NGOs publish reports.
International media runs the narrative.

India — a sovereign democracy of 1.4 billion — is placed in the global courtroom.""",

    # 9 — Step 9
    """\
Step 9: Discredit every institution.

Courts captured. Elections manipulated. Parliament irrelevant.
Army politicised. Bureaucracy broken. Reform impossible.

Once citizens stop believing in their own institutions —
the vacuum doesn't stay empty.
It fills with whoever the architects have prepared.""",

    # 10 — Steps 10-11
    """\
Step 10: Demonise the leadership.
One person answers for everything.
Then the businessmen: cronies, oligarchs, "owners of India."

Once the face of the nation is despised, what comes next feels like liberation.

Step 11: Build a ring of fire.
Border pressure. Unstable neighbours. Cyberattacks. Diplomatic isolation.""",

    # 11 — Step 12 + polarisation
    """\
Step 12: Break national morale.
Tell you Bharat is finished.
Tell the young to leave.
Make collapse feel inevitable.

Then — polarise everyone.

Religion vs religion. Young vs elders. Caste vs caste. State vs Centre.
Indian against Indian.

Split the elites. Officials prepare for "after."
Target the last wall: Police. Military. Intelligence.""",

    # 12 — The endgame
    """\
A government struggles when streets are angry.

A regime falls when the state stops defending itself.

Then comes the replacement.

A coalition. A malleable leader. A "temporary" arrangement.

The script has run across dozens of countries.
Only the language changes. Only the flag changes. Only the victim changes.""",

    # 13 — Warning
    """\
Stay alert. Till 2028.

Patterns matter more than individual headlines.
Be Vigilant. Be Careful. Be Patient.

Every student should learn this pattern.
Every citizen should be able to recognise it.

Yet most media houses never explain the architecture. Only the noise.""",

    # 14 — The question
    """\
Now look around carefully.

Is India merely arguing with itself?

Or is someone teaching it how to collapse?

If you can't see the pattern — you become the pawn.
If you can — you become the firewall.

Share this. The people who need to read it, won't find it on their own.""",

    # 15 — Mahayukti closer
    """\
This is why @wearemahayukti exists.

Not to fight politicians. Not to pick sides.

To build an India that cannot be collapsed from within —
by connecting its best minds, its citizens, and its institutions.

Make India Greatest. Not a slogan. A defence.

#MakeIndiaGreatest #India #Bharat""",
]


def oauth():
    return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)


def post_tweet(text: str, reply_to: str | None = None) -> str | None:
    payload: dict = {"text": text}
    if reply_to:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to}

    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
        auth=oauth(),
        timeout=30,
    )
    if r.ok:
        tid = r.json()["data"]["id"]
        print(f"  ✅ {tid}: {text[:60].replace(chr(10),' ')}...")
        return tid
    print(f"  ❌ Failed ({r.status_code}): {r.text[:300]}")
    return None


def main():
    if GUARD.exists():
        print("⏸️  Manifesto thread already posted — guard file exists.")
        print(f"  Thread ID: {GUARD.read_text().strip()}")
        return

    print(f"\n🇮🇳 Posting Mahayukti Manifesto Thread ({len(THREAD)} tweets)")
    print("─" * 60)

    prev_id: str | None = None
    first_id: str | None = None
    posted: list[str] = []

    for i, tweet_text in enumerate(THREAD, 1):
        chars = len(tweet_text)
        print(f"\n[{i}/{len(THREAD)}] {chars} chars")

        if chars > 280:
            print(f"  ⚠️  Over 280 chars! Trimming...")
            tweet_text = tweet_text[:277] + "..."

        tid = post_tweet(tweet_text, reply_to=prev_id)
        if not tid:
            print(f"\n❌ Thread broken at tweet {i}. Posted {len(posted)} tweets.")
            break

        posted.append(tid)
        if i == 1:
            first_id = tid
        prev_id = tid

        if i < len(THREAD):
            time.sleep(3)  # avoid rate limiting

    if first_id:
        thread_url = f"https://x.com/wearemahayukti/status/{first_id}"
        print(f"\n✅ Thread posted: {thread_url}")
        GUARD.write_text(first_id)

        log_file = Path(__file__).parent / "_manifesto_thread_log.json"
        log_file.write_text(json.dumps({
            "first_tweet_id": first_id,
            "tweet_ids":      posted,
            "thread_url":     thread_url,
            "total_tweets":   len(posted),
        }, indent=2))


if __name__ == "__main__":
    main()
