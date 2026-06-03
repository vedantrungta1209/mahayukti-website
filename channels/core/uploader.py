"""
YouTube Data API v3 upload.
Reads OAuth token from environment variable (same pattern as old system).
"""
import json
import os
import tempfile
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def _get_credentials(token_env_var: str) -> Credentials:
    token_json = os.environ[token_env_var]
    data = json.loads(token_json)
    creds = Credentials(
        token=data.get("token"),
        refresh_token=data["refresh_token"],
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def upload(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    token_env_var: str,
    is_short: bool = False,
    privacy: str = "public",
) -> str:
    """
    Upload video to YouTube. Returns the video ID.
    For Shorts: title should already contain #Shorts, and video must be ≤60s, 9:16.
    """
    creds = _get_credentials(token_env_var)
    youtube = build("youtube", "v3", credentials=creds)

    if is_short and "#Shorts" not in title:
        title = f"{title} #Shorts"

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": "22",   # People & Blogs — works broadly; change per channel if needed
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  uploading… {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"  ✓ uploaded: https://youtu.be/{video_id}")
    return video_id
