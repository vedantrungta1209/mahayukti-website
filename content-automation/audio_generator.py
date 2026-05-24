import asyncio
import json
import subprocess
from pathlib import Path
import edge_tts


async def _stream(text: str, audio_path: str, voice: str) -> list[dict]:
    """Stream TTS, write audio, return word boundary events (may be empty)."""
    communicate = edge_tts.Communicate(text, voice)
    words: list[dict] = []

    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 1e7,
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                })
    return words


def _audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path],
        capture_output=True, text=True,
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def _write_srt(words: list[dict], srt_path: str) -> None:
    """Group word-boundary events into subtitle lines."""
    chunks: list[tuple[float, float, str]] = []
    cur: list[dict] = []

    for w in words:
        cur.append(w)
        if len(cur) >= 6 or (w["end"] - cur[0]["start"]) >= 4.0:
            chunks.append((cur[0]["start"], cur[-1]["end"], " ".join(x["text"] for x in cur)))
            cur = []
    if cur:
        chunks.append((cur[0]["start"], cur[-1]["end"], " ".join(x["text"] for x in cur)))

    _save_srt(chunks, srt_path)
    print(f"  Subtitles: {len(chunks)} lines (word-synced)")


def _write_srt_fallback(text: str, audio_path: str, srt_path: str) -> None:
    """Fallback: distribute script words evenly over audio duration."""
    total = _audio_duration(audio_path)
    words = text.split()
    n = len(words)
    if n == 0 or total == 0:
        return

    words_per_sec = n / total
    chunks: list[tuple[float, float, str]] = []
    chunk_size = 6

    for i in range(0, n, chunk_size):
        chunk_words = words[i:i + chunk_size]
        start = i / words_per_sec
        end = (i + len(chunk_words)) / words_per_sec
        chunks.append((start, end, " ".join(chunk_words)))

    _save_srt(chunks, srt_path)
    print(f"  Subtitles: {len(chunks)} lines (time-distributed fallback)")


def _save_srt(chunks: list[tuple[float, float, str]], srt_path: str) -> None:
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
    voice: str = "hi-IN-MadhurNeural",
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    words = asyncio.run(_stream(text, output_path, voice))
    print(f"  Audio saved: {output_path}")

    if srt_path:
        if words:
            _write_srt(words, srt_path)
        else:
            # Hindi neural voices don't emit WordBoundary — distribute evenly
            _write_srt_fallback(text, output_path, srt_path)

    return output_path


# Available Indian voices:
# en-IN-NeerjaNeural   — female, Hinglish (sends WordBoundary events)
# en-IN-PrabhatNeural  — male, Hinglish
# hi-IN-SwaraNeural    — Hindi female
# hi-IN-MadhurNeural   — Hindi male (professional, no WordBoundary events)
