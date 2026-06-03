"""
Text-to-speech via Kokoro ONNX (free, no API key).
Generates per-scene audio WAV files.
"""
import os
from pathlib import Path

import soundfile as sf

_kokoro = None

_HF_REPO = "thewh1teagle/kokoro-onnx"


def _get_kokoro():
    """Lazy-load Kokoro model via huggingface_hub (handles redirects + caching)."""
    global _kokoro
    if _kokoro is None:
        from huggingface_hub import hf_hub_download
        from kokoro_onnx import Kokoro
        print("  downloading Kokoro model files…")
        model_path  = hf_hub_download(repo_id=_HF_REPO, filename="kokoro-v1.0.onnx")
        voices_path = hf_hub_download(repo_id=_HF_REPO, filename="voices-v1.0.bin")
        print("  ✓ Kokoro ready")
        _kokoro = Kokoro(model_path, voices_path)
    return _kokoro


def synthesise(text: str, voice: str, output_path: str | Path) -> float:
    """
    Synthesise text to WAV at output_path.
    Returns actual audio duration in seconds.
    """
    kokoro = _get_kokoro()
    samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
    sf.write(str(output_path), samples, sample_rate)
    return len(samples) / sample_rate


def synthesise_scenes(scenes: list[dict], voice: str, out_dir: Path) -> list[dict]:
    """
    Synthesise all scenes. Adds 'audio_path' and 'actual_duration' to each scene dict.
    scenes: [{"narration": str, "visual_prompt": str, "duration_hint": float}]
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for i, scene in enumerate(scenes):
        path = out_dir / f"scene_{i:02d}.wav"
        duration = synthesise(scene["narration"], voice, path)
        result.append({**scene, "audio_path": str(path), "actual_duration": duration})
        print(f"  TTS scene {i}: {duration:.1f}s — {scene['narration'][:50]}")
    return result


def synthesise_section(text: str, voice: str, out_dir: Path, idx: int) -> dict:
    """Synthesise a full long-form section narration. Returns path + duration."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"section_{idx:02d}.wav"
    duration = synthesise(text, voice, path)
    print(f"  TTS section {idx}: {duration:.1f}s")
    return {"audio_path": str(path), "duration": duration}
