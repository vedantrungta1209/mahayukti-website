#!/usr/bin/env python3
"""
Unified runner for all 7 Mahayukti topic channels.
  python runner.py --channel hustle --mode short
  python runner.py --channel crime  --mode long        # also generates trailer short
  python runner.py --channel business --mode long
"""
import argparse
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

GH_REPO = "vedantrungta1209/mahayukti-website"


def _counter_path(channel: str, mode: str) -> Path:
    return Path(__file__).parent / f"counters/{channel}_{mode}.txt"


def _read_counter(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except Exception:
        return 0


def _write_counter(path: Path, value: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(value))


def _push_token_secret(cfg) -> None:
    token_file = Path(__file__).parent / cfg.TOKEN_FILE
    if not token_file.exists():
        return
    token = token_file.read_text()
    subprocess.run(
        ["gh", "secret", "set", cfg.SECRET_NAME, "--body", token, "--repo", GH_REPO],
        capture_output=True,
    )
    print(f"  Token refreshed → {cfg.SECRET_NAME}")


def _cleanup(cfg) -> None:
    out = Path(__file__).parent / cfg.OUTPUT_DIR
    if out.exists():
        shutil.rmtree(out)


def _import_shared():
    sys.path.insert(0, str(Path(__file__).parent))
    from script_generator import generate_short_script, generate_long_script
    from audio_generator import generate_audio
    from video_composer import compose_short, compose_long, generate_thumbnail
    from youtube_uploader import upload_video, post_comment
    return (generate_short_script, generate_long_script, generate_audio,
            compose_short, compose_long, generate_thumbnail, upload_video,
            post_comment)


def _el_params(cfg) -> dict:
    return {
        "elevenlabs_voice_id": getattr(cfg, "ELEVENLABS_VOICE_ID", ""),
        "elevenlabs_key": os.environ.get("ELEVENLABS_API_KEY", ""),
    }


def run_short(cfg) -> None:
    print("=" * 60)
    print(f"  {cfg.CHANNEL_NAME} — SHORT")
    print("=" * 60)
    (generate_short_script, generate_long_script, generate_audio,
     compose_short, compose_long, generate_thumbnail, upload_video,
     post_comment) = _import_shared()

    counter_path = _counter_path(cfg.CHANNEL_ID, "short")
    idx   = _read_counter(counter_path)
    topic = cfg.SHORT_TOPICS[idx % len(cfg.SHORT_TOPICS)]
    print(f"  Topic #{idx}: {topic['name']}")

    print("  Generating script...")
    script = generate_short_script(topic, cfg)
    script["category"] = topic.get("category", "General")

    base = str(Path(__file__).parent / cfg.OUTPUT_DIR)
    audio_path = f"{base}/short_audio.mp3"
    srt_path   = f"{base}/short_subtitles.srt"
    video_path = f"{base}/short_video.mp4"

    print("  Generating audio + music...")
    generate_audio(
        script["script"], audio_path, srt_path,
        voice=cfg.SHORT_VOICE, music_seed=idx,
        **_el_params(cfg),
    )

    print("  Composing video...")
    compose_short(audio_path, script, video_path, srt_path, cfg)

    print("  Uploading to YouTube...")
    yt_id = upload_video(
        video_path=video_path,
        title=script.get("title", topic["name"]),
        description=script.get("description", ""),
        tags=script.get("tags", []),
        is_short=True,
        cfg=cfg,
    )

    # Post pinned comment for affiliate links / CTA
    pinned = script.get("pinned_comment", "")
    if pinned and yt_id:
        post_comment(yt_id, pinned, cfg)

    _push_token_secret(cfg)
    _write_counter(counter_path, idx + 1)
    _cleanup(cfg)
    print(f"  Done ✓  https://youtube.com/watch?v={yt_id}")


def run_long(cfg, also_short: bool = False) -> None:
    print("=" * 60)
    print(f"  {cfg.CHANNEL_NAME} — LONG{' + TRAILER' if also_short else ''}")
    print("=" * 60)
    (generate_short_script, generate_long_script, generate_audio,
     compose_short, compose_long, generate_thumbnail, upload_video,
     post_comment) = _import_shared()

    counter_path = _counter_path(cfg.CHANNEL_ID, "long")
    idx    = _read_counter(counter_path)
    topic  = cfg.LONG_TOPICS[idx % len(cfg.LONG_TOPICS)]
    print(f"  Topic #{idx}: {topic['name']}")

    print("  Generating script...")
    script = generate_long_script(topic, cfg)
    script["_category"] = topic.get("category", "General")

    base = str(Path(__file__).parent / cfg.OUTPUT_DIR)
    audio_path     = f"{base}/long_audio.mp3"
    srt_path       = f"{base}/long_subtitles.srt"
    video_path     = f"{base}/long_video.mp4"
    thumbnail_path = f"{base}/thumbnail.jpg"

    print("  Generating audio + music...")
    generate_audio(
        script["full_script"], audio_path, srt_path,
        voice=cfg.LONG_VOICE, music_seed=idx + 100,
        **_el_params(cfg),
    )

    print("  Composing video...")
    compose_long(audio_path, script, video_path, srt_path, cfg)

    print("  Generating thumbnail...")
    generate_thumbnail(script, thumbnail_path, cfg)

    print("  Uploading to YouTube...")
    yt_id = upload_video(
        video_path=video_path,
        title=script.get("title", topic["name"]),
        description=script.get("description", ""),
        tags=script.get("tags", []),
        is_short=False,
        thumbnail_path=thumbnail_path,
        cfg=cfg,
    )

    pinned = script.get("pinned_comment", "")
    if pinned and yt_id:
        post_comment(yt_id, pinned, cfg)

    _push_token_secret(cfg)
    _write_counter(counter_path, idx + 1)

    # Auto-generate trailer short (crime channel)
    if also_short and hasattr(cfg, "generate_trailer_script"):
        print("\n  Generating trailer short...")
        trailer = cfg.generate_trailer_script(script)
        trailer["category"] = script.get("_category", "General")
        t_audio = f"{base}/trailer_audio.mp3"
        t_srt   = f"{base}/trailer_subtitles.srt"
        t_video = f"{base}/trailer_video.mp4"
        generate_audio(
            trailer["script"], t_audio, t_srt,
            voice=cfg.SHORT_VOICE, music_seed=idx + 200,
            **_el_params(cfg),
        )
        compose_short(t_audio, trailer, t_video, t_srt, cfg)
        upload_video(
            video_path=t_video,
            title=trailer.get("title", f"Trailer: {topic['name']}"),
            description=trailer.get("description", ""),
            tags=trailer.get("tags", []),
            is_short=True,
            cfg=cfg,
        )
        print("  Trailer done ✓")

    _cleanup(cfg)
    print(f"  Done ✓  https://youtube.com/watch?v={yt_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True,
                        choices=["hustle", "business", "crime", "mind", "kanoon", "speak", "swasth"])
    parser.add_argument("--mode", choices=["short", "long"], required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    cfg = importlib.import_module(f"configs.{args.channel}")

    if args.mode == "short":
        run_short(cfg)
    else:
        run_long(cfg, also_short=getattr(cfg, "LONG_ALSO_GENERATES_SHORT", False))
