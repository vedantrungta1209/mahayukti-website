#!/usr/bin/env python3
"""
Run ONCE locally to get Facebook/Instagram tokens for direct posting.

Prerequisites:
  1. Create a Meta Developer App at https://developers.facebook.com
  2. Add "Facebook Login" and "Instagram Graph API" products
  3. Connect your Facebook Page and Instagram Business/Creator account
  4. Add redirect URI: http://localhost:8766/callback
  5. Grant permissions: pages_manage_posts, pages_read_engagement,
     instagram_basic, instagram_content_publish, pages_show_list

Usage: python scripts/setup_meta_auth.py
"""
import http.server, threading, urllib.parse, webbrowser, requests

APP_ID     = input("Meta App ID: ").strip()
APP_SECRET = input("Meta App Secret: ").strip()
GH_REPO    = "vedantrungta1209/mahayukti-website"

REDIRECT_URI = "http://localhost:8766/callback"
SCOPES = (
    "pages_manage_posts,pages_show_list,pages_read_engagement,"
    "instagram_basic,instagram_content_publish"
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
    print("No authorization code received. Check that redirect URI is registered in your Meta app.")
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

# Exchange for long-lived user token (60 days, needed to get permanent Page token)
r = requests.get("https://graph.facebook.com/v19.0/oauth/access_token", params={
    "grant_type":       "fb_exchange_token",
    "client_id":        APP_ID,
    "client_secret":    APP_SECRET,
    "fb_exchange_token": short_token,
}, timeout=30)
r.raise_for_status()
long_user_token = r.json()["access_token"]

# Debug: check token permissions
me_resp = requests.get("https://graph.facebook.com/v19.0/me", params={
    "fields": "id,name",
    "access_token": long_user_token,
}, timeout=30)
print("Me:", me_resp.json())

perms_resp = requests.get("https://graph.facebook.com/v19.0/me/permissions", params={
    "access_token": long_user_token,
}, timeout=30)
print("Permissions:", perms_resp.json())

# List pages
pages_resp = requests.get("https://graph.facebook.com/v19.0/me/accounts", params={
    "fields": "id,name,access_token",
    "access_token": long_user_token,
}, timeout=30)
pages_resp.raise_for_status()
print("Raw pages response:", pages_resp.json())
pages = pages_resp.json().get("data", [])

if not pages:
    print("No Facebook Pages found for this account.")
    raise SystemExit(1)

print("\nYour Facebook Pages:")
for i, p in enumerate(pages):
    print(f"  [{i}] {p['name']} (ID: {p['id']})")

idx        = int(input("\nSelect page index: ").strip())
page       = pages[idx]
page_id    = page["id"]
page_token = page["access_token"]  # Long-lived Page Token — never expires

# Get linked Instagram Business/Creator account
ig_resp = requests.get(
    f"https://graph.facebook.com/v19.0/{page_id}",
    params={"fields": "instagram_business_account", "access_token": page_token},
    timeout=30,
)
ig_data    = ig_resp.json()
ig_user_id = ig_data.get("instagram_business_account", {}).get("id", "")

if not ig_user_id:
    print("\n⚠️  No Instagram Business/Creator account linked to this page.")
    print("   Go to Instagram → Settings → Account → Switch to Professional Account")
    print("   Then link it to your Facebook Page in Meta Business Suite.")

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

print("\nNote: FB_PAGE_ACCESS_TOKEN never expires if generated correctly from a long-lived user token.")
print("Done. Run each command above in your terminal (requires gh CLI authenticated).")
