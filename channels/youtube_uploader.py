"""
YouTube uploader — configurable per channel via cfg object.
"""
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials(cfg) -> Credentials:
    token_file = Path(__file__).parent / cfg.TOKEN_FILE
    token_json = os.environ.get(cfg.TOKEN_ENV_VAR, "")
    creds = None

    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    elif token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        raise RuntimeError(
            f"No valid YouTube credentials for {cfg.CHANNEL_NAME}. "
            f"Set {cfg.TOKEN_ENV_VAR} secret or run setup_auth.py."
        )

    token_file.write_text(creds.to_json())
    return creds


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    cfg,
    category_id: str = "28",
    privacy: str = "public",
    made_for_kids: bool = False,
    is_short: bool = False,
    thumbnail_path: str | None = None,
) -> str:
    creds   = _get_credentials(cfg)
    youtube = build("youtube", "v3", credentials=creds)

    final_title = title
    if is_short and "#Shorts" not in title:
        final_title = f"{title} #Shorts"

    final_tags = list(tags) + (["Shorts", "YouTubeShorts"] if is_short else [])

    body = {
        "snippet": {
            "title":       final_title[:100],
            "description": description,
            "tags":        final_tags,
            "categoryId":  category_id,
        },
        "status": {
            "privacyStatus":           privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }

    media   = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload: {int(status.progress() * 100)}%")

    video_id   = response["id"]
    video_type = "Short" if is_short else "Video"
    print(f"  {video_type} uploaded: https://youtube.com/watch?v={video_id}")

    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            media_thumb = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            youtube.thumbnails().set(videoId=video_id, media_body=media_thumb).execute()
            print("  Thumbnail uploaded.")
        except Exception as e:
            print(f"  Thumbnail upload failed (needs verified channel): {e}")

    return video_id


def post_comment(video_id: str, text: str, cfg) -> None:
    """Post a comment on a video (appears as the channel owner's first comment)."""
    try:
        creds   = _get_credentials(cfg)
        youtube = build("youtube", "v3", credentials=creds)
        youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": text}
                    },
                }
            },
        ).execute()
        print("  Pinned comment posted.")
    except Exception as e:
        print(f"  Comment post skipped: {e}")
