"""
Vee Content Automation Pipeline
Run: python main.py
"""

import os
import sys
from pathlib import Path

from config import OUTPUT_DIR
from topics import get_todays_topic
from script_generator import generate_script
from audio_generator import generate_audio
from video_composer import compose_video
from thumbnail_generator import generate_thumbnail
from youtube_uploader import upload_video


def run():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    print("=" * 50)
    print("  Vee Content Automation Pipeline")
    print("=" * 50)

    # 1. Pick today's topic
    topic = get_todays_topic()
    print(f"\n[1/6] Topic: {topic['angle']}")
    print(f"      Category: {topic['category']}")

    # 2. Generate script via Gemini
    print("\n[2/6] Generating script (Gemini Flash)...")
    script_data = generate_script(topic)
    print(f"      Title: {script_data['title']}")

    # 3. Generate voiceover via edge-tts (free, no API key)
    print("\n[3/6] Generating voiceover (edge-tts)...")
    audio_path = f"{OUTPUT_DIR}/audio.mp3"
    generate_audio(script_data["script"], audio_path)

    # 4. Generate video frames + compose final video
    print("\n[4/6] Composing video...")
    video_path = f"{OUTPUT_DIR}/video.mp4"
    compose_video(audio_path, script_data, video_path)

    # 5. Generate thumbnail
    print("\n[5/6] Generating thumbnail...")
    thumb_path = f"{OUTPUT_DIR}/thumbnail.jpg"
    generate_thumbnail(script_data["title"], script_data["thumbnail_text"], thumb_path)

    # 6. Upload to YouTube
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
    print("=" * 50)


if __name__ == "__main__":
    missing = []
    if not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)
    run()
