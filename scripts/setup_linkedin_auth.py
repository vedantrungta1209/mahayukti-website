#!/usr/bin/env python3
"""
Run ONCE locally to get LinkedIn OAuth tokens for personal profile posting.

Prerequisites:
  1. Create a LinkedIn Developer App at https://developer.linkedin.com
  2. Add products: "Share on LinkedIn" + "Sign In with LinkedIn using OpenID Connect"
  3. Add redirect URL: http://localhost:8765/callback

Usage: python scripts/setup_linkedin_auth.py
"""
import http.server, threading, time, urllib.parse, webbrowser, requests

CLIENT_ID     = input("LinkedIn App Client ID: ").strip()
CLIENT_SECRET = input("LinkedIn App Client Secret: ").strip()

REDIRECT_URI = "http://localhost:8765/callback"
SCOPES       = "w_member_social openid profile email"
GH_REPO      = "vedantrungta1209/mahayukti-website"

auth_url = (
    "https://www.linkedin.com/oauth/v2/authorization?"
    + urllib.parse.urlencode({
        "response_type": "code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         SCOPES,
        "state":         "mahayukti",
    })
)

code_holder: dict = {}


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code_holder["code"] = qs.get("code", [""])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Authorization complete. Close this tab.</h2>")
    def log_message(self, *args): pass


server = http.server.HTTPServer(("localhost", 8765), _Handler)
t = threading.Thread(target=server.handle_request)
t.start()

print("\nOpening browser for LinkedIn authorization...")
webbrowser.open(auth_url)
t.join(timeout=120)

code = code_holder.get("code", "")
if not code:
    print("No authorization code received. Check that the redirect URI is registered in your app.")
    raise SystemExit(1)

# Exchange code for tokens
r = requests.post(
    "https://www.linkedin.com/oauth/v2/accessToken",
    data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
)
r.raise_for_status()
data = r.json()
access_token  = data["access_token"]
refresh_token = data.get("refresh_token", "")

# Fetch person URN via userinfo endpoint
me = requests.get(
    "https://api.linkedin.com/v2/userinfo",
    headers={"Authorization": f"Bearer {access_token}"},
    timeout=15,
)
me.raise_for_status()
person_id  = me.json()["sub"]
author_urn = f"urn:li:person:{person_id}"
name       = me.json().get("name", "your profile")

print(f"\nAuthorized as: {name}")
print(f"Person URN: {author_urn}")

now = str(int(time.time()))

print("\n\n" + "=" * 60)
print("Run these commands to set your GitHub secrets:")
print("=" * 60 + "\n")

secrets = {
    "LINKEDIN_ACCESS_TOKEN":    access_token,
    "LINKEDIN_REFRESH_TOKEN":   refresh_token,
    "LINKEDIN_CLIENT_ID":       CLIENT_ID,
    "LINKEDIN_CLIENT_SECRET":   CLIENT_SECRET,
    "LINKEDIN_AUTHOR_URN":      author_urn,
    "LINKEDIN_TOKEN_ISSUED_AT": now,
}

for name_k, value in secrets.items():
    print(f'gh secret set {name_k} --body "{value}" --repo {GH_REPO}')

if not refresh_token:
    print("\nNote: No refresh token received. LinkedIn only issues refresh tokens")
    print("if your app has 'offline_access' scope. Posts will still work for 60 days.")
