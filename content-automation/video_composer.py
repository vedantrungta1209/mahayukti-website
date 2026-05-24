import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips

from frame_generator import (
    create_title_frame, create_point_frame, create_hook_frame, create_outro_frame,
)
from config import OUTPUT_DIR, CHANNEL_NAME, CHANNEL_HANDLE, FPS

TITLE_DURATION = 8
HOOK_DURATION = 12
OUTRO_DURATION = 10
MIN_POINT_DURATION = 15

ZOOM_AMOUNT = 0.15   # 15% zoom — clearly visible motion
PAN_AMOUNT = 0.08    # 8% pan across the frame


def _ken_burns(img_path: str, duration: float, zoom_in: bool = True) -> VideoClip:
    """Ken Burns effect: zoom + pan for dynamic motion on static slides."""
    pil_img = PILImage.open(img_path).convert("RGB")
    orig_w, orig_h = pil_img.size

    def make_frame(t: float) -> np.ndarray:
        progress = t / duration
        scale = (1.0 + ZOOM_AMOUNT * progress) if zoom_in else (1.0 + ZOOM_AMOUNT * (1.0 - progress))
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        resized = pil_img.resize((new_w, new_h), PILImage.BILINEAR)

        margin_x = new_w - orig_w
        margin_y = new_h - orig_h

        if zoom_in:
            # Pan from top-left toward center as we zoom in
            x0 = int(margin_x * PAN_AMOUNT * (1.0 - progress))
            y0 = int(margin_y * PAN_AMOUNT * (1.0 - progress))
        else:
            # Pan from center toward bottom-right as we zoom out
            x0 = int(margin_x * (0.5 + PAN_AMOUNT * progress))
            y0 = int(margin_y * (0.5 + PAN_AMOUNT * progress))

        x0 = max(0, min(x0, margin_x))
        y0 = max(0, min(y0, margin_y))
        return np.array(resized.crop((x0, y0, x0 + orig_w, y0 + orig_h)))

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def _burn_subtitles(video_path: str, srt_path: str) -> None:
    """Burn SRT subtitles into video in-place using ffmpeg."""
    tmp = video_path.replace(".mp4", "_raw.mp4")
    os.rename(video_path, tmp)

    srt_abs = str(Path(srt_path).resolve())
    style = (
        "FontName=DejaVu Sans,"
        "FontSize=26,"
        "PrimaryColour=&H00FFFFFF,"   # white text
        "BorderStyle=3,"              # opaque background box
        "BackColour=&HAA000000,"      # dark semi-transparent bg
        "Outline=0,Shadow=0,"
        "Alignment=2,MarginV=55"      # bottom center
    )

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", tmp,
        "-vf", f"subtitles={srt_abs}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "copy",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp)

    if result.returncode != 0:
        print(f"  Subtitle burn warning: {result.stderr[:300]}")
    else:
        print(f"  Subtitles burned in.")


def compose_video(
    audio_path: str,
    script_data: dict,
    output_path: str,
    srt_path: str | None = None,
) -> str:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    audio = AudioFileClip(audio_path)
    total = audio.duration
    key_points: list[str] = script_data["key_points"]

    fixed_time = TITLE_DURATION + HOOK_DURATION + OUTRO_DURATION
    point_time = max((total - fixed_time) / len(key_points), MIN_POINT_DURATION)

    slides: list[tuple[str, float]] = []

    title_path = f"{OUTPUT_DIR}/slide_title.png"
    create_title_frame(script_data["title"], CHANNEL_NAME, title_path)
    slides.append((title_path, TITLE_DURATION))

    hook_path = f"{OUTPUT_DIR}/slide_hook.png"
    create_hook_frame(script_data["hook"], CHANNEL_NAME, hook_path)
    slides.append((hook_path, HOOK_DURATION))

    for i, point in enumerate(key_points):
        frame_path = f"{OUTPUT_DIR}/slide_point_{i}.png"
        create_point_frame(i + 1, point, CHANNEL_NAME, frame_path)
        slides.append((frame_path, point_time))

    outro_path = f"{OUTPUT_DIR}/slide_outro.png"
    create_outro_frame(CHANNEL_NAME, CHANNEL_HANDLE, outro_path)
    slides.append((outro_path, OUTRO_DURATION))

    # Alternate zoom-in / zoom-out for natural Ken Burns rhythm
    clips = [_ken_burns(path, dur, zoom_in=(i % 2 == 0)) for i, (path, dur) in enumerate(slides)]
    video = concatenate_videoclips(clips)

    if video.duration > total:
        video = video.subclipped(0, total)

    final = video.with_audio(audio)
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None,
    )

    audio.close()
    final.close()

    # Burn in subtitles as a second fast ffmpeg pass
    if srt_path and Path(srt_path).exists():
        _burn_subtitles(output_path, srt_path)

    print(f"  Video composed: {output_path}")
    return output_path
