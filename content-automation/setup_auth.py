"""
Run this ONCE locally to authenticate with your YouTube channel.
It opens a browser — sign in with the Google account that owns your channel.

Usage:
  python setup_auth.py

After running:
  1. A youtube_token.json file is created in this directory.
  2. Copy its contents and add it as a GitHub Secret named YOUTUBE_TOKEN_JSON.
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from config import CLIENT_SECRET_FILE, SCOPES, TOKEN_FILE

print("Opening browser for YouTube authorization...")
print(f"Make sure '{CLIENT_SECRET_FILE}' is in this directory first.\n")

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print(f"\nSaved: {TOKEN_FILE}")
print("\n--- Copy this JSON as your YOUTUBE_TOKEN_JSON GitHub Secret ---\n")
print(creds.to_json())
print("\n----------------------------------------------------------------")
