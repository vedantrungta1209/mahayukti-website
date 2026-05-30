"""
Cross-post YouTube Shorts to Instagram Reels + Facebook Reels.
Uses the same video file produced for YouTube — no extra rendering needed.
"""
import os
import time

import requests

from config import IG_USER_ID, FB_PAGE_ACCESS_TOKEN, FB_PAGE_ID

_GRAPH_URL = "https://graph.facebook.com/v22.0"


def _ig_post_reel(video_path: str, caption: str) -> str | None:
    ig_id    = os.environ.get("IG_USER_ID", IG_USER_ID)
    fb_token = os.environ.get("FB_PAGE_ACCESS_TOKEN", FB_PAGE_ACCESS_TOKEN)

    if not ig_id or not fb_token:
        print("  Instagram: credentials not set, skipping.")
        return None

    # Step 1: Upload video to server-accessible URL (use FB video upload endpoint)
    print("  Instagram: initiating reel upload...")

    # Instagram requires a publicly accessible URL.
    # We first upload to Facebook (which shares the same graph API) then cross-post.
    # Alternatively, use the resumable upload via IG container approach.

    # Create container
    container_url = f"{_GRAPH_URL}/{ig_id}/reels"
    with open(video_path, "rb") as f:
        video_data = f.read()

    # Use resumable upload
    init_resp = requests.post(
        f"{_GRAPH_URL}/{ig_id}/media",
        params={
            "media_type": "REELS",
            "video_url":  "__upload__",  # placeholder, will use upload_type
            "caption":    caption[:2200],
            "access_token": fb_token,
            "upload_type": "resumable",
        },
    )

    # Instagram Reels upload requires a publicly hosted video URL
    # Without one we skip — handled by hosting video on a temp URL via transfer.sh
    print("  Instagram: direct file upload requires hosted URL — using transfer.sh...")
    return _ig_post_via_transfer(video_path, caption, ig_id, fb_token)


def _upload_to_host(file_path: str) -> str | None:
    """Upload video to a public URL using multiple free hosts (tried in order)."""
    filename = os.path.basename(file_path)

    # Host 1: 0x0.st — reliable, no account needed, 512MB limit
    try:
        with open(file_path, "rb") as f:
            r = requests.post("https://0x0.st", files={"file": (filename, f)}, timeout=120)
        if r.status_code == 200:
            url = r.text.strip()
            print(f"  Hosted (0x0.st): {url}")
            return url
    except Exception as e:
        print(f"  0x0.st failed: {e}")

    # Host 2: transfer.sh — fallback
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

    print("  All video hosts failed — Instagram/Facebook cross-post skipped.")
    return None


def _ig_post_via_transfer(video_path: str, caption: str, ig_id: str, fb_token: str) -> str | None:
    video_url = _upload_to_host(video_path)
    if not video_url:
        print("  Instagram: could not host video, skipping.")
        return None

    # Create media container
    r = requests.post(
        f"{_GRAPH_URL}/{ig_id}/media",
        params={
            "media_type":   "REELS",
            "video_url":    video_url,
            "caption":      caption[:2200],
            "access_token": fb_token,
        },
    )
    if r.status_code != 200:
        print(f"  Instagram container error: {r.text[:200]}")
        return None

    container_id = r.json().get("id")
    if not container_id:
        print(f"  Instagram: no container ID in response")
        return None

    print(f"  Instagram container: {container_id} — waiting for processing...")

    # Poll for processing
    for _ in range(18):
        time.sleep(10)
        status_r = requests.get(
            f"{_GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": fb_token},
        )
        status = status_r.json().get("status_code", "")
        print(f"  Instagram status: {status}")
        if status == "FINISHED":
            break
        if status == "ERROR":
            print("  Instagram: processing error.")
            return None

    # Publish
    pub_r = requests.post(
        f"{_GRAPH_URL}/{ig_id}/media_publish",
        params={"creation_id": container_id, "access_token": fb_token},
    )
    if pub_r.status_code == 200:
        media_id = pub_r.json().get("id", "")
        print(f"  Instagram Reel published: {media_id}")
        return media_id
    else:
        print(f"  Instagram publish error: {pub_r.text[:200]}")
        return None


def _fb_post_reel(video_path: str, caption: str) -> str | None:
    fb_token  = os.environ.get("FB_PAGE_ACCESS_TOKEN", FB_PAGE_ACCESS_TOKEN)
    fb_page   = os.environ.get("FB_PAGE_ID", FB_PAGE_ID)

    if not fb_token or not fb_page:
        print("  Facebook: credentials not set, skipping.")
        return None

    print("  Facebook: uploading reel...")

    video_url = _upload_to_host(video_path)
    if not video_url:
        print("  Facebook: could not host video, skipping.")
        return None

    r = requests.post(
        f"{_GRAPH_URL}/{fb_page}/videos",
        params={
            "file_url":     video_url,
            "description":  caption[:5000],
            "published":    "true",
            "access_token": fb_token,
        },
    )
    if r.status_code == 200:
        video_id = r.json().get("id", "")
        print(f"  Facebook Reel posted: {video_id}")
        return video_id
    else:
        print(f"  Facebook post error: {r.text[:200]}")
        return None


def post_to_social(video_path: str, caption: str, post_instagram: bool = True, post_facebook: bool = True) -> dict:
    results = {}
    if post_instagram:
        results["instagram"] = _ig_post_via_transfer(
            video_path, caption,
            ig_id=os.environ.get("IG_USER_ID", IG_USER_ID),
            fb_token=os.environ.get("FB_PAGE_ACCESS_TOKEN", FB_PAGE_ACCESS_TOKEN),
        )
    if post_facebook:
        results["facebook"] = _fb_post_reel(video_path, caption)
    return results
