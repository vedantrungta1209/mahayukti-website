"""
Audio generator — ElevenLabs TTS primary (edge-tts fallback) + ambient background music.
Music mixed at 8% volume under voice for professional feel. No external URLs needed.
"""
import asyncio
import json
import os
import subprocess
from pathlib import Path

# ElevenLabs voice IDs — human-quality, much better than edge-tts
SHORT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam — energetic, clear male (great for AI tech)
LONG_VOICE_ID  = "pNInz6obpgDQGcFmaJgB"  # Adam — same for consistency

# edge-tts fallbacks (used only when ELEVENLABS_API_KEY is not set)
SHORT_VOICE_EDGE = "en-IN-NeerjaNeural"
LONG_VOICE_EDGE  = "en-IN-PrabhatNeural"

# Ambient chord presets — layered sine waves synthesised via ffmpeg
_AMBIENT_PRESETS = [
    (110.0, 146.8, 220.0, 70),   # A minor — calm tech
    (130.8, 196.0, 261.6, 80),   # C major — upbeat positive
    (146.8, 220.0, 293.7, 75),   # D minor — mysterious
    (98.0,  130.8, 196.0, 65),   # G major — warm
    (123.5, 185.0, 246.9, 72),   # B minor — cinematic
]


def _synth_elevenlabs(text: str, audio_path: str, voice_id: str) -> bool:
    """Generate audio via ElevenLabs API. Returns True on success."""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        return False
    try:
        import requests
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
        Path(audio_path).write_bytes(r.content)
        print(f"  ElevenLabs: {audio_path}")
        return True
    except Exception as e:
        print(f"  ElevenLabs error: {e}")
        return False


async def _stream_edge(text: str, audio_path: str, voice: str) -> list[dict]:
    """edge-tts fallback — streams audio + captures word boundaries for SRT."""
    import edge_tts
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


def _generate_ambient(seed: int, output_path: str, duration: float = 120.0) -> bool:
    preset = _AMBIENT_PRESETS[seed % len(_AMBIENT_PRESETS)]
    bass, mid, high, bpm = preset
    pulse = bpm / 60.0
    expr = (
        f"0.18*sin({bass}*2*PI*t)*sin({pulse}*2*PI*t+0.1)+"
        f"0.14*sin({mid}*2*PI*t)*sin({pulse*1.3}*2*PI*t+0.4)+"
        f"0.09*sin({high}*2*PI*t)*sin({pulse*0.7}*2*PI*t+0.8)+"
        f"0.04*sin({bass*2}*2*PI*t)*sin({pulse*2}*2*PI*t)"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100",
        "-t", str(duration), "-c:a", "aac", "-b:a", "128k", output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  Ambient music synthesised (preset {seed % len(_AMBIENT_PRESETS)}).")
            return True
        print(f"  Music synth warning: {result.stderr[:100]}")
    except Exception as e:
        print(f"  Music synth error: {e}")
    return False


def _mix_audio(voice_path: str, music_path: str, output_path: str, music_volume: float = 0.08) -> bool:
    try:
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", voice_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume},aloop=loop=-1:size=2e+09[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[out]",
            "-map", "[out]", "-c:a", "aac", "-b:a", "192k", output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("  Background music mixed.")
            return True
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
                   voice: str = SHORT_VOICE_ID, music_seed: int = 0) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    raw_audio = output_path.replace(".mp3", "_voice_raw.mp3")

    # Try ElevenLabs first (human-quality)
    words = []
    el_ok = _synth_elevenlabs(text, raw_audio, SHORT_VOICE_ID)

    if not el_ok:
        # Fall back to edge-tts
        edge_voice = SHORT_VOICE_EDGE if "Neural" in voice or "en-" in voice else LONG_VOICE_EDGE
        words = asyncio.run(_stream_edge(text, raw_audio, edge_voice))
        print(f"  edge-tts fallback: {raw_audio}")

    # Mix background music
    music_path = output_path.replace(".mp3", "_music.aac")
    mixed = False
    voice_duration = _audio_duration(raw_audio)
    if _generate_ambient(music_seed, music_path, duration=voice_duration + 5.0):
        mixed = _mix_audio(raw_audio, music_path, output_path)

    if not mixed:
        import shutil
        shutil.copy2(raw_audio, output_path)

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
