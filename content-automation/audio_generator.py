import asyncio
import edge_tts
from pathlib import Path


async def _generate_async(text: str, path: str, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)


def generate_audio(
    text: str,
    output_path: str,
    voice: str = "en-IN-NeerjaNeural",  # Indian English female — handles Hinglish naturally
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_generate_async(text, output_path, voice))
    print(f"  Audio saved: {output_path}")
    return output_path


# Available Indian voices:
# en-IN-NeerjaNeural   — female, natural, best for Hinglish
# en-IN-PrabhatNeural  — male
# hi-IN-SwaraNeural    — Hindi female (pure Hindi scripts)
# hi-IN-MadhurNeural   — Hindi male (pure Hindi scripts)
