"""
Video composer. Pipeline:
  channel intro card → cold open → kinetic slides + b-roll → CTA
No external APIs. Audio synced to exact TTS duration.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from moviepy import AudioFileClip, VideoClip, VideoFileClip, concatenate_videoclips

from frame_generator import create_thumbnail as _fg_thumbnail
from broll import fetch_broll_clip, get_broll_query
from fx import (
    make_channel_intro_frames,
    make_cold_open_frames,
    make_counter_frames,
    make_kinetic_slide_frames,
    make_cta_frames,
    make_lower_third_overlay,
    apply_cinematic_grade,
    frames_to_video,
    xfade_concat,
    dark_overlay,
    gradient_overlay,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _audio_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def _get_bg(category: str, topic: str, w: int, h: int, cfg) -> Image.Image | None:
    """Pexels b-roll frame → Pollinations fallback."""
    pexels_query = get_broll_query(getattr(cfg, "CHANNEL_ID", ""), category, topic)
    clip = fetch_broll_clip(pexels_query, duration=5.0, width=w, height=h, idx=0)
    if clip:
        try:
            frame_path = clip.replace(".mp4", "_bg.jpg")
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error",
                 "-ss", "1", "-i", clip, "-vframes", "1", frame_path],
                capture_output=True,
            )
            if Path(frame_path).exists():
                return Image.open(frame_path).convert("RGB").resize((w, h), Image.LANCZOS)
        except Exception:
            pass
    from frame_generator import _get_bg as _fg_bg
    return _fg_bg(category, topic, w, h, cfg)


def _attach_subtitles(video_path: str, srt_path: str) -> None:
    """Mux SRT as a soft subtitle track so YouTube picks it up automatically.
    Does NOT burn text into the picture — kinetic slides are the visual story."""
    tmp = video_path.replace(".mp4", "_nosub.mp4")
    os.rename(video_path, tmp)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", tmp, "-i", srt_path,
        "-map", "0:v", "-map", "0:a", "-map", "1:s",
        "-c:v", "copy", "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=hin",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    Path(tmp).unlink(missing_ok=True)
    if result.returncode == 0:
        print("  Subtitles muxed as soft track.")
    else:
        # mov_text mux failed — just keep the video without subtitle track
        os.rename(tmp, video_path) if Path(tmp).exists() else None


def _detect_stat(script_data: dict) -> tuple[str, int, str] | None:
    text = " ".join([
        script_data.get("hook", ""),
        script_data.get("script", ""),
        str(script_data.get("slides", "")),
    ])
    matches = re.findall(r"₹\s?([\d,]+)\s?(?:/day|/month|/hour|crore|lakh)?", text)
    if matches:
        raw = matches[0].replace(",", "")
        try:
            val = int(raw)
            if val > 0:
                suffix = "/day" if "/day" in text else "/month" if "/month" in text else ""
                return "₹", val, suffix
        except ValueError:
            pass
    return None


def _frames_clip(frames: list[np.ndarray], fps: int) -> VideoClip:
    def make_frame(t: float) -> np.ndarray:
        return frames[min(int(t * fps), len(frames) - 1)]
    return VideoClip(make_frame, duration=len(frames) / fps).with_fps(fps)


def _broll_clip(query: str, duration: float, w: int, h: int,
                idx: int = 0) -> VideoClip | None:
    path = fetch_broll_clip(query, duration, w, h, idx)
    if not path:
        return None
    try:
        clip = VideoFileClip(path).subclipped(0, duration)
        if clip.w != w or clip.h != h:
            clip = clip.resized((w, h))
        return clip
    except Exception as e:
        print(f"  B-roll load error: {e}")
        return None


def _mix_video_audio(raw_video: str, audio_path: str, output: str,
                     audio_dur: float) -> None:
    """Mix silent video with audio track. Pads video if shorter; trims to audio length."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", raw_video,
        "-i", audio_path,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        # Use exact audio duration (not -shortest which can cut audio early)
        "-t", str(audio_dur),
        output,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


# ── Shorts pipeline ───────────────────────────────────────────────────────────

def compose_short(audio_path: str, script_data: dict, output_path: str,
                  srt_path: str | None, cfg) -> str:
    base = Path(output_path).parent
    base.mkdir(parents=True, exist_ok=True)

    audio_dur = _audio_duration(audio_path)
    w, h, fps = cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg.FPS
    primary   = cfg.PRIMARY_COLOR
    accent    = cfg.ACCENT_COLOR
    category  = script_data.get("category", "General")
    topic     = script_data.get("topic_name", "")
    slides    = script_data.get("slides", [])
    handle    = cfg.CHANNEL_HANDLE

    # Time budget
    intro_dur  = 3.5     # channel intro card
    cold_dur   = 3.0     # cold open / hook
    cta_dur    = 5.0     # CTA card
    stat_dur   = 3.0 if _detect_stat(script_data) else 0.0
    fixed_dur  = intro_dur + cold_dur + cta_dur + stat_dur
    content_dur = max(audio_dur - fixed_dur, audio_dur * 0.55)
    n_slides    = max(len(slides) - 2, 1)
    per_slide   = max(content_dur / n_slides, 4.5)   # at least 4.5s per slide

    segment_paths = []

    # 1. Channel intro card (replaces D-ID — no watermark, no external API)
    print("  [Channel intro]")
    intro_frames = make_channel_intro_frames(
        handle, topic, primary, accent, w, h, fps, intro_dur,
    )
    intro_path = str(base / "seg_intro.mp4")
    frames_to_video(intro_frames, intro_path, fps)
    segment_paths.append(intro_path)

    # 2. Cold open
    print("  [Cold open]")
    hook = script_data.get("hook", slides[0].get("text", topic) if slides else topic)
    bg   = _get_bg(category, topic, w, h, cfg)
    cold_frames = make_cold_open_frames(
        hook, handle, primary, accent, w, h, fps, cold_dur, bg_image=bg,
    )
    cold_path = str(base / "seg_cold.mp4")
    frames_to_video(cold_frames, cold_path, fps)
    segment_paths.append(cold_path)

    # 3. Stats counter (if ₹ figure found)
    stat = _detect_stat(script_data)
    if stat and stat_dur > 0:
        print("  [Stats counter]")
        pfx, val, sfx = stat
        bg2 = _get_bg(category, "money income earning", w, h, cfg)
        counter_frames = make_counter_frames(
            pfx, val, sfx, "EARNING POTENTIAL", primary, accent,
            w, h, fps, stat_dur, bg_image=bg2,
        )
        ctr_path = str(base / "seg_counter.mp4")
        frames_to_video(counter_frames, ctr_path, fps)
        segment_paths.append(ctr_path)

    # 4. Content slides with b-roll
    content_slides = slides[1:-1] if len(slides) > 2 else slides
    for i, slide in enumerate(content_slides):
        print(f"  [Slide {i+1}/{len(content_slides)}] {slide.get('label', '')}")
        label = slide.get("label", "")
        text  = slide.get("text", "")

        broll_q    = get_broll_query(getattr(cfg, "CHANNEL_ID", ""), label, text)
        broll_clip = _broll_clip(broll_q, 5.0, w, h, idx=i)  # only need first frame

        if broll_clip:
            bg_frame = Image.fromarray(broll_clip.get_frame(0).astype(np.uint8))
            broll_clip.close()
        else:
            bg_frame = _get_bg(category, text, w, h, cfg)

        k_frames = make_kinetic_slide_frames(
            text, label, primary, accent, w, h, fps, per_slide,
            bg_image=bg_frame, is_short=True,
        )
        slide_path = str(base / f"seg_slide_{i}.mp4")
        frames_to_video(k_frames, slide_path, fps)
        segment_paths.append(slide_path)

    # 5. CTA
    print("  [CTA card]")
    bg_cta = _get_bg(category, "subscribe follow social", w, h, cfg)
    cta_frames = make_cta_frames(
        handle, cfg.CTA_LINE1, cfg.CTA_LINE2, cfg.CTA_SUBTEXT,
        primary, accent, w, h, fps, cta_dur, bg_image=bg_cta,
    )
    cta_path = str(base / "seg_cta.mp4")
    frames_to_video(cta_frames, cta_path, fps)
    segment_paths.append(cta_path)

    # 6. Concatenate silent segments
    print("  [Concat segments]")
    raw_video = str(base / "short_raw.mp4")
    xfade_concat(segment_paths, raw_video)

    # 7. Mix with audio (exact duration match — no cut, no overflow)
    print("  [Mix audio]")
    _mix_video_audio(raw_video, audio_path, output_path, audio_dur)
    Path(raw_video).unlink(missing_ok=True)

    # 8. Subtitles
    if srt_path and Path(srt_path).exists():
        _attach_subtitles(output_path, srt_path)

    # 9. Cinematic grade
    graded = output_path.replace(".mp4", "_graded.mp4")
    if apply_cinematic_grade(output_path, graded):
        shutil.move(graded, output_path)

    print(f"  Short: {output_path}")
    return output_path


# ── Long-form pipeline ────────────────────────────────────────────────────────

def compose_long(audio_path: str, script_data: dict, output_path: str,
                 srt_path: str | None, cfg) -> str:
    base = Path(output_path).parent
    base.mkdir(parents=True, exist_ok=True)

    audio_dur = _audio_duration(audio_path)
    w, h, fps = cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg.FPS
    primary   = cfg.PRIMARY_COLOR
    accent    = cfg.ACCENT_COLOR
    category  = script_data.get("_category", "General")
    items     = script_data.get("items", script_data.get("tools", []))
    ep_title  = script_data.get("episode_title", "")
    char_name = getattr(cfg, "CHARACTER_NAME", cfg.CHANNEL_NAME)

    # Time budget
    intro_dur   = 3.5
    title_dur   = 4.5
    outro_dur   = 5.0
    fixed_dur   = intro_dur + title_dur + outro_dur
    content_dur = max(audio_dur - fixed_dur, audio_dur * 0.75)
    per_item    = content_dur / max(len(items), 1)
    per_slide   = max(per_item / 3, 4.0)   # 3 slides per item, minimum 4s each

    segment_paths = []

    # 1. Channel intro card
    print("  [Channel intro]")
    intro_frames = make_channel_intro_frames(
        cfg.CHANNEL_HANDLE, ep_title, primary, accent, w, h, fps, intro_dur,
    )
    intro_path = str(base / "seg_intro.mp4")
    frames_to_video(intro_frames, intro_path, fps)
    segment_paths.append(intro_path)

    # 2. Cinematic title card
    print("  [Title card]")
    bg = _get_bg(category, ep_title, w, h, cfg)
    title_frames = make_cold_open_frames(
        ep_title, cfg.CHANNEL_NAME, primary, accent,
        w, h, fps, title_dur, bg_image=bg,
    )
    title_path = str(base / "seg_title.mp4")
    frames_to_video(title_frames, title_path, fps)
    segment_paths.append(title_path)

    # 3. Per-item segments (3 slides each)
    for item_idx, item in enumerate(items):
        item_name = item.get("name", "")
        item_cat  = item.get("category", category)
        kpts      = item.get("key_points", [])[:3]
        summary   = item.get("summary", item.get("india_verdict", ""))
        rank      = item.get("rank", item_idx + 1)

        print(f"  [Item {rank}: {item_name[:35]}]")

        # Shared b-roll for this item — only need first frame as still background
        broll_a = _broll_clip(
            get_broll_query(getattr(cfg, "CHANNEL_ID", ""), item_cat, item_name),
            5.0, w, h, idx=item_idx,
        )
        bg_a = (Image.fromarray(broll_a.get_frame(0).astype(np.uint8))
                if broll_a else _get_bg(item_cat, item_name, w, h, cfg))
        if broll_a:
            broll_a.close()

        # Slide A — item title
        frames_a = make_kinetic_slide_frames(
            f"#{rank} — {item_name}", cfg.LONG_INTRO_BADGE, primary, accent,
            w, h, fps, per_slide, bg_image=bg_a, is_short=False,
        )
        path_a = str(base / f"seg_{item_idx}_a.mp4")
        frames_to_video(frames_a, path_a, fps)
        segment_paths.append(path_a)

        # Slide B — key points
        kpt_text = " • ".join(kpts) if kpts else summary[:140]
        broll_b = _broll_clip(
            get_broll_query(getattr(cfg, "CHANNEL_ID", ""), item_cat, kpt_text[:30]),
            5.0, w, h, idx=item_idx + 1,
        )
        bg_b = (Image.fromarray(broll_b.get_frame(0).astype(np.uint8))
                if broll_b else _get_bg(item_cat, kpt_text[:40], w, h, cfg))
        if broll_b:
            broll_b.close()

        frames_b = make_kinetic_slide_frames(
            kpt_text, "KEY POINTS", primary, accent,
            w, h, fps, per_slide, bg_image=bg_b, is_short=False,
        )
        path_b = str(base / f"seg_{item_idx}_b.mp4")
        frames_to_video(frames_b, path_b, fps)
        segment_paths.append(path_b)

        # Slide C — verdict with lower-third
        frames_c_list = make_kinetic_slide_frames(
            summary[:220] if summary else kpt_text, "KEY TAKEAWAY",
            primary, accent, w, h, fps, per_slide,
            bg_image=bg_a, is_short=False,
        )

        # Lower-third overlay on last 1.5s
        lt_start = max(0, len(frames_c_list) - int(1.5 * fps))
        from PIL import ImageDraw as _ID
        for fi in range(lt_start, len(frames_c_list)):
            progress = min(1.0, (fi - lt_start) / max(int(0.4 * fps), 1))
            img = Image.fromarray(frames_c_list[fi])
            draw = _ID.Draw(img)
            make_lower_third_overlay(
                draw, char_name, getattr(cfg, "CHANNEL_NAME", ""),
                primary, accent, w, h, progress,
            )
            frames_c_list[fi] = np.array(img)

        path_c = str(base / f"seg_{item_idx}_c.mp4")
        frames_to_video(frames_c_list, path_c, fps)
        segment_paths.append(path_c)

    # 4. Outro
    print("  [Outro]")
    bg_out = _get_bg(category, "subscribe channel", w, h, cfg)
    outro_frames = make_cta_frames(
        cfg.CHANNEL_HANDLE, cfg.OUTRO_LINE1, cfg.OUTRO_LINE2, cfg.OUTRO_BELL_TEXT,
        primary, accent, w, h, fps, outro_dur, bg_image=bg_out,
    )
    outro_path = str(base / "seg_outro.mp4")
    frames_to_video(outro_frames, outro_path, fps)
    segment_paths.append(outro_path)

    # 5. Concat silent segments
    print("  [Concat]")
    raw_video = str(base / "long_raw.mp4")
    xfade_concat(segment_paths, raw_video)

    # 6. Mix audio (exact duration)
    print("  [Mix audio]")
    _mix_video_audio(raw_video, audio_path, output_path, audio_dur)
    Path(raw_video).unlink(missing_ok=True)

    # 7. Subtitles
    if srt_path and Path(srt_path).exists():
        _attach_subtitles(output_path, srt_path)

    # 8. Cinematic grade
    graded = output_path.replace(".mp4", "_graded.mp4")
    if apply_cinematic_grade(output_path, graded):
        shutil.move(graded, output_path)

    print(f"  Long-form: {output_path}")
    return output_path


# ── Thumbnail ─────────────────────────────────────────────────────────────────

def generate_thumbnail(script_data: dict, output_path: str, cfg) -> str:
    title    = script_data.get("title", script_data.get("episode_title", ""))
    items    = script_data.get("items", script_data.get("tools", []))
    category = items[0].get("category", "General") if items else "General"
    return _fg_thumbnail(title, category, output_path, cfg)
