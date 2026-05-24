#!/usr/bin/env python3
"""
One-time OAuth setup for Mahayukti AI YouTube channel (@mahayuktiAI).
Run this locally, then paste the token into GitHub secret YOUTUBE_AI_TOKEN_JSON.

Usage:
  1. Drop client_secret.json in this folder
  2. python3 setup_auth.py
  3. Browser opens — sign in with @mahayuktiAI Google account
  4. Token saved to youtube_ai_token.json automatically
  5. Script prints the gh secret set command to run
"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES        = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = "client_secret.json"
TOKEN_FILE    = "youtube_ai_token.json"


def main():
    if not Path(CLIENT_SECRET).exists():
        print(f"ERROR: {CLIENT_SECRET} not found in {Path.cwd()}")
        print("Download it from Google Cloud Console → APIs & Services → Credentials")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    print("\nOpening browser — sign in with the @mahayuktiAI Google account...")
    creds = flow.run_local_server(port=8080, prompt="consent", open_browser=True)

    Path(TOKEN_FILE).write_text(creds.to_json())
    print(f"\nToken saved to {TOKEN_FILE}")
    print("\nNow run this to add it to GitHub:")
    print(f'  gh secret set YOUTUBE_AI_TOKEN_JSON --body "$(cat {TOKEN_FILE})" --repo vedantrungta1209/mahayukti-website')


if __name__ == "__main__":
    main()
