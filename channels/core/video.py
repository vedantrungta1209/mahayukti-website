"""
Video clip generation via fal.ai Wan 2.6.
Each visual prompt → a short cinematic video clip.
"""
import os
import time
from pathlib import Path

import fal_client
import requests

# Wan model on fal.ai — swap to t2v-14b for higher quality (costs more)
WAN_MODEL_SHORT = "fal-ai/wan/v2.1/t2v-1.3b"   # 9:16, fast + cheap
WAN_MODEL_LONG  = "fal-ai/wan/v2.1/t2v-1.3b"   # 16:9, same model, different aspect


def _download(url: str, path: Path) -> None:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    path.write_bytes(r.content)


def generate_clip(
    prompt: str,
    output_path: Path,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 5,
    retries: int = 3,
) -> None:
    """
    Generate a video clip from a text prompt.
    aspect_ratio: "16:9" for long-form, "9:16" for Shorts
    duration_seconds: 4 or 5 (Wan 1.3B supports up to 5s per clip)
    """
    negative = (
        "text, subtitles, watermark, logo, blurry, low quality, distorted, "
        "ugly, bad anatomy, worst quality, nsfw, violence"
    )

    model = WAN_MODEL_SHORT if aspect_ratio == "9:16" else WAN_MODEL_LONG

    for attempt in range(1, retries + 1):
        try:
            print(f"  Wan clip [{aspect_ratio}]: {prompt[:60]}…")
            handler = fal_client.submit(
                model,
                arguments={
                    "prompt": prompt,
                    "negative_prompt": negative,
                    "num_frames": duration_seconds * 16,   # 16 fps
                    "aspect_ratio": aspect_ratio,
                    "num_inference_steps": 30,
                },
            )
            result = handler.get()
            video_url = result["video"]["url"]
            _download(video_url, output_path)
            print(f"    ✓ saved {output_path.name}")
            return
        except Exception as e:
            print(f"    attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)
    raise RuntimeError(f"Video generation failed after {retries} attempts for: {prompt}")


def generate_clips_for_scenes(
    scenes: list[dict],
    out_dir: Path,
    aspect_ratio: str = "9:16",
) -> list[dict]:
    """
    Generate one video clip per scene.
    Adds 'clip_path' to each scene dict.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for i, scene in enumerate(scenes):
        path = out_dir / f"clip_{i:02d}.mp4"
        if path.exists():
            print(f"  clip {i} cached, skipping")
        else:
            dur = min(5, max(4, int(scene.get("actual_duration", scene.get("duration_hint", 5)))))
            generate_clip(scene["visual_prompt"], path, aspect_ratio, dur)
        result.append({**scene, "clip_path": str(path)})
    return result


def generate_clips_for_section(
    visual_prompts: list[str],
    out_dir: Path,
    section_idx: int,
    aspect_ratio: str = "16:9",
) -> list[str]:
    """
    Generate clips for each visual prompt in a long-form section.
    Returns list of clip paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for j, vp in enumerate(visual_prompts):
        path = out_dir / f"section_{section_idx:02d}_clip_{j:02d}.mp4"
        if not path.exists():
            generate_clip(vp, path, aspect_ratio, duration_seconds=5)
        paths.append(str(path))
    return paths
