"""
Motion graphics engine — channel intro, kinetic text, stats, lower thirds,
title cards, color grading. All rendered via PIL + FFmpeg. No external services.
"""
import math
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
    return lines or [""]


# ── Compositing helpers ───────────────────────────────────────────────────────

def dark_overlay(img: Image.Image, opacity: int = 110) -> Image.Image:
    ov = Image.new("RGBA", img.size, (0, 0, 0, opacity))
    base = img.convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def gradient_overlay(img: Image.Image, color: tuple = (0, 0, 0),
                     top_opacity: int = 0, bottom_opacity: int = 180) -> Image.Image:
    w, h = img.size
    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grad)
    for y in range(h):
        a = int(top_opacity + (bottom_opacity - top_opacity) * (y / h))
        draw.line([(0, y), (w, y)], fill=(*color, a))
    base = img.convert("RGBA")
    base.alpha_composite(grad)
    return base.convert("RGB")


def _composite_card(base: Image.Image, x: int, y: int, w: int, h: int,
                    fill_rgba: tuple = (0, 0, 0, 190),
                    radius: int = 18) -> Image.Image:
    """Draw a rounded semi-transparent card onto base, return composited RGB image."""
    card = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill_rgba)
    result = base.convert("RGBA")
    result.alpha_composite(card)
    return result.convert("RGB")


def _accent_bar(base: Image.Image, x: int, y: int, bar_w: int, bar_h: int,
                color: tuple, progress: float = 1.0) -> Image.Image:
    """Draw a colored bar that sweeps in from left based on progress (0→1)."""
    img = base.convert("RGBA")
    bar = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(bar)
    end_x = x + int(bar_w * max(0.0, min(1.0, progress)))
    if end_x > x:
        d.rectangle([x, y, end_x, y + bar_h], fill=(*color, 255))
    img.alpha_composite(bar)
    return img.convert("RGB")


# ── Channel intro card (replaces D-ID) ───────────────────────────────────────

def make_channel_intro_frames(
    channel_handle: str,
    topic_name: str,
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    fps: int,
    duration: float = 3.5,
) -> list[np.ndarray]:
    """
    Animated channel branding intro — no external API, no watermark.
    Phase 0→0.5s : dark bg fades in + accent bar sweeps left→right
    Phase 0.5→2.5s: channel handle scales in, topic slides up
    Phase 2.5→3.5s: smooth fade out
    """
    n_frames = int(duration * fps)
    sweep_end   = int(0.45 * fps)
    hold_end    = n_frames - int(0.5 * fps)
    topic_start = int(0.55 * fps)

    handle_size = min(108, max(56, 1300 // max(len(channel_handle), 1)))
    h_font  = _font(handle_size, bold=True)
    t_font  = _font(46, bold=False)
    sub_font = _font(28, bold=False)

    frames = []
    for i in range(n_frames):
        # Sweep progress (0→1 in first sweep_end frames)
        if i <= sweep_end:
            sweep = i / max(sweep_end, 1)
        elif i <= hold_end:
            sweep = 1.0
        else:
            sweep = 1.0 - (i - hold_end) / max(n_frames - hold_end, 1)

        # Background: very dark with diagonal primary-colour streak
        base = Image.new("RGB", (width, height), (7, 5, 3))
        streak = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sd = ImageDraw.Draw(streak)
        # Two diagonal bands crossing near center
        for off, alpha in [(-width // 3, 22), (0, 30), (width // 3, 18)]:
            sd.polygon(
                [(off, 0), (off + width // 6, 0),
                 (off + width // 6 + height, height), (off + height, height)],
                fill=(*primary_color, alpha),
            )
        base = base.convert("RGBA")
        base.alpha_composite(streak)
        base = base.convert("RGB")

        draw = ImageDraw.Draw(base)

        # Accent bar sweeping in
        bar_y = height // 2 - int(handle_size * 0.65)
        bar_x0 = int(width * 0.08)
        bar_full_w = int(width * 0.84)
        base = _accent_bar(base, bar_x0, bar_y, bar_full_w, 6, accent_color, sweep)
        draw = ImageDraw.Draw(base)

        if sweep > 0.05:
            a = int(255 * sweep)

            # Channel handle — scales from 70% to 100% during sweep-in
            if i <= sweep_end:
                scale = 0.70 + 0.30 * sweep
                fs = max(20, int(handle_size * scale))
                hf = _font(fs, bold=True)
            else:
                hf = h_font

            hbbox = draw.textbbox((0, 0), channel_handle, font=hf)
            hx = (width - (hbbox[2] - hbbox[0])) // 2
            hy = height // 2 - (hbbox[3] - hbbox[1]) // 2 - 30

            draw.text((hx + 4, hy + 4), channel_handle, font=hf,
                      fill=(0, 0, 0))
            draw.text((hx, hy), channel_handle, font=hf,
                      fill=(a, a, a))

        # Topic name — slides up from below after topic_start
        if i >= topic_start:
            t_prog = min(1.0, (i - topic_start) / max(int(0.5 * fps), 1)) * sweep
            if t_prog > 0.05:
                ta = int(255 * t_prog)
                slide_offset = int((1 - t_prog) * 40)

                t_lines = _wrap(topic_name, t_font, int(width * 0.76))
                ty = height // 2 + int(handle_size * 0.55) + slide_offset
                for line in t_lines:
                    tbbox = draw.textbbox((0, 0), line, font=t_font)
                    tx = (width - (tbbox[2] - tbbox[0])) // 2
                    draw.text((tx, ty), line, font=t_font,
                              fill=(int(accent_color[0] * t_prog),
                                    int(accent_color[1] * t_prog),
                                    int(accent_color[2] * t_prog)))
                    ty += 54

        frames.append(np.array(base))

    return frames


# ── Cold-open title card ───────────────────────────────────────────────────────

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
    """Dramatic title card: accent bar sweeps in, headline fades + rises."""
    n_frames  = int(duration * fps)
    fade_in   = int(0.5 * fps)
    fade_out  = int(0.35 * fps)

    hl_size  = min(112, max(56, 1350 // max(len(headline), 1)))
    hl_font  = _font(hl_size, bold=True)
    sub_font = _font(38, bold=False)

    frames = []
    for i in range(n_frames):
        if i < fade_in:
            alpha = i / fade_in
        elif i > n_frames - fade_out:
            alpha = (n_frames - i) / fade_out
        else:
            alpha = 1.0

        slide = min(1.0, i / max(fade_in, 1))
        y_offset = int((1 - slide) * 55)

        if bg_image:
            # Subtle Ken Burns on the title bg
            zoom = 1.0 + 0.06 * (i / n_frames)
            nw, nh = int(width * zoom), int(height * zoom)
            zx, zy = (nw - width) // 2, (nh - height) // 2
            zoomed = bg_image.resize((nw, nh), Image.BILINEAR)
            bg = zoomed.crop((zx, zy, zx + width, zy + height))
            base = dark_overlay(bg, opacity=int(140 * alpha + 20))
            if height > width:  # shorts — extra bottom gradient
                base = gradient_overlay(base, top_opacity=0, bottom_opacity=120)
        else:
            v = int(8 * alpha)
            base = Image.new("RGB", (width, height), (v, v, v + 4))

        draw = ImageDraw.Draw(base)

        # Sweeping accent bar
        bar_y = height // 2 - int(hl_size * 0.7) + y_offset
        base = _accent_bar(base, int(width * 0.08), bar_y, int(width * 0.84), 5,
                           accent_color, progress=slide)
        draw = ImageDraw.Draw(base)

        # Headline — left-aligned from left margin
        lm = 56   # left margin
        hl_lines = _wrap(headline, hl_font, width - lm * 2)
        y_start = height // 2 - len(hl_lines) * (hl_size + 12) // 2 + y_offset
        for line in hl_lines:
            x = lm
            draw.text((x + 3, y_start + 3), line, font=hl_font, fill=(0, 0, 0))
            draw.text((x, y_start), line, font=hl_font,
                      fill=(int(255 * alpha), int(255 * alpha), int(255 * alpha)))
            y_start += hl_size + 12

        # Subtext — left-aligned
        if subtext:
            sub_lines = _wrap(subtext, sub_font, width - lm * 2)
            y_sub = y_start + 18 + y_offset
            for line in sub_lines:
                draw.text((lm, y_sub), line, font=sub_font,
                          fill=(int(primary_color[0] * alpha),
                                int(primary_color[1] * alpha),
                                int(primary_color[2] * alpha)))
                y_sub += 46

        frames.append(np.array(base))

    return frames


# ── Animated number counter ────────────────────────────────────────────────────

def make_counter_frames(
    prefix: str,
    target: int,
    suffix: str,
    label: str,
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    fps: int,
    duration: float,
    bg_image: Image.Image | None = None,
) -> list[np.ndarray]:
    n_frames = int(duration * fps)
    num_font = _font(min(156, max(80, 1200 // max(len(str(target)), 1))), bold=True)
    lbl_font = _font(34, bold=True)

    def ease_out(t: float) -> float:
        return 1 - (1 - t) ** 3

    frames = []
    for i in range(n_frames):
        val = int(ease_out(i / n_frames) * target)

        if bg_image:
            base = dark_overlay(bg_image.copy().resize((width, height), Image.LANCZOS), 160)
        else:
            base = Image.new("RGB", (width, height), (8, 6, 2))

        draw = ImageDraw.Draw(base)
        val_str = f"{prefix}{val:,}{suffix}"
        bbox = draw.textbbox((0, 0), val_str, font=num_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        y = height // 2 - (bbox[3] - bbox[1]) // 2 - 20

        # Glow passes
        for glow in range(3, 0, -1):
            gc = tuple(min(255, c + 40) for c in accent_color)
            draw.text((x - glow, y - glow), val_str, font=num_font, fill=(*gc, 35))

        draw.text((x + 4, y + 4), val_str, font=num_font, fill=(0, 0, 0))
        draw.text((x, y), val_str, font=num_font, fill=(255, 255, 255))

        lbbox = draw.textbbox((0, 0), label, font=lbl_font)
        lx = (width - (lbbox[2] - lbbox[0])) // 2
        draw.text((lx, y + (bbox[3] - bbox[1]) + 18), label,
                  font=lbl_font, fill=primary_color)

        bar_y = y - 18
        draw.rectangle([width // 2 - 90, bar_y, width // 2 + 90, bar_y + 4],
                       fill=accent_color)
        frames.append(np.array(base))

    return frames


# ── Lower third (character name) ──────────────────────────────────────────────

def make_lower_third_overlay(
    draw: ImageDraw.ImageDraw,
    name: str,
    title: str,
    primary_color: tuple,
    accent_color: tuple,
    width: int,
    height: int,
    progress: float,
) -> None:
    name_font  = _font(36, bold=True)
    title_font = _font(24, bold=False)
    bar_w, bar_h = 330, 70
    x_final = 40
    y_pos = height - 145
    x = int(x_final - (1 - progress) * (bar_w + 100))
    draw.rounded_rectangle([x, y_pos, x + bar_w, y_pos + bar_h], radius=8, fill=(0, 0, 0))
    draw.rounded_rectangle([x, y_pos, x + 5, y_pos + bar_h], radius=4, fill=primary_color)
    draw.text((x + 16, y_pos + 6), name, font=name_font, fill=(255, 255, 255))
    draw.text((x + 16, y_pos + 40), title, font=title_font, fill=accent_color)


# ── Kinetic text slide ─────────────────────────────────────────────────────────

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
    Left-anchored bottom strip layout (not centered card):
    - Background fully visible in top ~50% (shorts) / full frame (long)
    - Heavy gradient darkens only the bottom strip where text lives
    - Card spans near-full width, anchored to left edge (not centered)
    - Text: left-aligned, large font, word-by-word reveal
    - Ken Burns zoom on background throughout
    """
    words  = text.split()
    n_frames      = int(duration * fps)
    reveal_frames = min(int(1.2 * fps), max(n_frames // 3, int(0.5 * fps)))

    txt_size = 72 if is_short else 58
    txt_font = _font(txt_size, bold=True)
    lbl_size = 24

    # Layout — full width strip, left-anchored
    margin   = 28          # px from left/right edge
    pad_x    = 36
    pad_y    = 32
    label_h  = (lbl_size + 26) if label else 0
    max_tw   = width - margin * 2 - pad_x * 2
    lines    = _wrap(text, txt_font, max_tw)
    line_h   = txt_size + 16
    text_h   = len(lines) * line_h
    card_w   = width - margin * 2
    card_h   = pad_y * 2 + label_h + text_h + 8

    # Anchor: bottom of screen for shorts, vertical-centre for long
    if is_short:
        card_y = height - card_h - 40   # 40px from bottom edge
    else:
        card_y = height - card_h - 60
    card_x = margin   # LEFT-anchored, not centered

    frames = []
    for i in range(n_frames):
        # Ken Burns on background
        if bg_image:
            zoom = 1.0 + 0.05 * (i / n_frames)
            nw, nh = int(width * zoom), int(height * zoom)
            zx, zy = (nw - width) // 2, (nh - height) // 2
            zoomed = bg_image.resize((nw, nh), Image.BILINEAR)
            bg = zoomed.crop((zx, zy, zx + width, zy + height))
            # Light overlay on whole frame
            base = dark_overlay(bg, opacity=70)
            # Strong gradient darkening only the bottom strip (where card lives)
            base = gradient_overlay(base, top_opacity=0,
                                    bottom_opacity=200 if is_short else 170)
        else:
            base = Image.new("RGB", (width, height), (10, 8, 4))

        # Dark card (semi-transparent, left-anchored, full-width)
        base = _composite_card(base, card_x, card_y, card_w, card_h,
                               fill_rgba=(0, 0, 0, 185), radius=16)

        # Accent left border stripe on card
        ab = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        abd = ImageDraw.Draw(ab)
        abd.rounded_rectangle(
            [card_x, card_y, card_x + 6, card_y + card_h],
            radius=3, fill=(*accent_color, 255),
        )
        base = base.convert("RGBA")
        base.alpha_composite(ab)
        base = base.convert("RGB")

        draw = ImageDraw.Draw(base)

        # Label chip — top-left inside card
        if label:
            _draw_label_chip(draw, label, primary_color, (255, 255, 255),
                             card_x + pad_x, card_y + 12)

        # Word-by-word reveal
        n_rev = (len(words) if i >= reveal_frames
                 else max(1, int(len(words) * i / reveal_frames)))

        # Draw text — strictly left-aligned from card_x + pad_x
        ty = card_y + pad_y + label_h
        rev_left = n_rev
        for line in lines:
            lw  = line.split()
            n_d = min(len(lw), rev_left)
            rev_left -= n_d
            tx  = card_x + pad_x   # always restart from left edge per line

            drawn  = " ".join(lw[:n_d])
            undawn = " ".join(lw[n_d:])

            if drawn:
                # Shadow
                draw.text((tx + 2, ty + 2), drawn, font=txt_font, fill=(0, 0, 0))
                # Revealed: bright white
                draw.text((tx, ty), drawn, font=txt_font, fill=(255, 255, 255))
                dx = draw.textbbox((0, 0), drawn + " ", font=txt_font)
                tx += dx[2] - dx[0]

            if undawn:
                # Unrevealed: dim grey
                draw.text((tx, ty), undawn, font=txt_font, fill=(60, 60, 60))

            ty += line_h

        # Thin accent bar at very top and bottom of screen
        draw.rectangle([0, height - 4, width, height], fill=primary_color)
        draw.rectangle([0, 0, width, 4], fill=primary_color)

        frames.append(np.array(base))

    return frames


def _draw_label_chip(draw, text: str, bg_color: tuple, text_color: tuple,
                     x: int, y: int) -> None:
    font = _font(22, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    pw = bbox[2] - bbox[0] + 24
    ph = bbox[3] - bbox[1] + 12
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=bg_color)
    draw.text((x + 12, y + 6), text, font=font, fill=text_color)


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
    n_frames = int(duration * fps)
    l1_font  = _font(62, bold=True)
    l2_font  = _font(70, bold=True)
    h_font   = _font(82, bold=True)
    sub_font = _font(30, bold=False)

    frames = []
    for i in range(n_frames):
        pulse = 1.0 + 0.04 * math.sin(i * math.pi * 2 / fps)
        fade  = min(1.0, i / max(int(0.4 * fps), 1))

        if bg_image:
            # Slight zoom
            zoom = 1.0 + 0.03 * (i / n_frames)
            nw, nh = int(width * zoom), int(height * zoom)
            zx, zy = (nw - width) // 2, (nh - height) // 2
            zoomed = bg_image.resize((nw, nh), Image.BILINEAR)
            bg = zoomed.crop((zx, zy, zx + width, zy + height))
            base = dark_overlay(bg, 165)
        else:
            base = Image.new("RGB", (width, height), (8, 5, 2))

        draw = ImageDraw.Draw(base)
        draw.rectangle([0, 0, width, 4], fill=primary_color)
        draw.rectangle([0, height - 4, width, height], fill=primary_color)

        lm = 56   # left margin — matches slide layout
        y1 = int(height * 0.22)
        for text, font, color in [
            (cta_line1, l1_font, (int(255 * fade), int(255 * fade), int(255 * fade))),
            (cta_line2, l2_font, accent_color),
        ]:
            draw.text((lm + 2, y1 + 2), text, font=font, fill=(0, 0, 0))
            draw.text((lm, y1), text, font=font, fill=color)
            bbox = draw.textbbox((0, 0), text, font=font)
            y1 += (bbox[3] - bbox[1]) + 14

        # Pulsing handle — left-aligned
        h_size = int(82 * pulse)
        hfp = _font(h_size, bold=True)
        hy = height // 2 + 10
        draw.text((lm + 3, hy + 3), channel_handle, font=hfp, fill=(0, 0, 0))
        draw.text((lm, hy), channel_handle, font=hfp, fill=primary_color)

        draw.text((lm, hy + h_size + 18), cta_subtext, font=sub_font,
                  fill=(175, 175, 175))

        frames.append(np.array(base))

    return frames


# ── FFmpeg color grading ───────────────────────────────────────────────────────

def apply_cinematic_grade(input_path: str, output_path: str) -> bool:
    vf = (
        "curves=r='0/0 0.2/0.22 0.5/0.55 0.8/0.83 1/1':"
        "g='0/0 0.2/0.2 0.5/0.52 0.8/0.8 1/1':"
        "b='0/0 0.2/0.17 0.5/0.46 0.8/0.76 1/0.95',"
        "eq=contrast=1.07:brightness=0.015:saturation=1.10,"
        "vignette=PI/4"
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


# ── Frames → video ─────────────────────────────────────────────────────────────

def frames_to_video(frames: list[np.ndarray], output_path: str, fps: int) -> str:
    """Encode frames to H.264 via ffmpeg pipe, freeing each frame after write."""
    if not frames:
        return output_path
    h, w = frames[0].shape[:2]
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "rgb24",
        "-r", str(fps), "-i", "pipe:0",
        "-vcodec", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", output_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(len(frames)):
        proc.stdin.write(frames[i].tobytes())
        frames[i] = None  # allow GC to free the buffer immediately
    proc.stdin.close()
    proc.wait()
    return output_path


# ── xfade concat ──────────────────────────────────────────────────────────────

def xfade_concat(clip_paths: list[str], output_path: str,
                 transition: str = "fade", duration: float = 0.3) -> bool:
    if len(clip_paths) == 1:
        import shutil
        shutil.copy2(clip_paths[0], output_path)
        return True

    list_file = output_path + ".concat.txt"
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{Path(p).resolve()}'\n")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-an",
        output_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    Path(list_file).unlink(missing_ok=True)
    return r.returncode == 0
