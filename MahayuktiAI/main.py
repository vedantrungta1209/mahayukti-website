#!/usr/bin/env python3
"""
Mahayukti AI — YouTube + Instagram + Facebook Automation
  --mode short   : Generate + upload one "AI Tool of the Day" Short (~60s)
  --mode long    : Generate + upload one "Top 5 AI Tools" long-form video (~9 min)
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from config import OUTPUT_DIR, TOKEN_FILE
from tools_list import get_short_tool, get_long_tools
from script_generator import generate_short_script, generate_long_script
from audio_generator import generate_audio, SHORT_VOICE, LONG_VOICE
from video_composer import compose_short, compose_long, generate_thumbnail
from youtube_uploader import upload_video

COUNTER_SHORT = Path(__file__).parent / "tool_counter_short.txt"
COUNTER_LONG  = Path(__file__).parent / "tool_counter_long.txt"
GH_REPO       = "vedantrungta1209/mahayukti-website"


def _read_counter(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except Exception:
        return 0


def _write_counter(path: Path, value: int) -> None:
    path.write_text(str(value))


def _push_token_secret(secret_name: str) -> None:
    if not Path(TOKEN_FILE).exists():
        return
    token = Path(TOKEN_FILE).read_text()
    subprocess.run(
        ["gh", "secret", "set", secret_name, "--body", token, "--repo", GH_REPO],
        capture_output=True,
    )
    print(f"  Token refreshed → {secret_name}")


def _cleanup() -> None:
    if Path(OUTPUT_DIR).exists():
        shutil.rmtree(OUTPUT_DIR)


def run_short() -> None:
    print("=" * 60)
    print("  Mahayukti AI — SHORT (AI Tool of the Day)")
    print("=" * 60)

    idx  = _read_counter(COUNTER_SHORT)
    tool = get_short_tool(idx)
    print(f"  Tool #{idx}: {tool['name']} ({tool['category']})")

    print("  Generating script...")
    script = generate_short_script(tool)
    script["category"] = tool["category"]

    audio_path = f"{OUTPUT_DIR}/short_audio.mp3"
    srt_path   = f"{OUTPUT_DIR}/short_subtitles.srt"
    video_path = f"{OUTPUT_DIR}/short_video.mp4"

    print("  Generating audio + music...")
    generate_audio(script["script"], audio_path, srt_path, voice=SHORT_VOICE, music_seed=idx)

    print("  Composing video...")
    compose_short(audio_path, script, video_path, srt_path)

    # Upload to YouTube
    print("  Uploading to YouTube...")
    yt_video_id = upload_video(
        video_path=video_path,
        title=script.get("title", f"{tool['name']} — AI Tool of the Day"),
        description=script.get("description", ""),
        tags=script.get("tags", []),
        is_short=True,
    )

    _push_token_secret("YOUTUBE_AI_TOKEN_JSON")
    _write_counter(COUNTER_SHORT, idx + 1)
    _cleanup()
    print(f"  Done ✓  YouTube: https://youtube.com/watch?v={yt_video_id}")


def run_long() -> None:
    print("=" * 60)
    print("  Mahayukti AI — LONG (Top 5 AI Tools This Week)")
    print("=" * 60)

    idx   = _read_counter(COUNTER_LONG)
    tools = get_long_tools(idx)
    print(f"  Batch #{idx}: {', '.join(t['name'] for t in tools)}")

    print("  Generating script...")
    script = generate_long_script(tools)
    # Carry category from first tool for visual theming
    script["_first_category"] = tools[0]["category"] if tools else "Productivity"

    audio_path     = f"{OUTPUT_DIR}/long_audio.mp3"
    srt_path       = f"{OUTPUT_DIR}/long_subtitles.srt"
    video_path     = f"{OUTPUT_DIR}/long_video.mp4"
    thumbnail_path = f"{OUTPUT_DIR}/thumbnail.jpg"

    print("  Generating audio + music...")
    generate_audio(script["full_script"], audio_path, srt_path, voice=LONG_VOICE, music_seed=idx + 100)

    print("  Composing video...")
    compose_long(audio_path, script, video_path, srt_path)

    print("  Generating thumbnail...")
    generate_thumbnail(script, thumbnail_path)

    print("  Uploading to YouTube...")
    yt_video_id = upload_video(
        video_path=video_path,
        title=script.get("title", "Top 5 AI Tools for Indians This Week"),
        description=script.get("description", ""),
        tags=script.get("tags", []),
        is_short=False,
        thumbnail_path=thumbnail_path,
    )

    _push_token_secret("YOUTUBE_AI_TOKEN_JSON")
    _write_counter(COUNTER_LONG, idx + 1)
    _cleanup()
    print(f"  Done ✓  YouTube: https://youtube.com/watch?v={yt_video_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["short", "long"], required=True)
    args = parser.parse_args()

    if args.mode == "short":
        run_short()
    else:
        run_long()
