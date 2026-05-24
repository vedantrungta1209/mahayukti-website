import asyncio
from pathlib import Path
import edge_tts


async def _stream(text: str, audio_path: str, srt_path: str | None, voice: str) -> None:
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

    if srt_path and words:
        _write_srt(words, srt_path)


def _write_srt(words: list[dict], srt_path: str) -> None:
    """Group words into subtitle lines and write SRT file."""
    chunks: list[tuple[float, float, str]] = []
    cur: list[dict] = []

    for w in words:
        cur.append(w)
        if len(cur) >= 6 or (w["end"] - cur[0]["start"]) >= 4.0:
            chunks.append((cur[0]["start"], cur[-1]["end"], " ".join(x["text"] for x in cur)))
            cur = []
    if cur:
        chunks.append((cur[0]["start"], cur[-1]["end"], " ".join(x["text"] for x in cur)))

    def ts(s: float) -> str:
        h, r = divmod(s, 3600)
        m, sec = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int((sec % 1) * 1000):03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate(chunks, 1):
            f.write(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n\n")

    print(f"  Subtitles: {len(chunks)} lines generated")


def generate_audio(
    text: str,
    output_path: str,
    srt_path: str | None = None,
    voice: str = "hi-IN-MadhurNeural",
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_stream(text, output_path, srt_path, voice))
    print(f"  Audio saved: {output_path}")
    return output_path


# Available Indian voices:
# en-IN-NeerjaNeural   — female, natural, best for Hinglish
# en-IN-PrabhatNeural  — male
# hi-IN-SwaraNeural    — Hindi female
# hi-IN-MadhurNeural   — Hindi male (professional, authoritative)
