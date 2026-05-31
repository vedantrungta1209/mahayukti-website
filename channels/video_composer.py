"""
Generic video composer — accepts cfg object for all channel-specific settings.
"""
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips

from frame_generator import (
    create_short_title_frame, create_short_info_frame, create_short_cta_frame,
    create_long_intro_frame, create_long_section_frame, create_long_outro_frame,
    create_thumbnail as _create_thumbnail,
)

ZOOM = 0.10
PAN  = 0.05


def _ken_burns(img_path: str, duration: float, w: int, h: int, zoom_in: bool = True) -> VideoClip:
    pil_img = PILImage.open(img_path).convert("RGB")

    def make_frame(t: float) -> np.ndarray:
        progress = t / duration
        scale = (1.0 + ZOOM * progress) if zoom_in else (1.0 + ZOOM * (1.0 - progress))
        new_w, new_h = int(w * scale), int(h * scale)
        resized = pil_img.resize((new_w, new_h), PILImage.BILINEAR)
        mx, my = new_w - w, new_h - h
        x0 = int(mx * PAN * (1.0 - progress)) if zoom_in else int(mx * (0.5 + PAN * progress))
        y0 = int(my * PAN * (1.0 - progress)) if zoom_in else int(my * (0.5 + PAN * progress))
        x0 = max(0, min(x0, mx))
        y0 = max(0, min(y0, my))
        return np.array(resized.crop((x0, y0, x0 + w, y0 + h)))

    return VideoClip(make_frame, duration=duration).with_fps(fps)


def _burn_subtitles(video_path: str, srt_path: str, fps: int) -> None:
    tmp = video_path.replace(".mp4", "_raw.mp4")
    os.rename(video_path, tmp)
    srt_abs = str(Path(srt_path).resolve())
    style = (
        "FontName=DejaVu Sans,FontSize=26,PrimaryColour=&H00FFFFFF,"
        "BorderStyle=3,BackColour=&HAA000000,Outline=0,Shadow=0,"
        "Alignment=2,MarginV=60"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", tmp,
        "-vf", f"subtitles={srt_abs}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "copy", video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp)
    if result.returncode != 0:
        print(f"  Subtitle warning: {result.stderr[:200]}")
    else:
        print("  Subtitles burned in.")


def _render(slides: list[tuple[str, float]], audio_path: str, output_path: str,
            w: int, h: int, fps: int, srt_path: str | None) -> str:
    audio = AudioFileClip(audio_path)

    def _kb(img_path, duration, idx):
        pil_img = PILImage.open(img_path).convert("RGB")
        zoom_in = (idx % 2 == 0)

        def make_frame(t):
            progress = t / duration
            scale = (1.0 + ZOOM * progress) if zoom_in else (1.0 + ZOOM * (1.0 - progress))
            nw, nh = int(w * scale), int(h * scale)
            res = pil_img.resize((nw, nh), PILImage.BILINEAR)
            mx, my = nw - w, nh - h
            x0 = int(mx * PAN * (1.0 - progress)) if zoom_in else int(mx * (0.5 + PAN * progress))
            y0 = int(my * PAN * (1.0 - progress)) if zoom_in else int(my * (0.5 + PAN * progress))
            return np.array(res.crop((max(0, min(x0, mx)), max(0, min(y0, my)),
                                      max(0, min(x0, mx)) + w, max(0, min(y0, my)) + h)))

        return VideoClip(make_frame, duration=duration).with_fps(fps)

    clips = [_kb(p, d, i) for i, (p, d) in enumerate(slides)]
    video = concatenate_videoclips(clips)
    if video.duration > audio.duration:
        video = video.subclipped(0, audio.duration)
    final = video.with_audio(audio)
    final.write_videofile(output_path, fps=fps, codec="libx264", audio_codec="aac",
                          preset="ultrafast", threads=4, logger=None)
    audio.close()
    final.close()
    if srt_path and Path(srt_path).exists():
        _burn_subtitles(output_path, srt_path, fps)
    print(f"  Video: {output_path}")
    return output_path


def compose_short(audio_path: str, script_data: dict, output_path: str,
                  srt_path: str | None, cfg) -> str:
    base = str(Path(output_path).parent)
    Path(base).mkdir(parents=True, exist_ok=True)

    audio = AudioFileClip(audio_path)
    total = audio.duration
    audio.close()

    topic_name = script_data.get("topic_name", "Topic")
    category   = script_data.get("category", "General")
    slides_def = script_data.get("slides", [])
    n          = max(len(slides_def), 1)
    per_slide  = total / n

    slides: list[tuple[str, float]] = []

    title_path = f"{base}/short_slide_0.png"
    create_short_title_frame(topic_name, category, title_path, cfg)
    slides.append((title_path, per_slide))

    for i, slide in enumerate(slides_def[1:-1], 1):
        path = f"{base}/short_slide_{i}.png"
        create_short_info_frame(slide.get("label", ""), slide.get("text", ""),
                                category, topic_name, path, cfg)
        slides.append((path, per_slide))

    cta_path = f"{base}/short_slide_cta.png"
    create_short_cta_frame(category, topic_name, cta_path, cfg)
    slides.append((cta_path, per_slide))

    return _render(slides, audio_path, output_path, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg.FPS, srt_path)


def compose_long(audio_path: str, script_data: dict, output_path: str,
                 srt_path: str | None, cfg) -> str:
    base = str(Path(output_path).parent)
    Path(base).mkdir(parents=True, exist_ok=True)

    audio = AudioFileClip(audio_path)
    total = audio.duration
    audio.close()

    items    = script_data.get("items", script_data.get("tools", []))
    category = script_data.get("_category", items[0].get("category", "General") if items else "General")

    n_slides  = 1 + len(items) * 3 + 1
    per_slide = total / n_slides

    slides: list[tuple[str, float]] = []

    intro_path = f"{base}/long_slide_intro.png"
    create_long_intro_frame(script_data.get("episode_title", ""), category, intro_path, cfg)
    slides.append((intro_path, per_slide))

    for i, item in enumerate(items):
        item_cat  = item.get("category", category)
        item_name = item.get("name", "")
        rank      = item.get("rank", i + 1)
        summary   = item.get("summary", item.get("india_verdict", ""))
        kpts      = item.get("key_points", [])[:3]

        title_path = f"{base}/long_slide_{i}_title.png"
        create_long_section_frame(rank, item_name, [f"#{rank}", summary[:60], ""],
                                  summary, item_cat, title_path, cfg)
        slides.append((title_path, per_slide))

        pts_path = f"{base}/long_slide_{i}_pts.png"
        create_long_section_frame(rank, item_name, kpts, summary, item_cat, pts_path, cfg)
        slides.append((pts_path, per_slide))

        verdict_path = f"{base}/long_slide_{i}_verdict.png"
        create_long_section_frame(rank, item_name, ["Key takeaway:", summary, ""],
                                  summary, item_cat, verdict_path, cfg)
        slides.append((verdict_path, per_slide))

    outro_path = f"{base}/long_slide_outro.png"
    create_long_outro_frame(category, outro_path, cfg)
    slides.append((outro_path, per_slide))

    return _render(slides, audio_path, output_path, cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg.FPS, srt_path)


def generate_thumbnail(script_data: dict, output_path: str, cfg) -> str:
    title    = script_data.get("title", script_data.get("episode_title", ""))
    items    = script_data.get("items", script_data.get("tools", []))
    category = items[0].get("category", "General") if items else "General"
    return _create_thumbnail(title, category, output_path, cfg)
