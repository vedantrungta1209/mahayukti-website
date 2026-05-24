#!/usr/bin/env python3
"""
One-time OAuth setup for Mahayukti AI YouTube channel (@mahayuktiAI).
Run this locally, then paste the token into GitHub secret YOUTUBE_AI_TOKEN_JSON.

Usage:
  1. Drop client_secret.json in this folder
  2. python setup_auth.py
  3. A URL will be printed — open it, authorise with @mahayuktiAI account
  4. Paste the full URL you land on back into the terminal
  5. Token saved to youtube_ai_token.json — paste its contents into GitHub secret
"""
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = "client_secret.json"
TOKEN_FILE    = "youtube_ai_token.json"


def main():
    if not Path(CLIENT_SECRET).exists():
        print(f"ERROR: {CLIENT_SECRET} not found in {Path.cwd()}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET, SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )

    auth_url, _ = flow.authorization_url(prompt="consent")
    print("\n" + "=" * 60)
    print("Open this URL in your browser (log in as @mahayuktiAI account):")
    print("=" * 60)
    print(auth_url)
    print("=" * 60)
    code = input("\nPaste the authorisation code shown after login: ").strip()

    flow.fetch_token(code=code)
    creds = flow.credentials

    Path(TOKEN_FILE).write_text(creds.to_json())
    print(f"\nToken saved to {TOKEN_FILE}")
    print("\nNow run:")
    print(f'  gh secret set YOUTUBE_AI_TOKEN_JSON --body "$(cat {TOKEN_FILE})" --repo vedantrungta1209/mahayukti-website')


if __name__ == "__main__":
    main()
