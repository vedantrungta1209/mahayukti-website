"""
Cross-post a short video (MP4) to Instagram Reels + Facebook Reels + LinkedIn.
Used by finance-short, crime trailer, and any future channel that produces a Short.
No extra dependencies beyond `requests` (already in channels/requirements.txt).
"""
import base64
import os
import time
from pathlib import Path

import requests

_GRAPH_URL = "https://graph.facebook.com/v22.0"
_GH_REPO   = "vedantrungta1209/mahayukti-website"
_MAX_UPLOAD = 50 * 1024 * 1024   # 50 MB — GitHub Contents API practical limit


def _upload_to_host(file_path: str) -> str | None:
    """Upload file to GitHub repo; served publicly via mahayukti.com."""
    gh_token = os.environ.get("GH_TOKEN", "")
    if not gh_token:
        print("  GH_TOKEN missing — cannot host file.")
        return None

    file_size = os.path.getsize(file_path)
    if file_size > _MAX_UPLOAD:
        print(f"  File {file_size // 1024 // 1024}MB > 50MB limit — skipping.")
        return None

    filename = os.path.basename(file_path)
    # Images go to thumbs sub-folder; videos go to shorts
    is_image = filename.lower().endswith((".jpg", ".jpeg", ".png"))
    repo_dir = "images/shorts/thumbs" if is_image else "images/shorts"
    api_url  = f"https://api.github.com/repos/{_GH_REPO}/contents/{repo_dir}/{filename}"
    headers  = {"Authorization": f"token {gh_token}",
                "Accept": "application/vnd.github.v3+json"}

    encoded = base64.b64encode(Path(file_path).read_bytes()).decode()
    check   = requests.get(api_url, headers=headers, timeout=15)
    sha     = check.json().get("sha") if check.status_code == 200 else None

    payload = {"message": f"shorts: {filename}", "content": encoded, "branch": "main"}
    if sha:
        payload["sha"] = sha

    try:
        r = requests.put(api_url, headers=headers, json=payload, timeout=180)
        r.raise_for_status()
        url = f"https://mahayukti.com/{repo_dir}/{filename}"
        print(f"  Hosted (GitHub): {url}")
        return url
    except Exception as e:
        print(f"  GitHub hosting failed: {e}")
        return None


def post_ig_reel(video_path: str, caption: str, thumbnail_path: str | None = None) -> bool:
    ig_id    = os.environ.get("IG_USER_ID", "")
    fb_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
    if not ig_id or not fb_token:
        print("  Instagram: credentials missing — skipping.")
        return False

    video_url = _upload_to_host(video_path)
    if not video_url:
        print("  Instagram: could not host video — skipping.")
        return False

    # Upload thumbnail if provided
    thumb_url = None
    if thumbnail_path:
        thumb_url = _upload_to_host(thumbnail_path)

    # Create media container
    params = {
        "media_type":   "REELS",
        "video_url":    video_url,
        "caption":      caption[:2200],
        "access_token": fb_token,
    }
    if thumb_url:
        params["thumbnail_url"] = thumb_url

    r = requests.post(
        f"{_GRAPH_URL}/{ig_id}/media",
        params=params,
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
        r = requests.post(make_url, json={"linkedin_text": text[:3000]}, timeout=20)
        ok = r.status_code < 300
        print(f"  LinkedIn: {'✅ posted' if ok else f'⚠️ failed ({r.status_code})'}")
        return ok
    except Exception as e:
        print(f"  LinkedIn: ⚠️ {e}")
        return False


def cross_post_short(video_path: str, ig_caption: str, li_text: str = "",
                     skip_instagram: bool = False, skip_facebook: bool = False,
                     skip_linkedin: bool = False,
                     thumbnail_path: str | None = None) -> None:
    """Post a short video to IG + FB. Optionally post a LinkedIn text update."""
    print("\n📲 Cross-posting to social platforms...")
    if not skip_instagram:
        post_ig_reel(video_path, ig_caption, thumbnail_path=thumbnail_path)
    if not skip_facebook:
        post_fb_reel(video_path, ig_caption)
    if li_text and not skip_linkedin:
        post_linkedin(li_text)
