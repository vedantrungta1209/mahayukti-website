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
ZOOM_AMOUNT = 0.05   # 5% zoom over each slide's duration


def _ken_burns(img_path: str, duration: float, zoom_in: bool = True) -> VideoClip:
    """Wrap a static slide PNG in a slow Ken Burns zoom for motion feel."""
    pil_img = PILImage.open(img_path).convert("RGB")
    orig_w, orig_h = pil_img.size

    def make_frame(t: float) -> np.ndarray:
        progress = t / duration
        scale = (1.0 + ZOOM_AMOUNT * progress) if zoom_in else (1.0 + ZOOM_AMOUNT * (1.0 - progress))
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        resized = pil_img.resize((new_w, new_h), PILImage.BILINEAR)
        x0 = (new_w - orig_w) // 2
        y0 = (new_h - orig_h) // 2
        return np.array(resized.crop((x0, y0, x0 + orig_w, y0 + orig_h)))

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def compose_video(audio_path: str, script_data: dict, output_path: str) -> str:
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

    # Alternate zoom-in / zoom-out for each slide (Ken Burns rhythm)
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

    print(f"  Video composed: {output_path}")
    return output_path
