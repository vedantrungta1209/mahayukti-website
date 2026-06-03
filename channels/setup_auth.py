#!/usr/bin/env python3
"""
One-time OAuth setup for all 7 Mahayukti topic channels.
Runs each channel auth sequentially — opens browser, you sign in to
the correct Google account, token auto-saved to GitHub secret.

Usage (all channels):
  cd channels && python3 setup_auth.py

Usage (single channel):
  python3 setup_auth.py --channel hustle

Requirements:
  pip install google-auth-oauthlib google-auth google-api-python-client
  gh CLI must be authenticated: gh auth login

The client_secret.json is shared across all channels — same OAuth app,
different Google accounts. When the browser opens, sign in with the
Google account that owns THAT specific channel.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

# Upload + comment posting scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

CLIENT_SECRET = Path(__file__).parent.parent / "MahayuktiAI" / "client_secret.json"
GH_REPO       = "vedantrungta1209/mahayukti-website"

CHANNELS = [
    {
        "id":          "hustle",
        "name":        "Mahayukti Hustle",
        "handle":      "@mahayuktihustle",
        "secret_name": "YOUTUBE_HUSTLE_TOKEN_JSON",
        "token_file":  "hustle_token.json",
        "port":        8080,
    },
    {
        "id":          "business",
        "name":        "Mahayukti Business",
        "handle":      "@mahayuktibusiness",
        "secret_name": "YOUTUBE_BUSINESS_TOKEN_JSON",
        "token_file":  "business_token.json",
        "port":        8081,
    },
    {
        "id":          "crime",
        "name":        "Mahayukti Crime",
        "handle":      "@mahayuktikrime",
        "secret_name": "YOUTUBE_CRIME_TOKEN_JSON",
        "token_file":  "crime_token.json",
        "port":        8082,
    },
    {
        "id":          "mind",
        "name":        "Mahayukti Mind",
        "handle":      "@mahayuktimind",
        "secret_name": "YOUTUBE_MIND_TOKEN_JSON",
        "token_file":  "mind_token.json",
        "port":        8083,
    },
    {
        "id":          "kanoon",
        "name":        "Mahayukti Kanoon",
        "handle":      "@mahayuktikanoon",
        "secret_name": "YOUTUBE_KANOON_TOKEN_JSON",
        "token_file":  "kanoon_token.json",
        "port":        8084,
    },
    {
        "id":          "speak",
        "name":        "Mahayukti Speak",
        "handle":      "@mahayuktispeak",
        "secret_name": "YOUTUBE_SPEAK_TOKEN_JSON",
        "token_file":  "speak_token.json",
        "port":        8085,
    },
    {
        "id":          "swasth",
        "name":        "Mahayukti Swasth",
        "handle":      "@mahayuktiswasth",
        "secret_name": "YOUTUBE_SWASTH_TOKEN_JSON",
        "token_file":  "swasth_token.json",
        "port":        8086,
    },
    {
        "id":          "finance",
        "name":        "Mahayukti Finance",
        "handle":      "@mahayuktifinance",
        "secret_name": "YOUTUBE_FINANCE_TOKEN_JSON",
        "token_file":  "finance_token.json",
        "port":        8087,
    },
]


def _bar(ch: dict, total: int, idx: int) -> None:
    print()
    print("=" * 60)
    print(f"  Channel {idx + 1}/{total}: {ch['name']} ({ch['handle']})")
    print("=" * 60)


def _save_secret(secret_name: str, value: str) -> bool:
    result = subprocess.run(
        ["gh", "secret", "set", secret_name, "--body", value, "--repo", GH_REPO],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"  ✅ Secret saved → {secret_name}")
        return True
    print(f"  ❌ gh secret set failed: {result.stderr.strip()}")
    print(f"     Manual command: gh secret set {secret_name} --body '...' --repo {GH_REPO}")
    return False


def auth_channel(ch: dict) -> bool:
    token_path = Path(__file__).parent / ch["token_file"]

    print(f"\n  Sign in with the Google account that owns {ch['handle']}")
    print(f"  (If already signed in to another account, use Chrome incognito or switch accounts)\n")
    print("  Opening browser now...")

    if not CLIENT_SECRET.exists():
        print(f"  ❌ client_secret.json not found at {CLIENT_SECRET}")
        print("  Download from Google Cloud Console → APIs & Services → Credentials")
        return False

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
        creds = flow.run_local_server(
            port=ch["port"],
            prompt="consent",
            open_browser=True,
        )
    except Exception as e:
        print(f"  ❌ OAuth failed: {e}")
        return False

    token_json = creds.to_json()
    token_path.write_text(token_json)
    print(f"  Token saved locally → {token_path.name}")

    return _save_secret(ch["secret_name"], token_json)


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up YouTube OAuth for Mahayukti channels")
    parser.add_argument(
        "--channel", "-c",
        choices=[c["id"] for c in CHANNELS],
        help="Run for a single channel only. Omit to run all 7 sequentially.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip channels whose token file already exists locally.",
    )
    args = parser.parse_args()

    targets = [c for c in CHANNELS if c["id"] == args.channel] if args.channel else CHANNELS

    if args.skip_existing:
        existing_before = [c for c in targets if (Path(__file__).parent / c["token_file"]).exists()]
        targets = [c for c in targets if not (Path(__file__).parent / c["token_file"]).exists()]
        if existing_before:
            print(f"Skipping (token exists): {', '.join(c['id'] for c in existing_before)}")

    if not targets:
        print("Nothing to do — all tokens already exist.")
        return

    print(f"\nSetting up {len(targets)} channel(s):")
    for i, ch in enumerate(targets):
        print(f"  {i + 1}. {ch['name']} ({ch['handle']})")

    print()
    print("For each channel, the browser will open.")
    print("Sign in to the Google account that manages THAT channel.")
    print("You can use different browser profiles or incognito for each.\n")

    failed = []
    for idx, ch in enumerate(targets):
        _bar(ch, len(targets), idx)
        ok = auth_channel(ch)
        if not ok:
            failed.append(ch["id"])
        if idx < len(targets) - 1:
            print("\n  Waiting 2 seconds before next channel...")
            import time
            time.sleep(2)

    print()
    print("=" * 60)
    if not failed:
        print("  ✅ All channels authorised and secrets saved!")
    else:
        print(f"  ⚠️  Completed with failures: {', '.join(failed)}")
        print("  Re-run with --channel <id> to retry specific channels.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Set ELEVENLABS_API_KEY   → elevenlabs.io (free tier)")
    print("  2. Set D_ID_API_KEY          → d-id.com (free: 20 credits)")
    print("  3. Set IMGBB_API_KEY         → imgbb.com/api (free)")
    print("  4. Set MAKE_LINKEDIN_WEBHOOK_URL for LinkedIn (MahaYukti)")
    print("  5. Upload character photos to GitHub releases + set CHARACTER_IMAGE_URL in each config")
    print()


if __name__ == "__main__":
    main()
