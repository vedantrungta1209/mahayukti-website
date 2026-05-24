#!/usr/bin/env python3
"""
Auto-refresh LinkedIn access token when it's > 50 days old.
Runs at the start of every daily-post workflow run.
Stores refreshed tokens back to GitHub secrets via gh CLI.
"""
import os, time, subprocess, sys, requests

REFRESH_TOKEN = os.environ.get("LINKEDIN_REFRESH_TOKEN", "")
CLIENT_ID     = os.environ.get("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
GH_REPO       = "vedantrungta1209/mahayukti-website"

if not REFRESH_TOKEN or not CLIENT_ID or not CLIENT_SECRET:
    print("LinkedIn refresh credentials not configured — skipping refresh.")
    sys.exit(0)

ISSUED_AT = int(os.environ.get("LINKEDIN_TOKEN_ISSUED_AT") or "0")

age_days = (time.time() - ISSUED_AT) / 86400
print(f"LinkedIn token age: {age_days:.0f} days")

if age_days < 50:
    print("Token is fresh — no refresh needed.")
    sys.exit(0)

print("Refreshing LinkedIn access token...")
r = requests.post(
    "https://www.linkedin.com/oauth/v2/accessToken",
    data={
        "grant_type":    "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
)
r.raise_for_status()
data = r.json()

new_token   = data["access_token"]
new_refresh = data.get("refresh_token", REFRESH_TOKEN)
now         = str(int(time.time()))


def _set_secret(name: str, value: str):
    subprocess.run(
        ["gh", "secret", "set", name, "--body", value, "--repo", GH_REPO],
        check=True, capture_output=True,
    )


_set_secret("LINKEDIN_ACCESS_TOKEN",    new_token)
_set_secret("LINKEDIN_REFRESH_TOKEN",   new_refresh)
_set_secret("LINKEDIN_TOKEN_ISSUED_AT", now)
print("LinkedIn token refreshed and stored in GitHub secrets.")
