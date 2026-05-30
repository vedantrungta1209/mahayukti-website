import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image as PILImage
from moviepy import AudioFileClip, VideoClip, concatenate_videoclips

from frame_generator import (
    create_short_title_frame, create_short_info_frame, create_short_cta_frame,
    create_long_intro_frame, create_long_tool_frame, create_long_outro_frame,
    create_thumbnail,
)
from config import OUTPUT_DIR, SHORT_WIDTH, SHORT_HEIGHT, LONG_WIDTH, LONG_HEIGHT, FPS

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

    return VideoClip(make_frame, duration=duration).with_fps(FPS)


def _burn_subtitles(video_path: str, srt_path: str) -> None:
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
            w: int, h: int, srt_path: str | None) -> str:
    audio = AudioFileClip(audio_path)
    clips = [_ken_burns(p, d, w, h, zoom_in=(i % 2 == 0)) for i, (p, d) in enumerate(slides)]
    video = concatenate_videoclips(clips)
    if video.duration > audio.duration:
        video = video.subclipped(0, audio.duration)
    final = video.with_audio(audio)
    final.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac",
                          preset="ultrafast", threads=4, logger=None)
    audio.close()
    final.close()
    if srt_path and Path(srt_path).exists():
        _burn_subtitles(output_path, srt_path)
    print(f"  Video: {output_path}")
    return output_path


def compose_short(audio_path: str, script_data: dict, output_path: str, srt_path: str | None = None) -> str:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    audio = AudioFileClip(audio_path)
    total = audio.duration
    audio.close()

    tool_name = script_data.get("tool_name", "AI Tool")
    category  = script_data.get("category", "Productivity")

    slides_def = script_data.get("slides", [])
    n = max(len(slides_def), 1)
    per_slide = total / n

    slides: list[tuple[str, float]] = []

    title_path = f"{OUTPUT_DIR}/short_slide_0.png"
    create_short_title_frame(tool_name, category, title_path)
    slides.append((title_path, per_slide))

    for i, slide in enumerate(slides_def[1:-1], 1):
        path = f"{OUTPUT_DIR}/short_slide_{i}.png"
        create_short_info_frame(slide.get("label", ""), slide.get("text", ""), category, tool_name, path)
        slides.append((path, per_slide))

    cta_path = f"{OUTPUT_DIR}/short_slide_cta.png"
    create_short_cta_frame(category, tool_name, cta_path)
    slides.append((cta_path, per_slide))

    return _render(slides, audio_path, output_path, SHORT_WIDTH, SHORT_HEIGHT, srt_path)


def compose_long(audio_path: str, script_data: dict, output_path: str, srt_path: str | None = None) -> str:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    audio = AudioFileClip(audio_path)
    total = audio.duration
    audio.close()

    tools = script_data.get("tools", [])
    category = script_data.get("_first_category", "Productivity")

    n_slides = 1 + len(tools) * 3 + 1
    per_slide = total / n_slides

    slides: list[tuple[str, float]] = []

    intro_path = f"{OUTPUT_DIR}/long_slide_intro.png"
    create_long_intro_frame(script_data.get("episode_title", "Top 5 AI Tools This Week"), category, intro_path)
    slides.append((intro_path, per_slide))

    for i, tool in enumerate(tools):
        tool_category = tool.get("category", category)
        tool_name = tool.get("name", "AI Tool")

        title_path = f"{OUTPUT_DIR}/long_slide_{i}_title.png"
        create_long_tool_frame(
            tool["rank"], tool_name,
            [f"#{tool['rank']} This Week", tool.get("india_verdict", "")[:60], ""],
            tool.get("india_verdict", ""), tool_category, title_path,
        )
        slides.append((title_path, per_slide))

        pts_path = f"{OUTPUT_DIR}/long_slide_{i}_pts.png"
        create_long_tool_frame(
            tool["rank"], tool_name,
            tool.get("key_points", [])[:3],
            tool.get("india_verdict", ""), tool_category, pts_path,
        )
        slides.append((pts_path, per_slide))

        verdict_path = f"{OUTPUT_DIR}/long_slide_{i}_verdict.png"
        create_long_tool_frame(
            tool["rank"], tool_name,
            ["India Verdict:", tool.get("india_verdict", ""), ""],
            tool.get("india_verdict", ""), tool_category, verdict_path,
        )
        slides.append((verdict_path, per_slide))

    outro_path = f"{OUTPUT_DIR}/long_slide_outro.png"
    create_long_outro_frame(category, outro_path)
    slides.append((outro_path, per_slide))

    return _render(slides, audio_path, output_path, LONG_WIDTH, LONG_HEIGHT, srt_path)


def generate_thumbnail(script_data: dict, output_path: str) -> str:
    title = script_data.get("title", script_data.get("episode_title", "Top 5 AI Tools"))
    tools = script_data.get("tools", [])
    category = tools[0].get("category", "Productivity") if tools else "Productivity"
    return create_thumbnail(title, category, output_path)
