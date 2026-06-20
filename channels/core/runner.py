#!/usr/bin/env python3
"""
Main orchestrator for the Mahayukti v2 video pipeline.

  python core/runner.py --channel finance --mode short
  python core/runner.py --channel finance --mode long
  python core/runner.py --channel business --mode short
"""
import argparse
import importlib
import shutil
import sys
import tempfile
from pathlib import Path

CHANNELS_DIR = Path(__file__).parent.parent
COUNTERS_DIR = CHANNELS_DIR / "counters"
CONFIGS_DIR  = CHANNELS_DIR / "configs"


# ── Counter helpers ───────────────────────────────────────────────────────────

def _counter_path(channel: str, mode: str) -> Path:
    return COUNTERS_DIR / f"{channel}_{mode}.txt"


def _read_counter(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except Exception:
        return 0


def _write_counter(path: Path, value: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(value))


# ── Pipeline: SHORT ───────────────────────────────────────────────────────────

def run_short(config, work_dir: Path) -> None:
    from core import writer, tts, video, composer, uploader

    # Pick topic — try trending signals first
    ctr_path = _counter_path(config.CHANNEL_ID, "short")
    idx = _read_counter(ctr_path) % len(config.SHORT_TOPICS)
    try:
        from core.trending import pick_topic_with_trending
        seeds = getattr(config, "TRENDING_SEEDS", None)
        if seeds:
            topic = pick_topic_with_trending(config.SHORT_TOPICS, seeds, idx)
        else:
            topic = config.SHORT_TOPICS[idx]
    except Exception as e:
        print(f"  Trending detection failed ({e}), using static topic")
        topic = config.SHORT_TOPICS[idx]
    print(f"\n📱 SHORT: {topic['name']}")

    # 1. Script
    print("✍️  Generating script…")
    script = writer.generate_short(config, topic)
    print(f"   title: {script['youtube_title']}")
    print(f"   scenes: {len(script['scenes'])}")

    # 2. TTS — prefer ElevenLabs voice ID if available
    print("🎙️  Synthesising audio…")
    audio_dir = work_dir / "audio"
    voice = getattr(config, "ELEVENLABS_VOICE_ID", None) or config.VOICE
    scenes = tts.synthesise_scenes(script["scenes"], voice, audio_dir)

    # 3. Video clips
    print("🎬  Generating video clips (fal.ai Wan)…")
    clips_dir = work_dir / "clips"
    scenes = video.generate_clips_for_scenes(scenes, clips_dir, aspect_ratio="9:16")

    # 4. Compose
    print("🎞️  Composing final video…")
    composed_dir = work_dir / "composed"
    final = composer.compose_short(scenes, config, composed_dir)

    # 5. Upload
    print("🚀  Uploading to YouTube…")
    uploader.upload(
        video_path=final,
        title=script["youtube_title"],
        description=script["youtube_description"],
        tags=script["tags"],
        token_env_var=config.TOKEN_ENV_VAR,
        is_short=True,
    )

    # Advance counter
    _write_counter(ctr_path, idx + 1)
    print(f"\n✅  Short complete. Counter → {idx + 1}")


# ── Pipeline: LONG ────────────────────────────────────────────────────────────

def run_long(config, work_dir: Path) -> None:
    from core import writer, tts, video, composer, uploader

    # Pick topic
    ctr_path = _counter_path(config.CHANNEL_ID, "long")
    idx = _read_counter(ctr_path) % len(config.LONG_TOPICS)
    topic = config.LONG_TOPICS[idx]
    print(f"\n🎥 LONG: {topic['name']}")

    # 1. Script
    print("✍️  Generating script…")
    script = writer.generate_long(config, topic)
    print(f"   title: {script['youtube_title']}")
    print(f"   sections: {len(script['sections'])}")

    # 2. TTS + video per section
    print("🎙️  Synthesising + generating clips per section…")
    sections_data = []
    audio_dir = work_dir / "audio"
    clips_dir = work_dir / "clips"

    for i, section in enumerate(script["sections"]):
        print(f"  [{i+1}/{len(script['sections'])}] {section['heading']}")

        # TTS for this section
        audio = tts.synthesise_section(
            section["narration"], config.VOICE, audio_dir, i
        )

        # Video clips for this section
        clip_paths = video.generate_clips_for_section(
            section["visual_prompts"], clips_dir, i, aspect_ratio="16:9"
        )

        sections_data.append({
            "heading": section["heading"],
            "audio_path": audio["audio_path"],
            "audio_duration": audio["duration"],
            "clip_paths": clip_paths,
        })

    # 3. Compose
    print("🎞️  Composing final video…")
    composed_dir = work_dir / "composed"
    final = composer.compose_long(sections_data, config, composed_dir)

    # 4. Upload
    print("🚀  Uploading to YouTube…")
    uploader.upload(
        video_path=final,
        title=script["youtube_title"],
        description=script["youtube_description"],
        tags=script["tags"],
        token_env_var=config.TOKEN_ENV_VAR,
        is_short=False,
    )

    # Advance counter
    _write_counter(ctr_path, idx + 1)
    print(f"\n✅  Long-form complete. Counter → {idx + 1}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True, help="Channel ID (e.g. finance, business)")
    parser.add_argument("--mode", required=True, choices=["short", "long"])
    parser.add_argument("--keep-work-dir", action="store_true", help="Keep temp work dir for debugging")
    args = parser.parse_args()

    # Load channel config
    sys.path.insert(0, str(CHANNELS_DIR))
    try:
        config = importlib.import_module(f"configs.{args.channel}")
    except ModuleNotFoundError:
        print(f"ERROR: no config found at configs/{args.channel}.py")
        sys.exit(1)

    # Validate required attributes
    required = ["CHANNEL_ID", "CHANNEL_NAME", "NICHE", "VOICE", "TOKEN_ENV_VAR",
                "SHORT_TOPICS", "LONG_TOPICS", "PRIMARY_HEX", "VIDEO_STYLE"]
    missing = [a for a in required if not hasattr(config, a)]
    if missing:
        print(f"ERROR: config missing: {missing}")
        sys.exit(1)

    # Run in a temp directory
    with tempfile.TemporaryDirectory(prefix=f"mahayukti_{args.channel}_") as tmp:
        work_dir = Path(tmp)
        try:
            if args.mode == "short":
                run_short(config, work_dir)
            else:
                run_long(config, work_dir)
        except Exception:
            if args.keep_work_dir:
                keep = Path(f"/tmp/mahayukti_{args.channel}_{args.mode}_debug")
                shutil.copytree(tmp, str(keep), dirs_exist_ok=True)
                print(f"Work dir preserved at: {keep}")
            raise


if __name__ == "__main__":
    main()
