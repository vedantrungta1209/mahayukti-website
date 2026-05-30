"""
Mahayukti Finance — thumbnail generator.
Pollinations AI background per category, emerald/gold overlay.
"""
import hashlib
import io
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont

from config import CHANNEL_NAME, CHANNEL_HANDLE, BOLD_FONT_PATHS, REGULAR_FONT_PATHS
from frame_generator import _palette, _CATEGORY_PROMPTS, _seed

THUMB_W = 1280
THUMB_H = 720


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = BOLD_FONT_PATHS if bold else REGULAR_FONT_PATHS
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if draw.textbbox((0, 0), test, font=font)[2] > max_w and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _fetch_thumb_bg(category: str, title: str) -> Image.Image | None:
    template = _CATEGORY_PROMPTS.get(
        category,
        "financial wealth india abstract neon dark background horizontal landscape cinematic no text no people",
    )
    prompt = template.replace("{o}", "horizontal landscape widescreen")
    seed = _seed(f"thumb:{category}:{title}")
    encoded = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={THUMB_W}&height={THUMB_H}&seed={seed}&nologo=true&model=flux"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=45)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                return img.resize((THUMB_W, THUMB_H), Image.LANCZOS)
        except Exception as e:
            print(f"  Thumb Pollinations attempt {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(3)
    return None


def generate_thumbnail(title: str, thumb_text: str, output_path: str, category: str = "") -> str:
    _, _, primary, accent = _palette(category)

    # Background
    bg = _fetch_thumb_bg(category, title)
    if bg is None:
        bg = Image.new("RGB", (THUMB_W, THUMB_H), (13, 17, 23))
        draw_bg = ImageDraw.Draw(bg)
        for y in range(THUMB_H):
            t = y / THUMB_H
            draw_bg.line([(0, y), (THUMB_W, y)], fill=(
                int(13 + (35 - 13) * t), int(17 + (10 - 17) * t), int(23 + (60 - 23) * t)
            ))

    # Dark overlay
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 145))
    img = bg.convert("RGBA")
    img.alpha_composite(overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Accent bars
    draw.rectangle([0, 0, 8, THUMB_H], fill=primary)
    draw.rectangle([THUMB_W - 8, 0, THUMB_W, THUMB_H], fill=accent)
    draw.rectangle([0, THUMB_H - 6, THUMB_W, THUMB_H], fill=primary)

    # Large thumb text centered
    main_font = _font(108, bold=True)
    lines = _wrap(thumb_text, main_font, THUMB_W - 100, draw)
    line_h = 128
    total_h = len(lines) * line_h
    y = THUMB_H // 2 - total_h // 2 - 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=main_font)
        lw = bbox[2] - bbox[0]
        x = (THUMB_W - lw) // 2
        draw.text((x + 3, y + 3), line, font=main_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=main_font, fill=(255, 255, 255))
        y += line_h

    # Channel badge top-left
    badge_font = _font(28, bold=True)
    badge_text = "MAHAYUKTI FINANCE"
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw, bh = bbox[2] - bbox[0] + 28, bbox[3] - bbox[1] + 14
    draw.rounded_rectangle([22, 22, 22 + bw, 22 + bh], radius=bh // 2, fill=primary)
    draw.text((35, 29), badge_text, font=badge_font, fill=(0, 0, 0))

    # Handle bottom-left
    handle_font = _font(34, bold=False)
    draw.text((22, THUMB_H - 52), CHANNEL_HANDLE, font=handle_font, fill=accent)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95)
    print(f"  Thumbnail saved: {output_path}")
    return output_path
