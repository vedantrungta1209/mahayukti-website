"""
Cross-post a short video (MP4) to Instagram Reels + Facebook Reels + LinkedIn.
Used by finance-short, crime trailer, and any future channel that produces a Short.
No extra dependencies beyond `requests` (already in channels/requirements.txt).
"""
import os
import time

import requests

_GRAPH_URL = "https://graph.facebook.com/v22.0"


def _upload_to_host(file_path: str) -> str | None:
    filename = os.path.basename(file_path)

    # Host 1: 0x0.st — 512 MB limit, no account needed
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://0x0.st", files={"file": (filename, f)}, timeout=120)
        if r.status_code == 200:
            url = r.text.strip()
            print(f"  Hosted (0x0.st): {url}")
            return url
    except Exception as e:
        print(f"  0x0.st failed: {e}")

    # Host 2: transfer.sh fallback
    try:
        with open(file_path, "rb") as f:
            r = requests.put(
                f"https://transfer.sh/{filename}",
                data=f,
                headers={"Max-Downloads": "5", "Max-Days": "1"},
                timeout=120,
            )
        if r.status_code == 200:
            url = r.text.strip()
            print(f"  Hosted (transfer.sh): {url}")
            return url
    except Exception as e:
        print(f"  transfer.sh failed: {e}")

    return None


def post_ig_reel(video_path: str, caption: str) -> bool:
    ig_id    = os.environ.get("IG_USER_ID", "")
    fb_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
    if not ig_id or not fb_token:
        print("  Instagram: credentials missing — skipping.")
        return False

    video_url = _upload_to_host(video_path)
    if not video_url:
        print("  Instagram: could not host video — skipping.")
        return False

    # Create media container
    r = requests.post(
        f"{_GRAPH_URL}/{ig_id}/media",
        params={"media_type": "REELS", "video_url": video_url,
                "caption": caption[:2200], "access_token": fb_token},
        timeout=30,
    )
    if r.status_code != 200 or "id" not in r.json():
        print(f"  Instagram container error: {r.text[:200]}")
        return False

    container_id = r.json()["id"]

    # Poll until ready
    for _ in range(20):
        time.sleep(10)
        s = requests.get(
            f"{_GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": fb_token},
            timeout=15,
        ).json().get("status_code", "")
        if s == "FINISHED":
            break
        if s == "ERROR":
            print("  Instagram container processing error.")
            return False

    # Publish
    p = requests.post(
        f"{_GRAPH_URL}/{ig_id}/media_publish",
        params={"creation_id": container_id, "access_token": fb_token},
        timeout=30,
    )
    ok = p.status_code == 200 and "id" in p.json()
    print(f"  Instagram: {'✅ posted' if ok else '⚠️ publish failed'}")
    return ok


def post_fb_reel(video_path: str, caption: str) -> bool:
    fb_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
    fb_page  = os.environ.get("FB_PAGE_ID", "")
    if not fb_token or not fb_page:
        print("  Facebook: credentials missing — skipping.")
        return False

    video_url = _upload_to_host(video_path)
    if not video_url:
        print("  Facebook: could not host video — skipping.")
        return False

    r = requests.post(
        f"{_GRAPH_URL}/{fb_page}/video_reels",
        params={"upload_phase": "finish", "video_url": video_url,
                "title": caption[:100], "description": caption[:2000],
                "access_token": fb_token},
        timeout=60,
    )
    ok = r.status_code == 200
    print(f"  Facebook: {'✅ posted' if ok else f'⚠️ failed — {r.text[:100]}'}")
    return ok


def post_linkedin(text: str) -> bool:
    make_url = os.environ.get("MAKE_WEBHOOK_URL", "")
    if not make_url:
        print("  LinkedIn: MAKE_WEBHOOK_URL not set — skipping.")
        return False
    try:
        r = requests.post(make_url, json={"text": text[:3000]}, timeout=20)
        ok = r.status_code < 300
        print(f"  LinkedIn: {'✅ posted' if ok else f'⚠️ failed ({r.status_code})'}")
        return ok
    except Exception as e:
        print(f"  LinkedIn: ⚠️ {e}")
        return False


def cross_post_short(video_path: str, ig_caption: str, li_text: str = "",
                     skip_instagram: bool = False, skip_facebook: bool = False,
                     skip_linkedin: bool = False) -> None:
    """Post a short video to IG + FB. Optionally post a LinkedIn text update."""
    print("\n📲 Cross-posting to social platforms...")
    if not skip_instagram:
        post_ig_reel(video_path, ig_caption)
    if not skip_facebook:
        post_fb_reel(video_path, ig_caption)
    if li_text and not skip_linkedin:
        post_linkedin(li_text)
