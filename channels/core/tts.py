"""
Text-to-speech via edge-tts (Microsoft Edge TTS — free, no API key, no downloads).
Generates per-scene audio MP3 files. Duration measured via ffprobe.
"""
import asyncio
import subprocess
from pathlib import Path


def _duration(path: Path) -> float:
    """Return audio duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


async def _synthesise_async(text: str, voice: str, output_path: Path) -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def synthesise(text: str, voice: str, output_path: Path) -> float:
    """
    Synthesise text to MP3 at output_path.
    Returns actual audio duration in seconds.
    """
    output_path = Path(output_path)
    asyncio.run(_synthesise_async(text, voice, output_path))
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
