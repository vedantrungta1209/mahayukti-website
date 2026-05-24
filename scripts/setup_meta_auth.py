#!/usr/bin/env python3
"""
Run ONCE locally to get Facebook/Instagram tokens for direct posting.

Usage: python3 scripts/setup_meta_auth.py
"""
import urllib.parse, requests, sys

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

print("\n" + "=" * 60)
print("STEP 1: Open this URL in your browser:")
print("=" * 60)
print(auth_url)
print("\nAfter you authorize, your browser will redirect to a URL")
print("starting with: http://localhost:8766/callback?code=...")
print("The page may show an error — that's fine.")
print("\nSTEP 2: Copy the FULL URL from your browser's address bar")
print("and paste it here.")
print("=" * 60)

redirect_url = input("\nPaste the full redirect URL here: ").strip()

parsed = urllib.parse.urlparse(redirect_url)
qs     = urllib.parse.parse_qs(parsed.query)
code   = qs.get("code", [""])[0]

if not code:
    print("No code found in URL. Make sure you copied the full URL after authorizing.")
    raise SystemExit(1)

print("Got authorization code. Exchanging for token...")

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
print("Got long-lived user token.")

# Try me/accounts first (direct page admin)
pages_resp = requests.get("https://graph.facebook.com/v19.0/me/accounts", params={
    "fields": "id,name,access_token",
    "access_token": long_user_token,
}, timeout=30)
pages = pages_resp.json().get("data", [])

# Fallback: list pages via Business Manager
if not pages:
    print("Trying Business Manager API...")
    biz_resp = requests.get("https://graph.facebook.com/v19.0/me/businesses", params={
        "fields": "id,name",
        "access_token": long_user_token,
    }, timeout=30)
    businesses = biz_resp.json().get("data", [])
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
    print("\nNo Facebook Pages found. Make sure you are an admin of the MahaYukti Facebook Page.")
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
