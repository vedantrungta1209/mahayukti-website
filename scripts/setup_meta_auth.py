#!/usr/bin/env python3
"""
Run ONCE locally to get Facebook/Instagram tokens for direct posting.

Usage: python scripts/setup_meta_auth.py
"""
import http.server, threading, urllib.parse, webbrowser, requests, sys

APP_ID     = input("Meta App ID: ").strip()
APP_SECRET = input("Meta App Secret: ").strip()
GH_REPO    = "vedantrungta1209/mahayukti-website"

REDIRECT_URI = "http://localhost:8766/callback"
SCOPES = (
    "pages_manage_posts,pages_show_list,pages_read_engagement,"
    "instagram_basic,instagram_content_publish,business_management"
)

auth_url = (
    "https://www.facebook.com/v19.0/dialog/oauth?"
    + urllib.parse.urlencode({
        "client_id":    APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope":        SCOPES,
        "response_type":"code",
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


server = http.server.HTTPServer(("localhost", 8766), _Handler)
t = threading.Thread(target=server.handle_request)
t.start()

print("\nOpening browser for Meta authorization...")
webbrowser.open(auth_url)
t.join(timeout=120)

code = code_holder.get("code", "")
if not code:
    print("No authorization code received.")
    raise SystemExit(1)

# Exchange for short-lived user token
r = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
    "client_id":     APP_ID,
    "redirect_uri":  REDIRECT_URI,
    "client_secret": APP_SECRET,
    "code":          code,
}, timeout=30)
r.raise_for_status()
short_token = r.json()["access_token"]

# Exchange for long-lived user token
r = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
    "grant_type":        "fb_exchange_token",
    "client_id":         APP_ID,
    "client_secret":     APP_SECRET,
    "fb_exchange_token": short_token,
}, timeout=30)
r.raise_for_status()
long_user_token = r.json()["access_token"]

# Try me/accounts first (direct page admin)
pages_resp = requests.get("https://graph.facebook.com/v19.0/me/accounts", params={
    "fields": "id,name,access_token",
    "access_token": long_user_token,
}, timeout=30)
pages = pages_resp.json().get("data", [])

# Fallback: list pages via Business Manager
if not pages:
    print("me/accounts empty — trying Business Manager...")
    biz_resp = requests.get("https://graph.facebook.com/v19.0/me/businesses", params={
        "fields": "id,name",
        "access_token": long_user_token,
    }, timeout=30)
    businesses = biz_resp.json().get("data", [])
    print("Businesses found:", [(b["name"], b["id"]) for b in businesses])
    for biz in businesses:
        owned = requests.get(
            f"https://graph.facebook.com/v19.0/{biz['id']}/owned_pages",
            params={"fields": "id,name,access_token", "access_token": long_user_token},
            timeout=30,
        )
        pages.extend(owned.json().get("data", []))
        client = requests.get(
            f"https://graph.facebook.com/v19.0/{biz['id']}/client_pages",
            params={"fields": "id,name,access_token", "access_token": long_user_token},
            timeout=30,
        )
        pages.extend(client.json().get("data", []))

if not pages:
    print("\nNo Facebook Pages found via any method.")
    print("Make sure you are an admin of the MahaYukti Facebook Page.")
    raise SystemExit(1)

print("\nYour Facebook Pages:")
for i, p in enumerate(pages):
    print(f"  [{i}] {p['name']} (ID: {p['id']})")

idx        = int(input("\nSelect page index: ").strip())
page       = pages[idx]
page_id    = page["id"]
page_token = page["access_token"]

# Get linked Instagram Business account
ig_resp = requests.get(
    f"https://graph.facebook.com/v19.0/{page_id}",
    params={"fields": "instagram_business_account", "access_token": page_token},
    timeout=30,
)
ig_data    = ig_resp.json()
ig_user_id = ig_data.get("instagram_business_account", {}).get("id", "")

if not ig_user_id:
    print("\nNo Instagram Business account linked to this page.")
    print("Link it in Meta Business Suite → Instagram accounts.")

print("\n\n" + "=" * 60)
print("Run these commands to set your GitHub secrets:")
print("=" * 60 + "\n")

secrets = {
    "FB_PAGE_ACCESS_TOKEN": page_token,
    "FB_PAGE_ID":           page_id,
}
if ig_user_id:
    secrets["IG_USER_ID"] = ig_user_id

for name, value in secrets.items():
    print(f'gh secret set {name} --body "{value}" --repo {GH_REPO}')

print("\nNote: FB_PAGE_ACCESS_TOKEN never expires if generated correctly.")
print("Done.")
