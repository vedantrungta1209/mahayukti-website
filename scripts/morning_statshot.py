#!/usr/bin/env python3
"""
MahaYukti Morning Stat Shot — runs daily at 8 AM IST.
One compelling India data point per morning — the most shareable format on India X.
No news dependency. Always fresh. Framed with strategic context.
Replaces parliament_pulse for non-session periods.
"""

import os, json, datetime, requests, sys
from pathlib import Path
from requests_oauthlib import OAuth1

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]

_DIR      = Path(__file__).parent
_LOG_FILE = _DIR / "morning_statshot_log.json"
_DAILY    = _DIR / "morning_statshot_daily.txt"
MAX_LOG   = 200

# Rotate across these domains — prevents repetition, covers all Mahayukti angles
STAT_DOMAINS = [
    "India's defence & strategic manufacturing (missiles, warships, fighter jets, HAL, DRDO, BrahMos)",
    "India's space economy (ISRO, private space, satellite exports, Chandrayaan, Gaganyaan)",
    "India's infrastructure (highways, ports, airports, metro, bullet train, optical fibre)",
    "India's manufacturing & PLI (semiconductors, electronics, pharma, textiles, auto EVs)",
    "India's digital economy (UPI, fintech, startup unicorns, AI, data centres)",
    "India's energy transition (solar, wind, green hydrogen, nuclear, EV adoption)",
    "India's global trade & diplomacy (exports, bilateral deals, FTAs, G20 outcomes)",
    "India's demographic dividend (working-age population, STEM graduates, skilling)",
    "India in global rankings (ease of business, innovation, logistics, startup ecosystems)",
    "India's agriculture & food security (production records, export bans, crop tech)",
    "India's financial markets (FII flows, BSE market cap, forex reserves, debt reduction)",
    "India's healthcare & pharma (generic exports, AIIMS expansion, vaccination records)",
]


def _oauth():
    return OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)


def _load_log() -> dict:
    if _LOG_FILE.exists():
        try:
            data = json.loads(_LOG_FILE.read_text())
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {"posted": [], "domain_index": 0}


def _save_log(log: dict):
    log["posted"] = log["posted"][-MAX_LOG:]
    _LOG_FILE.write_text(json.dumps(log))


def _posted_today() -> bool:
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
    return _DAILY.exists() and _DAILY.read_text().strip() == today


def _mark_today():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
    _DAILY.write_text(today)


def generate_statshot(domain: str, recent_posts: list[str]) -> str:
    recent_block = ""
    if recent_posts:
        recent_block = "\n\nRECENTLY POSTED (use different stats, no repetition):\n" + "\n".join(f"- {p}" for p in recent_posts[-8:])

    system = """\
You are posting as @wearemahayukti — India's Make India Greatest movement.
Morning posts should make people feel: India is bigger than they thought. Share this.

STAT SHOT FORMAT (most viral format on India X):
- Open with ONE specific, verifiable India stat or milestone — the kind that surprises
- Follow with 1-2 sentences of WHY it matters / what it signals for India's trajectory
- Close with a forward-looking line — where India is headed, not just where it is
- Total: 210-250 characters + hashtags
- NO generic openers: not "India is" / not "Did you know" / not "India has"
- Open directly with the number or fact: "₹3.8 lakh crore in defence exports by 2029..."
- One emoji max — skip if it feels forced
- END with exactly 2-3 hashtags: always #India + 1-2 domain-specific
  Pool: #India #Bharat #ViksitBharat #IndiaRising #IndiaEconomy #IndiaDefence
        #DigitalIndia #IndiaGeopolitics #MakeIndiaGreatest #ISRO #IndiaManufacturing
        #IndiaFirst #IndiaLeads #IndiaSpace #IndiaInfrastructure #IndiaEnergy

STAT QUALITY RULES:
- Must be a real, plausible, verifiable India figure — not made up
- Prefer official data: ISRO, MoD, MoF, RBI, SEBI, MeitY, NITI Aayog, PIB
- No vague claims: not "India is growing fast" — instead "India added 127 GW solar capacity..."
- One stat only — depth beats breadth
- If uncertain of exact figure, choose a domain where you're confident
- If citing more than one year/figure for comparison (e.g. "up from X in year Y"), you MUST
  double-check the values are actually different and the math is internally consistent
  before responding — e.g. never write "81st, up from 81st, climbed 40 ranks" (that is a
  contradiction: 81 to 81 is zero change, not 40). If you are not fully certain of the
  distinct historical figure, do NOT cite a multi-year comparison — state only the current
  figure with no "up from" framing.
- Global rankings/indices (ease of business, innovation index, logistics index, etc.) change
  methodology and rank frequently and are the easiest category to get wrong — for this
  domain specifically, only cite a ranking if you are highly confident of the exact year and
  exact rank; otherwise pick a different angle within the same domain (e.g. a specific
  reform, investment figure, or program) instead of a numbered rank.

Respond with ONLY the post text (including hashtags). Nothing else."""

    prompt = f"""Domain for today's stat shot: {domain}{recent_block}

Write one crisp morning stat shot. Open with the number. Context in 1-2 sentences. Forward-looking close. 210-250 chars + hashtags."""

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
                    "max_tokens": 200,
                    "system":     system,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"].strip().strip('"')
            return text[:280]
        except Exception as e:
            print(f"  Generation attempt {attempt+1} failed: {e}")
            import time; time.sleep(5)
    return ""


def post_tweet(text: str) -> bool:
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text},
        auth=_oauth(),
        timeout=30,
    )
    if r.ok:
        tid = r.json().get("data", {}).get("id", "")
        print(f"  ✅ Posted: https://x.com/wearemahayukti/status/{tid}")
        return True
    print(f"  ❌ Failed ({r.status_code}): {r.text[:300]}")
    return False


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n📊 MahaYukti Morning Stat Shot — {now}")

    if _posted_today():
        print("⏸️  Already posted today — skipping.")
        return

    log = _load_log()
    domain_idx = log.get("domain_index", 0) % len(STAT_DOMAINS)
    domain = STAT_DOMAINS[domain_idx]
    print(f"  Domain: {domain[:60]}...")

    text = generate_statshot(domain, log.get("posted", []))
    if not text:
        print("❌ Generation failed.")
        return

    print(f"\n→ Post ({len(text)} chars): {text}")

    if post_tweet(text):
        log["posted"].append(text[:80])
        log["domain_index"] = (domain_idx + 1) % len(STAT_DOMAINS)
        _save_log(log)
        _mark_today()

        # Cross-post to LinkedIn via Make.com webhook (non-fatal)
        make_url = os.environ.get("MAKE_WEBHOOK_URL", "")
        if make_url:
            try:
                li_text = (
                    f"Morning data point for India:\n\n"
                    f"{text.split('#')[0].strip()}\n\n"
                    f"— @wearemahayukti | Make India Greatest\n\n"
                    f"#India #MakeIndiaGreatest #Mahayukti #IndiaData #IndiaFirst"
                )
                r = requests.post(make_url, json={"linkedin_text": li_text[:3000]}, timeout=15)
                print(f"  LinkedIn: {'✅ posted' if r.ok else f'⚠️ failed ({r.status_code})'}")
            except Exception as e:
                print(f"  LinkedIn: ⚠️ {e}")

        print("✅ Done")


if __name__ == "__main__":
    main()
