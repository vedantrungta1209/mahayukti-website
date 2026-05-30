"""
Audio generator — TTS voice + background music from Pixabay (free, no key needed).
Music mixed at low volume under voice for professional feel.
"""
import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

import requests
import edge_tts

SHORT_VOICE = "en-IN-NeerjaNeural"   # female, Indian English — energetic for Shorts
LONG_VOICE  = "en-IN-PrabhatNeural"  # male, Indian English — authoritative for long-form

# Royalty-free background music tracks from Pixabay (verified free, no API key needed)
_MUSIC_TRACKS = [
    "https://cdn.pixabay.com/audio/2024/11/06/audio_9fcb6c6ec7.mp3",  # lo-fi tech
    "https://cdn.pixabay.com/audio/2024/10/14/audio_c7ad9b3be6.mp3",  # ambient future
    "https://cdn.pixabay.com/audio/2024/09/23/audio_0b3a6b0f24.mp3",  # upbeat tech
    "https://cdn.pixabay.com/audio/2024/08/12/audio_f64d84bed9.mp3",  # chill beats
    "https://cdn.pixabay.com/audio/2024/07/29/audio_9dc9e76bfd.mp3",  # electronic
]


async def _stream(text: str, audio_path: str, voice: str) -> list[dict]:
    communicate = edge_tts.Communicate(text, voice)
    words: list[dict] = []
    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text":  chunk["text"],
                    "start": chunk["offset"] / 1e7,
                    "end":   (chunk["offset"] + chunk["duration"]) / 1e7,
                })
    return words


def _audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def _fetch_music(seed: int, output_path: str) -> bool:
    track_url = _MUSIC_TRACKS[seed % len(_MUSIC_TRACKS)]
    try:
        r = requests.get(track_url, timeout=20)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"  Music fetch failed: {e}")
    return False


def _mix_audio(voice_path: str, music_path: str, output_path: str, music_volume: float = 0.08) -> bool:
    """Mix voice (100%) with background music (8% volume) using ffmpeg."""
    try:
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", voice_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume},aloop=loop=-1:size=2e+09[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[out]",
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("  Background music mixed.")
            return True
        else:
            print(f"  Music mix warning: {result.stderr[:200]}")
    except Exception as e:
        print(f"  Music mix error: {e}")
    return False


def _write_srt(words: list[dict], srt_path: str) -> None:
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 5 or (w["end"] - cur[0]["start"]) >= 3.5:
            chunks.append((cur[0]["start"], cur[-1]["end"], " ".join(x["text"] for x in cur)))
            cur = []
    if cur:
        chunks.append((cur[0]["start"], cur[-1]["end"], " ".join(x["text"] for x in cur)))
    _save_srt(chunks, srt_path)


def _write_srt_fallback(text: str, audio_path: str, srt_path: str) -> None:
    total = _audio_duration(audio_path)
    words = text.split()
    n = len(words)
    if not n or not total:
        return
    wps = n / total
    chunks = []
    for i in range(0, n, 5):
        chunk = words[i:i + 5]
        chunks.append((i / wps, (i + len(chunk)) / wps, " ".join(chunk)))
    _save_srt(chunks, srt_path)


def _save_srt(chunks: list[tuple], srt_path: str) -> None:
    def ts(s: float) -> str:
        h, r = divmod(s, 3600)
        m, sec = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int((sec % 1) * 1000):03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate(chunks, 1):
            f.write(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n\n")


def generate_audio(text: str, output_path: str, srt_path: str | None = None,
                   voice: str = SHORT_VOICE, music_seed: int = 0) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Generate TTS
    raw_audio = output_path.replace(".mp3", "_voice_raw.mp3")
    words = asyncio.run(_stream(text, raw_audio, voice))
    print(f"  Voice audio: {raw_audio}")

    # Try to mix background music
    music_path = output_path.replace(".mp3", "_music.mp3")
    mixed = False
    if _fetch_music(music_seed, music_path):
        mixed = _mix_audio(raw_audio, music_path, output_path)

    if not mixed:
        # Fall back to voice only
        import shutil
        shutil.copy2(raw_audio, output_path)

    # Cleanup temp files
    for p in [raw_audio, music_path]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    if srt_path:
        if words:
            _write_srt(words, srt_path)
        else:
            _write_srt_fallback(text, output_path, srt_path)
        print(f"  SRT: {srt_path}")

    return output_path
