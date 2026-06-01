import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from config import TOKEN_FILE, CLIENT_SECRET_FILE, SCOPES


def _get_credentials() -> Credentials:
    creds = None

    # In CI: token JSON is stored as a GitHub secret env var
    token_env = os.getenv("YOUTUBE_TOKEN_JSON", "{}")
    if token_env and token_env != "{}":
        creds = Credentials.from_authorized_user_info(json.loads(token_env), SCOPES)

    # Locally: read from file
    elif Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # First-time local auth (opens browser)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    # Always persist so the CI token-refresh step can read it back
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    return creds


def upload_video(
    video_path: str,
    thumbnail_path: str,
    title: str,
    description: str,
    tags: list[str],
    category_id: str = "27",  # 27 = Education
) -> str:
    creds = _get_credentials()
    yt = build("youtube", "v3", credentials=creds)

    # Ensure YouTube classifies this as a Short
    if "#Shorts" not in title:
        title = (title[:93] + " #Shorts") if len(title) > 93 else title + " #Shorts"

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": category_id,
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024,  # 8 MB chunks
    )

    print("  Uploading to YouTube...")
    request = yt.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  Upload: {pct}%")

    video_id = response["id"]
    print(f"  Video live: https://youtube.com/watch?v={video_id}")

    # Set custom thumbnail (requires verified channel with custom thumbnails enabled)
    if Path(thumbnail_path).exists():
        try:
            yt.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
            ).execute()
            print("  Thumbnail set.")
        except HttpError as e:
            print(f"  Thumbnail skipped: {e.reason}")

    return video_id
