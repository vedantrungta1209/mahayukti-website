import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips

from frame_generator import (
    create_title_frame, create_point_frame, create_hook_frame, create_outro_frame,
)
from config import OUTPUT_DIR, CHANNEL_HANDLE, FPS

TITLE_DURATION   = 3
HOOK_DURATION    = 7
OUTRO_DURATION   = 5
MIN_POINT_DURATION = 8

ZOOM_AMOUNT = 0.12
PAN_AMOUNT  = 0.06


def _ken_burns(img_path: str, duration: float, zoom_in: bool = True) -> VideoClip:
    pil_img = PILImage.open(img_path).convert("RGB")
    orig_w, orig_h = pil_img.size

    def make_frame(t: float) -> np.ndarray:
        progress = t / duration
        scale = (1.0 + ZOOM_AMOUNT * progress) if zoom_in else (1.0 + ZOOM_AMOUNT * (1.0 - progress))
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        resized = pil_img.resize((new_w, new_h), PILImage.BILINEAR)
        mx, my = new_w - orig_w, new_h - orig_h
        x0 = int(mx * PAN_AMOUNT * (1.0 - progress)) if zoom_in else int(mx * (0.5 + PAN_AMOUNT * progress))
        y0 = int(my * PAN_AMOUNT * (1.0 - progress)) if zoom_in else int(my * (0.5 + PAN_AMOUNT * progress))
        x0, y0 = max(0, min(x0, mx)), max(0, min(y0, my))
        return np.array(resized.crop((x0, y0, x0 + orig_w, y0 + orig_h)))

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def _burn_subtitles(video_path: str, srt_path: str) -> None:
    tmp = video_path.replace(".mp4", "_raw.mp4")
    os.rename(video_path, tmp)
    srt_abs = str(Path(srt_path).resolve())
    style = (
        "FontName=DejaVu Sans,FontSize=26,PrimaryColour=&H00FFFFFF,"
        "BorderStyle=3,BackColour=&HAA000000,Outline=0,Shadow=0,"
        "Alignment=2,MarginV=55"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", tmp,
        "-vf", f"subtitles={srt_abs}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "copy", video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp)
    if result.returncode != 0:
        print(f"  Subtitle burn warning: {result.stderr[:200]}")
    else:
        print("  Subtitles burned in.")


def compose_video(
    audio_path: str,
    script_data: dict,
    output_path: str,
    srt_path: str | None = None,
) -> str:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    category = script_data.get("_category", "")
    angle    = script_data.get("_angle", script_data.get("title", ""))

    audio = AudioFileClip(audio_path)
    total = audio.duration
    key_points: list[str] = script_data["key_points"]

    fixed_time = TITLE_DURATION + HOOK_DURATION + OUTRO_DURATION
    point_time = max((total - fixed_time) / max(len(key_points), 1), MIN_POINT_DURATION)

    slides: list[tuple[str, float]] = []

    title_path = f"{OUTPUT_DIR}/slide_title.png"
    create_title_frame(script_data["title"], category, angle, title_path)
    slides.append((title_path, TITLE_DURATION))

    hook_path = f"{OUTPUT_DIR}/slide_hook.png"
    create_hook_frame(script_data["hook"], category, angle, hook_path)
    slides.append((hook_path, HOOK_DURATION))

    for i, point in enumerate(key_points):
        frame_path = f"{OUTPUT_DIR}/slide_point_{i}.png"
        create_point_frame(i + 1, point, category, angle, frame_path)
        slides.append((frame_path, point_time))

    outro_path = f"{OUTPUT_DIR}/slide_outro.png"
    create_outro_frame(category, angle, outro_path)
    slides.append((outro_path, OUTRO_DURATION))

    clips = [_ken_burns(p, d, zoom_in=(i % 2 == 0)) for i, (p, d) in enumerate(slides)]
    video = concatenate_videoclips(clips)
    if video.duration > total:
        video = video.subclipped(0, total)

    final = video.with_audio(audio)
    final.write_videofile(
        output_path, fps=FPS, codec="libx264", audio_codec="aac",
        preset="ultrafast", threads=4, logger=None,
    )
    audio.close()
    final.close()

    if srt_path and Path(srt_path).exists():
        _burn_subtitles(output_path, srt_path)

    print(f"  Video composed: {output_path}")
    return output_path
