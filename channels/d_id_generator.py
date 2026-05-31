"""
D-ID API wrapper — generates a talking-head character intro video.
Each channel has a named AI host (photo + voice) who introduces the topic.
Free tier: 20 credits (~20 intro clips). Paid: $5.99/mo for 100 credits.

Usage: set D_ID_API_KEY GitHub secret. If absent, channel skips character intro.
"""
import os
import subprocess
import time
from pathlib import Path

import requests

_BASE = "https://api.d-id.com"


def _api_key() -> str:
    return os.environ.get("D_ID_API_KEY", "")


def generate_character_intro(
    character_image_url: str,
    intro_text: str,
    output_path: str,
    elevenlabs_voice_id: str = "",
    elevenlabs_key: str = "",
    tts_voice: str = "en-IN-PrabhatNeural",
    max_wait: int = 300,
) -> bool:
    """
    Generate a talking-head intro clip via D-ID.
    Returns True and writes output_path on success; returns False on failure.
    """
    api_key = _api_key()
    if not api_key:
        return False

    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
    }

    # Build voice provider
    el_key = elevenlabs_key or os.environ.get("ELEVENLABS_API_KEY", "")
    if el_key and elevenlabs_voice_id:
        voice_provider = {
            "type": "elevenlabs",
            "voice_id": elevenlabs_voice_id,
            "voice_config": {
                "model_id": "eleven_multilingual_v2",
                "stability": 0.5,
                "similarity_boost": 0.8,
            },
        }
    else:
        voice_provider = {
            "type": "microsoft",
            "voice_id": tts_voice,
        }

    body = {
        "source_url": character_image_url,
        "script": {
            "type": "text",
            "input": intro_text,
            "provider": voice_provider,
            "ssml": False,
        },
        "config": {
            "fluent": True,
            "pad_audio": 0.0,
            "stitch": True,
        },
    }

    # Create talk
    r = requests.post(f"{_BASE}/talks", headers=headers, json=body, timeout=30)
    if not r.ok:
        print(f"  D-ID create failed ({r.status_code}): {r.text[:300]}")
        return False

    talk_id = r.json()["id"]
    print(f"  D-ID talk created: {talk_id}")

    # Poll for completion
    deadline = time.time() + max_wait
    while time.time() < deadline:
        time.sleep(5)
        status_r = requests.get(f"{_BASE}/talks/{talk_id}", headers=headers, timeout=20)
        if not status_r.ok:
            continue
        data = status_r.json()
        status = data.get("status", "")
        if status == "done":
            result_url = data.get("result_url", "")
            if not result_url:
                print("  D-ID done but no result_url.")
                return False
            # Download video
            vid_r = requests.get(result_url, timeout=120, stream=True)
            if vid_r.ok:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    for chunk in vid_r.iter_content(8192):
                        f.write(chunk)
                print(f"  D-ID character intro downloaded: {output_path}")
                return True
            print(f"  D-ID download failed: {vid_r.status_code}")
            return False
        elif status == "error":
            print(f"  D-ID processing error: {data.get('error', '')}")
            return False
        else:
            print(f"  D-ID status: {status}...")

    print(f"  D-ID timeout after {max_wait}s")
    return False


def prepend_intro(intro_path: str, main_path: str, output_path: str) -> bool:
    """
    Concatenate D-ID character intro + main video using ffmpeg.
    Output overwrites output_path.
    """
    list_file = intro_path.replace(".mp4", "_concat.txt")
    with open(list_file, "w") as f:
        f.write(f"file '{Path(intro_path).resolve()}'\n")
        f.write(f"file '{Path(main_path).resolve()}'\n")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        Path(list_file).unlink(missing_ok=True)
        if result.returncode == 0:
            print("  Character intro prepended to main video.")
            return True
        print(f"  ffmpeg concat warning: {result.stderr[:200]}")
        # If direct copy fails (codec mismatch), re-encode
        cmd_reencode = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", list_file + ".retry",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ]
    except Exception as e:
        print(f"  Concat error: {e}")
    return False
