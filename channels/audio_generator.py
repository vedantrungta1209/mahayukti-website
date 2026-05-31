"""
Audio generator — ElevenLabs (primary, character-grade quality) + edge-tts fallback.
Music mixed at 8% volume under voice. No external URLs needed for music.
"""
import asyncio
import json
import os
import subprocess
from pathlib import Path

import edge_tts
import requests

SHORT_VOICE = "en-IN-NeerjaNeural"   # edge-tts fallback
LONG_VOICE  = "en-IN-PrabhatNeural"  # edge-tts fallback

_AMBIENT_PRESETS = [
    (110.0, 146.8, 220.0, 70),   # A minor — calm tech
    (130.8, 196.0, 261.6, 80),   # C major — upbeat positive
    (146.8, 220.0, 293.7, 75),   # D minor — mysterious
    (98.0,  130.8, 196.0, 65),   # G major — warm
    (123.5, 185.0, 246.9, 72),   # B minor — cinematic
]


async def _stream_edge_tts(text: str, audio_path: str, voice: str) -> list[dict]:
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


def _generate_elevenlabs(text: str, audio_path: str, voice_id: str, api_key: str) -> bool:
    """Generate audio via ElevenLabs API. Returns True on success."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability":         0.45,
            "similarity_boost":  0.80,
            "style":             0.35,
            "use_speaker_boost": True,
        },
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=120, stream=True)
        if r.status_code == 200:
            with open(audio_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  ElevenLabs voice generated ({voice_id}).")
            return True
        print(f"  ElevenLabs error {r.status_code}: {r.text[:200]} — falling back to edge-tts")
    except Exception as e:
        print(f"  ElevenLabs error: {e} — falling back to edge-tts")
    return False


def _audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def _generate_ambient(seed: int, output_path: str, duration: float = 120.0) -> bool:
    """
    Cinematic ambient pad — multi-layer synthesis with warmth, soft attack,
    reverb-style delay, and a low-pass filter to avoid harshness.
    """
    preset = _AMBIENT_PRESETS[seed % len(_AMBIENT_PRESETS)]
    bass, mid, high, bpm = preset
    beat = bpm / 60.0

    # Soft pad: harmonics with gentle amplitude modulation (tremolo) + envelope
    # attack = 2s (sin²), release tail via amplitude shaping
    attack = 2.0
    expr = (
        # Bass pad layer — slow swell
        f"0.15*sin({bass}*2*PI*t)*sin({beat*0.5}*2*PI*t+0.1)*min(1,t/{attack})+"
        # Mid pad layer — slightly detuned for warmth
        f"0.11*sin({mid*1.002}*2*PI*t)*sin({beat*0.7}*2*PI*t+0.3)*min(1,t/{attack})+"
        # High shimmer — quiet, airy
        f"0.06*sin({high}*2*PI*t)*sin({beat*1.3}*2*PI*t+0.6)*min(1,t/{attack})+"
        # Sub-bass breathe
        f"0.05*sin({bass*0.5}*2*PI*t)*min(1,t/{attack})+"
        # Octave warmth
        f"0.04*sin({mid*2}*2*PI*t)*sin({beat*0.3}*2*PI*t)*min(1,t/{attack})"
    )

    raw_path = output_path.replace(".aac", "_raw.aac")
    cmd_synth = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100",
        "-t", str(duration + 2),
        "-c:a", "aac", "-b:a", "192k", raw_path,
    ]
    try:
        r1 = subprocess.run(cmd_synth, capture_output=True, text=True)
        if r1.returncode != 0:
            print(f"  Music synth warning: {r1.stderr[:100]}")
            return False

        # Post-process: low-pass filter (removes harshness) + gentle reverb via
        # adelay + amix + trim to exact duration
        cmd_post = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", raw_path,
            "-af", (
                "lowpass=f=4000,"           # cut harsh highs
                "equalizer=f=200:t=o:w=2:g=3,"   # boost low-mids (warmth)
                "aecho=0.8:0.6:60:0.4,"    # subtle room reverb
                "volume=0.85,"              # pull back slightly after reverb
                f"atrim=0:{duration},"
                "aformat=sample_rates=44100:channel_layouts=stereo"
            ),
            "-c:a", "aac", "-b:a", "192k", output_path,
        ]
        r2 = subprocess.run(cmd_post, capture_output=True, text=True)
        Path(raw_path).unlink(missing_ok=True)
        if r2.returncode == 0:
            print(f"  Ambient music synthesised (preset {seed % len(_AMBIENT_PRESETS)}).")
            return True
        print(f"  Music post-process warning: {r2.stderr[:150]}")
        # Use raw as fallback
        import shutil
        if Path(raw_path).exists():
            shutil.move(raw_path, output_path)
            return True
    except Exception as e:
        print(f"  Music synth error: {e}")
    return False


def _mix_audio(voice_path: str, music_path: str, output_path: str, music_volume: float = 0.06) -> bool:
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


def generate_audio(
    text: str,
    output_path: str,
    srt_path: str | None = None,
    voice: str = SHORT_VOICE,
    music_seed: int = 0,
    elevenlabs_voice_id: str = "",
    elevenlabs_key: str = "",
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    raw_audio = output_path.replace(".mp3", "_voice_raw.mp3")
    words: list[dict] = []

    # ElevenLabs first (character-grade voice), edge-tts fallback
    el_key = elevenlabs_key or os.environ.get("ELEVENLABS_API_KEY", "")
    el_vid = elevenlabs_voice_id or ""
    used_elevenlabs = False

    if el_key and el_vid:
        used_elevenlabs = _generate_elevenlabs(text, raw_audio, el_vid, el_key)

    if not used_elevenlabs:
        words = asyncio.run(_stream_edge_tts(text, raw_audio, voice))
        print(f"  edge-tts voice: {raw_audio}")

    # Ambient background music
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
