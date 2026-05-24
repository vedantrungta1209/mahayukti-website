import asyncio
import json
import subprocess
from pathlib import Path
import edge_tts

SHORT_VOICE = "en-IN-NeerjaNeural"   # female, Indian English — energetic for Shorts
LONG_VOICE  = "en-IN-PrabhatNeural"  # male, Indian English — authoritative for long-form


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
    return float(json.loads(result.stdout)["format"]["duration"])


def _write_srt(words: list[dict], srt_path: str) -> None:
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 6 or (w["end"] - cur[0]["start"]) >= 4.0:
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
    for i in range(0, n, 6):
        chunk = words[i:i + 6]
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


def generate_audio(text: str, output_path: str, srt_path: str | None = None, voice: str = SHORT_VOICE) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    words = asyncio.run(_stream(text, output_path, voice))
    print(f"  Audio: {output_path}")

    if srt_path:
        if words:
            _write_srt(words, srt_path)
        else:
            _write_srt_fallback(text, output_path, srt_path)
        print(f"  SRT: {srt_path}")

    return output_path
