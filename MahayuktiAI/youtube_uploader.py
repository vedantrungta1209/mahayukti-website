import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import TOKEN_FILE, SCOPES

_ENV_VAR = "YOUTUBE_AI_TOKEN_JSON"


def _get_credentials() -> Credentials:
    creds = None
    token_json = os.environ.get(_ENV_VAR, "")

    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    elif Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        raise RuntimeError(f"No valid YouTube credentials. Set {_ENV_VAR} secret or run setup_auth.py")

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    return creds


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    category_id: str = "28",   # Science & Technology
    privacy: str = "public",
    made_for_kids: bool = False,
    is_short: bool = False,
) -> str:
    creds = _get_credentials()
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
            "privacyStatus":          privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload: {int(status.progress() * 100)}%")

    video_id = response["id"]
    video_type = "Short" if is_short else "Video"
    print(f"  {video_type} uploaded: https://youtube.com/watch?v={video_id}")
    return video_id
