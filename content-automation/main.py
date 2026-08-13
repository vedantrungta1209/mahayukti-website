"""
Mahayukti Finance — Content Pipeline
YouTube only. Runs once daily via GitHub Actions.
"""

import os
import sys
from pathlib import Path

from config import OUTPUT_DIR, CHANNEL_HANDLE
from topics import get_todays_topic
from script_generator import generate_script
from audio_generator import generate_audio
from video_composer import compose_video
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_video


def run():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    print("=" * 50)
    print("  Mahayukti Finance — Content Pipeline")
    print("=" * 50)

    topic = get_todays_topic()
    print(f"\n[1/6] Topic: {topic['angle']}")
    print(f"      Category: {topic['category']}")

    print("\n[2/6] Generating script...")
    script_data = generate_script(topic)
    print(f"      Title: {script_data['title']}")

    # Thread category + angle into script_data for frame generator
    script_data["_category"] = topic["category"]
    script_data["_angle"]    = topic["angle"]

    print("\n[3/6] Generating voiceover + music...")
    audio_path = f"{OUTPUT_DIR}/audio.mp3"
    srt_path   = f"{OUTPUT_DIR}/subtitles.srt"
    # Use counter value as music seed so each video gets a different ambient preset
    from topics import COUNTER_FILE
    try:
        music_seed = int(COUNTER_FILE.read_text().strip()) if COUNTER_FILE.exists() else 0
    except Exception:
        music_seed = 0
    generate_audio(script_data["script"], audio_path, srt_path, music_seed=music_seed)

    print("\n[4/6] Composing video...")
    video_path = f"{OUTPUT_DIR}/video.mp4"
    compose_video(audio_path, script_data, video_path, srt_path)

    print("\n[5/6] Generating thumbnail...")
    thumb_path = f"{OUTPUT_DIR}/thumbnail.jpg"
    generate_thumbnail(
        script_data["title"],
        script_data["thumbnail_text"],
        thumb_path,
        category=topic["category"],
    )

    print("\n[6/6] Uploading to YouTube...")
    video_id = upload_video(
        video_path=video_path,
        thumbnail_path=thumb_path,
        title=script_data["title"],
        description=script_data["description"],
        tags=script_data["tags"],
    )

    print("\n" + "=" * 50)
    print(f"  Done! https://youtube.com/watch?v={video_id}")
    print(f"  Channel: https://youtube.com/{CHANNEL_HANDLE}")
    print("=" * 50)


if __name__ == "__main__":
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        sys.exit(1)
    run()
