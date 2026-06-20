"""
Text-to-speech — ElevenLabs primary (human-quality), edge-tts fallback.
ElevenLabs is used automatically when ELEVENLABS_API_KEY is set and the
voice parameter is an ElevenLabs voice ID (not an "en-XX-*" edge-tts name).
"""
import asyncio
import os
import subprocess
from pathlib import Path


def _duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def _is_elevenlabs_voice(voice: str) -> bool:
    """ElevenLabs voice IDs are hex strings (20 chars) — not 'en-IN-*' names."""
    return not voice.startswith("en-") and len(voice) > 10


def _synthesise_elevenlabs(text: str, voice_id: str, output_path: Path) -> None:
    import requests
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json",
                 "Accept": "audio/mpeg"},
        json={
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.80, "style": 0.15},
        },
        timeout=60,
    )
    r.raise_for_status()
    output_path.write_bytes(r.content)


async def _synthesise_edge_async(text: str, voice: str, output_path: Path) -> None:
    import edge_tts
    await edge_tts.Communicate(text, voice).save(str(output_path))


def synthesise(text: str, voice: str, output_path: Path) -> float:
    """
    Synthesise text to MP3 at output_path. Returns duration in seconds.
    Uses ElevenLabs when ELEVENLABS_API_KEY is set + voice is an EL voice ID;
    falls back to edge-tts otherwise.
    """
    output_path = Path(output_path)
    el_key = os.environ.get("ELEVENLABS_API_KEY", "")

    if el_key and _is_elevenlabs_voice(voice):
        try:
            _synthesise_elevenlabs(text, voice, output_path)
            return _duration(output_path)
        except Exception as e:
            print(f"  ElevenLabs error ({e}) — falling back to edge-tts")

    asyncio.run(_synthesise_edge_async(text, voice, output_path))
    return _duration(output_path)


def synthesise_scenes(scenes: list[dict], voice: str, out_dir: Path) -> list[dict]:
    """
    Synthesise all scenes. Adds 'audio_path' and 'actual_duration' to each scene dict.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for i, scene in enumerate(scenes):
        path = out_dir / f"scene_{i:02d}.mp3"
        duration = synthesise(scene["narration"], voice, path)
        result.append({**scene, "audio_path": str(path), "actual_duration": duration})
        print(f"  TTS scene {i}: {duration:.1f}s — {scene['narration'][:50]}")
    return result


def synthesise_section(text: str, voice: str, out_dir: Path, idx: int) -> dict:
    """Synthesise a full long-form section narration. Returns path + duration."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"section_{idx:02d}.mp3"
    duration = synthesise(text, voice, path)
    print(f"  TTS section {idx}: {duration:.1f}s")
    return {"audio_path": str(path), "duration": duration}
