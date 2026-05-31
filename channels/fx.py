"""
Motion graphics engine — animated stats, kinetic text, lower thirds,
title cards, spotlight effects, color grading.
All rendered via PIL + MoviePy + FFmpeg. No external services needed.
"""
import os
import subprocess
import math
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Font helpers ──────────────────────────────────────────────────────────────

_BOLD_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
_REG_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = _BOLD_PATHS if bold else _REG_PATHS
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], []
    draw = ImageDraw.Draw(Image.new("RGB", (max_w * 2, 100)))
    for word in words:
        test = " ".join(cur + [word])
        if draw.textbbox((0, 0), test, font=font)[2] > max_w and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines


# ── Dark overlay + gradient ────────────────────────────────────────────────────

def dark_overlay(img: Image.Image, opacity: int = 140) -> Image.Image:
    ov = Image.new("RGBA", img.size, (0, 0, 0, opacity))
    base = img.convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def gradient_overlay(img: Image.Image, color: tuple = (0, 0, 0),
                     top_opacity: int = 0, bottom_opacity: int = 200) -> Image.Image:
    h, w = img.size[1], img.size[0]
    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grad)
    for y in range(h):
        a = int(top_opacity + (bottom_opacity - top_opacity) * (y / h))
        draw.line([(0, y), (w, y)], fill=(*color, a))
    base = img.convert("RGBA")
    base.alpha_composite(grad)
    return base.convert("RGB")


# ── Animated cold-open title card ──────────────────────────────────────────────

def make_cold_open_frames(
    headline: str,
    subtext: str,
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    fps: int,
    duration: float,
    bg_image: Image.Image | None = None,
) -> list[np.ndarray]:
    """
    Creates a dramatic title card with animated text reveal.
    3-phase: fade-in (0.4s) → hold → fade-out (0.3s)
    """
    n_frames = int(duration * fps)
    fade_in  = int(0.4 * fps)
    fade_out = int(0.3 * fps)
    frames   = []

    hl_font = _font(min(120, max(60, 1400 // max(len(headline), 1))), bold=True)
    sub_font = _font(40, bold=False)

    for i in range(n_frames):
        # Alpha for fade
        if i < fade_in:
            alpha = i / fade_in
        elif i > n_frames - fade_out:
            alpha = (n_frames - i) / fade_out
        else:
            alpha = 1.0

        # Slide-in offset (text rises into place)
        slide_progress = min(1.0, i / max(fade_in, 1))
        y_offset = int((1 - slide_progress) * 60)

        if bg_image:
            base = bg_image.copy().resize((width, height), Image.LANCZOS)
            base = dark_overlay(base, opacity=int(150 * alpha))
        else:
            bg_val = int(10 * alpha)
            base = Image.new("RGB", (width, height), (bg_val, bg_val, bg_val + 5))

        draw = ImageDraw.Draw(base)

        # Accent bar
        bar_h = 6
        bar_alpha_val = int(255 * alpha)
        # Draw accent bar
        bar_img = Image.new("RGBA", (width, bar_h), (*accent_color, bar_alpha_val))
        base.paste(bar_img.convert("RGB"),
                   (0, height // 2 - 80 + y_offset),
                   mask=bar_img.split()[3])

        # Headline
        hl_lines = _wrap(headline, hl_font, width - 80)
        y_start = height // 2 - len(hl_lines) * 65 + y_offset
        for line in hl_lines:
            bbox = draw.textbbox((0, 0), line, font=hl_font)
            x = (width - (bbox[2] - bbox[0])) // 2
            # Shadow
            draw.text((x + 3, y_start + 3), line, font=hl_font,
                      fill=(0, 0, 0))
            # Main text with alpha simulation
            r, g, b = (255, 255, 255)
            c = (int(r * alpha), int(g * alpha), int(b * alpha))
            draw.text((x, y_start), line, font=hl_font, fill=c)
            y_start += 75

        # Subtext
        if subtext:
            sub_lines = _wrap(subtext, sub_font, width - 120)
            y_sub = y_start + 20
            for line in sub_lines:
                bbox = draw.textbbox((0, 0), line, font=sub_font)
                x = (width - (bbox[2] - bbox[0])) // 2
                c = (int(primary_color[0] * alpha),
                     int(primary_color[1] * alpha),
                     int(primary_color[2] * alpha))
                draw.text((x, y_sub), line, font=sub_font, fill=c)
                y_sub += 48

        frames.append(np.array(base))

    return frames


# ── Animated number counter ────────────────────────────────────────────────────

def make_counter_frames(
    prefix: str,          # e.g. "₹"
    target: int,          # e.g. 50000
    suffix: str,          # e.g. "/day"
    label: str,           # e.g. "EARNING POTENTIAL"
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    fps: int,
    duration: float,
    bg_image: Image.Image | None = None,
) -> list[np.ndarray]:
    """Counter that counts up from 0 to target over duration with easing."""
    n_frames = int(duration * fps)
    frames   = []
    num_font = _font(min(160, max(80, 1200 // max(len(str(target)), 1))), bold=True)
    lbl_font = _font(36, bold=True)
    pfx_font = _font(80, bold=True)

    def ease_out(t: float) -> float:
        return 1 - (1 - t) ** 3

    for i in range(n_frames):
        t = i / n_frames
        val = int(ease_out(t) * target)

        if bg_image:
            base = dark_overlay(bg_image.copy().resize((width, height), Image.LANCZOS), 160)
        else:
            base = Image.new("RGB", (width, height), (8, 6, 2))

        draw = ImageDraw.Draw(base)

        # Glow effect — draw text slightly larger in accent color first
        val_str = f"{prefix}{val:,}{suffix}"
        bbox = draw.textbbox((0, 0), val_str, font=num_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        y = height // 2 - (bbox[3] - bbox[1]) // 2 - 20

        # Glow passes
        for glow in range(3, 0, -1):
            glow_color = (
                min(255, accent_color[0] + 30),
                min(255, accent_color[1] + 30),
                min(255, accent_color[2] + 30),
            )
            draw.text((x - glow, y - glow), val_str, font=num_font,
                      fill=(*glow_color, 40))

        # Shadow
        draw.text((x + 4, y + 4), val_str, font=num_font, fill=(0, 0, 0))
        # Main
        draw.text((x, y), val_str, font=num_font, fill=(255, 255, 255))

        # Label below
        lbbox = draw.textbbox((0, 0), label, font=lbl_font)
        lx = (width - (lbbox[2] - lbbox[0])) // 2
        draw.text((lx, y + (bbox[3] - bbox[1]) + 20), label,
                  font=lbl_font, fill=primary_color)

        # Accent line
        bar_y = y - 20
        draw.rectangle([width // 2 - 100, bar_y, width // 2 + 100, bar_y + 4],
                        fill=accent_color)

        frames.append(np.array(base))

    return frames


# ── Lower third (character name + title) ─────────────────────────────────────

def make_lower_third_overlay(
    draw: ImageDraw.ImageDraw,
    name: str,
    title: str,
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    progress: float,   # 0→1 for slide-in animation
) -> None:
    """Draw animated lower-third onto an existing draw context."""
    name_font  = _font(38, bold=True)
    title_font = _font(26, bold=False)

    bar_w = 340
    bar_h = 72
    x_final = 40
    y_pos   = height - 150

    # Slide in from left
    x = int(x_final - (1 - progress) * (bar_w + 100))

    # Background pill
    draw.rounded_rectangle(
        [x, y_pos, x + bar_w, y_pos + bar_h],
        radius=8,
        fill=(0, 0, 0),
    )
    # Accent left edge
    draw.rounded_rectangle(
        [x, y_pos, x + 6, y_pos + bar_h],
        radius=4,
        fill=primary_color,
    )

    # Name
    draw.text((x + 18, y_pos + 6), name, font=name_font, fill=(255, 255, 255))
    # Title
    draw.text((x + 18, y_pos + 42), title, font=title_font, fill=accent_color)


# ── Kinetic text overlay on a video frame ─────────────────────────────────────

def make_kinetic_slide_frames(
    text: str,
    label: str,
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    fps: int,
    duration: float,
    bg_image: Image.Image | None = None,
    is_short: bool = True,
) -> list[np.ndarray]:
    """
    Kinetic text slide: text reveals word by word, with subtle scale animation.
    """
    words     = text.split()
    n_frames  = int(duration * fps)
    frames    = []
    reveal_in = int(0.7 * fps)   # first 0.7s revealing words

    lbl_font  = _font(24, bold=True)
    txt_font_size = 64 if is_short else 52
    txt_font  = _font(txt_font_size, bold=True)

    words_per_frame = max(1, len(words) * fps // max(reveal_in, 1))

    for i in range(n_frames):
        if bg_image:
            base = dark_overlay(
                bg_image.copy().resize((width, height), Image.LANCZOS),
                opacity=165
            )
        else:
            base = Image.new("RGB", (width, height), (10, 8, 4))

        draw = ImageDraw.Draw(base)

        # How many words are revealed so far
        if i < reveal_in:
            n_revealed = max(1, int(len(words) * (i / reveal_in)))
        else:
            n_revealed = len(words)

        # Build revealed + hidden text
        revealed  = " ".join(words[:n_revealed])
        hidden    = " ".join(words[n_revealed:])
        full_text = text

        # Wrap the full text to get consistent layout
        lines      = _wrap(full_text, txt_font, width - 80)
        total_h    = len(lines) * (txt_font_size + 14)
        y_start    = height // 2 - total_h // 2 - 20

        # Draw each line with word-level reveal
        revealed_words_left = n_revealed
        for line in lines:
            line_words  = line.split()
            n_draw      = min(len(line_words), revealed_words_left)
            revealed_words_left -= n_draw

            drawn_part   = " ".join(line_words[:n_draw])
            undawn_part  = " ".join(line_words[n_draw:])

            bbox = draw.textbbox((0, 0), line, font=txt_font)
            x = (width - (bbox[2] - bbox[0])) // 2

            if drawn_part:
                # Revealed words — bright white with shadow
                draw.text((x + 3, y_start + 3), drawn_part, font=txt_font, fill=(0, 0, 0))
                draw.text((x, y_start), drawn_part, font=txt_font, fill=(255, 255, 255))
                drawn_bbox = draw.textbbox((0, 0), drawn_part + " ", font=txt_font)
                x += drawn_bbox[2] - drawn_bbox[0]

            if undawn_part:
                # Hidden words — dim
                draw.text((x, y_start), undawn_part, font=txt_font, fill=(80, 80, 80))

            y_start += txt_font_size + 14

        # Label chip at top
        if label:
            _draw_label_chip(draw, label, primary_color, accent_color, 40, 40)

        # Bottom accent bar
        draw.rectangle(
            [0, height - 6, width, height],
            fill=primary_color,
        )
        draw.rectangle([0, 0, width, 6], fill=primary_color)

        frames.append(np.array(base))

    return frames


def _draw_label_chip(draw, text: str, bg_color: tuple, text_color: tuple,
                     x: int, y: int) -> None:
    font = _font(22, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    pw, ph = bbox[2] - bbox[0] + 24, bbox[3] - bbox[1] + 12
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=bg_color)
    draw.text((x + 12, y + 6), text, font=font, fill=(0, 0, 0))


# ── CTA card ──────────────────────────────────────────────────────────────────

def make_cta_frames(
    channel_handle: str,
    cta_line1: str,
    cta_line2: str,
    cta_subtext: str,
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    fps: int,
    duration: float,
    bg_image: Image.Image | None = None,
) -> list[np.ndarray]:
    """Pulsing CTA card with subscribe animation."""
    n_frames = int(duration * fps)
    frames   = []
    l1_font  = _font(64, bold=True)
    l2_font  = _font(72, bold=True)
    h_font   = _font(80, bold=True)
    sub_font = _font(30, bold=False)

    for i in range(n_frames):
        # Pulse effect on handle text
        pulse = 1.0 + 0.04 * math.sin(i * math.pi * 2 / fps)

        if bg_image:
            base = dark_overlay(bg_image.copy().resize((width, height), Image.LANCZOS), 170)
        else:
            base = Image.new("RGB", (width, height), (8, 5, 2))

        draw = ImageDraw.Draw(base)

        draw.rectangle([0, 0, width, 6], fill=primary_color)
        draw.rectangle([0, height - 6, width, height], fill=primary_color)

        y1 = height // 2 - 220
        for text, font, color in [
            (cta_line1, l1_font, (255, 255, 255)),
            (cta_line2, l2_font, accent_color),
        ]:
            bbox = draw.textbbox((0, 0), text, font=font)
            x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((x + 2, y1 + 2), text, font=font, fill=(0, 0, 0))
            draw.text((x, y1), text, font=font, fill=color)
            y1 += (bbox[3] - bbox[1]) + 16

        # Pulsing handle
        h_size = int(80 * pulse)
        h_font_p = _font(h_size, bold=True)
        hbbox = draw.textbbox((0, 0), channel_handle, font=h_font_p)
        hx = (width - (hbbox[2] - hbbox[0])) // 2
        hy = height // 2 + 15
        draw.text((hx + 3, hy + 3), channel_handle, font=h_font_p, fill=(0, 0, 0))
        draw.text((hx, hy), channel_handle, font=h_font_p, fill=primary_color)

        # Subtext
        sb_bbox = draw.textbbox((0, 0), cta_subtext, font=sub_font)
        sx = (width - (sb_bbox[2] - sb_bbox[0])) // 2
        draw.text((sx, hy + h_size + 20), cta_subtext, font=sub_font, fill=(180, 180, 180))

        frames.append(np.array(base))

    return frames


# ── FFmpeg color grading (cinematic warm Indian tone) ─────────────────────────

def apply_cinematic_grade(input_path: str, output_path: str) -> bool:
    """
    Applies cinematic color grading:
    - Warm color temperature (golden Indian tone)
    - Slight contrast boost
    - Subtle vignette
    - Lifted shadows (cinematic look)
    """
    vf = (
        "curves=r='0/0 0.2/0.22 0.5/0.55 0.8/0.83 1/1':"
        "g='0/0 0.2/0.2 0.5/0.52 0.8/0.8 1/1':"
        "b='0/0 0.2/0.17 0.5/0.46 0.8/0.76 1/0.95',"    # warm tone
        "eq=contrast=1.08:brightness=0.02:saturation=1.12,"   # contrast + sat
        "vignette=PI/3.5"                                      # vignette
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-c:a", "copy",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print("  Cinematic grade applied.")
        return True
    print(f"  Grade warning: {r.stderr[:200]}")
    return False


# ── Frames → video ────────────────────────────────────────────────────────────

def frames_to_video(frames: list[np.ndarray], output_path: str, fps: int) -> str:
    """Convert a list of numpy frames to an mp4 via MoviePy."""
    from moviepy import VideoClip

    def make_frame(t: float) -> np.ndarray:
        idx = min(int(t * fps), len(frames) - 1)
        return frames[idx]

    duration = len(frames) / fps
    clip = VideoClip(make_frame, duration=duration).with_fps(fps)
    clip.write_videofile(output_path, fps=fps, codec="libx264",
                         audio=False, preset="ultrafast", logger=None)
    clip.close()
    return output_path


# ── xfade transition between two clips ───────────────────────────────────────

def xfade_concat(clip_paths: list[str], output_path: str,
                 transition: str = "fade", duration: float = 0.3) -> bool:
    """Concatenate clips with smooth xfade transitions."""
    if len(clip_paths) == 1:
        import shutil
        shutil.copy2(clip_paths[0], output_path)
        return True

    # Build ffmpeg xfade filter chain
    n = len(clip_paths)
    inputs = []
    for p in clip_paths:
        inputs += ["-i", p]

    # Build complex filter
    # We need to calculate cumulative offsets
    # Get durations first
    durations = []
    for p in clip_paths:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", p],
            capture_output=True, text=True,
        )
        import json
        try:
            d = float(json.loads(r.stdout)["format"]["duration"])
        except Exception:
            d = 3.0
        durations.append(d)

    # Simple concat for now (xfade gets complex with n>2, use concat filter)
    list_file = output_path + ".concat.txt"
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{Path(p).resolve()}'\n")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    Path(list_file).unlink(missing_ok=True)
    return r.returncode == 0
