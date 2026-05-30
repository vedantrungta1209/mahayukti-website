"""
Mahayukti Finance — frame generator.
Unique Pollinations AI background per finance category, emerald/gold brand palette.
"""
import hashlib
import io
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont

from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT,
    PRIMARY_COLOR, ACCENT_COLOR, TEXT_COLOR, SUBTLE_COLOR,
    BOLD_FONT_PATHS, REGULAR_FONT_PATHS, CHANNEL_NAME, CHANNEL_HANDLE,
)

_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

# Per-category visual palettes: (bg_dark, bg_mid, primary, accent)
_CATEGORY_PALETTES = {
    "SIP aur Mutual Funds":       ((3, 15, 8),    (5, 30, 15),   (16, 185, 129),  (234, 179, 8)),
    "Stock Market Basics":        ((3, 10, 20),   (5, 20, 40),   (59, 130, 246),  (16, 185, 129)),
    "Tax Saving":                 ((20, 10, 3),   (40, 20, 5),   (249, 115, 22),  (234, 179, 8)),
    "Credit Cards aur Loans":     ((20, 5, 5),    (40, 10, 10),  (239, 68, 68),   (251, 146, 60)),
    "Emergency Fund aur Saving":  ((3, 18, 15),   (5, 35, 30),   (20, 184, 166),  (16, 185, 129)),
    "Insurance":                  ((5, 10, 25),   (10, 20, 50),  (99, 102, 241),  (167, 139, 250)),
    "Retirement Planning":        ((5, 15, 25),   (10, 30, 50),  (14, 165, 233),  (99, 102, 241)),
    "Real Estate":                ((15, 10, 5),   (30, 20, 10),  (161, 98, 7),    (234, 179, 8)),
    "Gold aur Alternatives":      ((20, 15, 3),   (40, 30, 5),   (234, 179, 8),   (251, 191, 36)),
    "Digital Payments aur Banking":((3, 12, 20),  (5, 24, 40),   (56, 189, 248),  (16, 185, 129)),
    "Passive Income":             ((3, 18, 8),    (5, 35, 15),   (132, 204, 22),  (20, 184, 166)),
    "Common Money Mistakes":      ((20, 5, 5),    (40, 10, 10),  (244, 63, 94),   (251, 146, 60)),
    "Startup aur Business Finance":((5, 15, 20),  (10, 30, 40),  (139, 92, 246),  (59, 130, 246)),
    "Personal Finance Psychology": ((8, 5, 20),   (15, 10, 40),  (192, 38, 211),  (244, 63, 94)),
    "India-Specific Finance":     ((20, 10, 3),   (40, 20, 5),   (249, 115, 22),  (251, 191, 36)),
}
_DEFAULT_PALETTE = ((3, 15, 8), (5, 30, 15), PRIMARY_COLOR, ACCENT_COLOR)

# Per-category Pollinations background prompts
_CATEGORY_PROMPTS = {
    "SIP aur Mutual Funds":       "growing investment chart emerald green wealth building financial growth abstract {o} no text no people",
    "Stock Market Basics":        "stock market candlestick chart blue neon trading terminal financial data {o} no text no people",
    "Tax Saving":                 "indian rupee symbol golden tax savings financial documents office {o} cinematic no text no people",
    "Credit Cards aur Loans":     "credit card floating neon red orange debt finance banking abstract {o} no text no people",
    "Emergency Fund aur Saving":  "piggy bank coins saving teal mint abstract financial security {o} cinematic no text no people",
    "Insurance":                  "protective shield umbrella blue purple insurance security abstract {o} cinematic no text no people",
    "Retirement Planning":        "sunset horizon golden hour retirement planning peaceful wealth {o} cinematic no text no people",
    "Real Estate":                "modern building architecture real estate india urban property {o} cinematic no text no people",
    "Gold aur Alternatives":      "gold bars coins glowing warm yellow precious metal investment {o} cinematic no text no people",
    "Digital Payments aur Banking":"upi digital payment phone india fintech abstract neon blue {o} no text no people",
    "Passive Income":             "money flowing streams passive income green abundance financial freedom {o} no text no people",
    "Common Money Mistakes":      "financial mistake warning red abstract danger money management {o} no text no people",
    "Startup aur Business Finance":"startup office india business meeting finance charts purple blue {o} cinematic no text no people",
    "Personal Finance Psychology":"brain neuron mind psychology money behavior abstract colorful {o} cinematic no text no people",
    "India-Specific Finance":     "india flag golden saffron green government finance schemes {o} cinematic no text no people",
}


def _palette(category: str) -> tuple:
    return _CATEGORY_PALETTES.get(category, _DEFAULT_PALETTE)


def _seed(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 1_000_000


def _fetch_bg(category: str, angle: str, w: int, h: int) -> Image.Image | None:
    orientation = "vertical portrait" if h > w else "horizontal landscape"
    template = _CATEGORY_PROMPTS.get(
        category,
        "financial wealth india abstract neon dark background {o} cinematic no text no people",
    )
    prompt = template.replace("{o}", orientation)
    seed = _seed(f"{category}:{angle}")
    encoded = quote(prompt)
    url = f"{_POLLINATIONS_BASE}/{encoded}?width={w}&height={h}&seed={seed}&nologo=true&model=flux"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=45)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                return img.resize((w, h), Image.LANCZOS)
        except Exception as e:
            print(f"  Pollinations attempt {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(3)
    return None


def _fallback_bg(w: int, h: int, bg1: tuple, bg2: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h), bg1)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(bg1[0] + (bg2[0] - bg1[0]) * t)
        g = int(bg1[1] + (bg2[1] - bg1[1]) * t)
        b = int(bg1[2] + (bg2[2] - bg1[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _dark_overlay(img: Image.Image, opacity: int = 150) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, opacity))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    result = base.convert("RGB")
    return result, ImageDraw.Draw(result)


def _get_bg(category: str, angle: str, w: int, h: int) -> Image.Image:
    img = _fetch_bg(category, angle, w, h)
    if img is None:
        bg1, bg2, _, _ = _palette(category)
        img = _fallback_bg(w, h, bg1, bg2)
    return img


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


def _center_block(draw, lines, font, center_y, line_h, color, width):
    total_h = len(lines) * line_h
    y = center_y - total_h // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=color)
        y += line_h


def _pill(draw, x, y, text, font, bg_color, text_color=(0, 0, 0)):
    bbox = draw.textbbox((0, 0), text, font=font)
    pw, ph = bbox[2] - bbox[0] + 28, bbox[3] - bbox[1] + 14
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=bg_color)
    draw.text((x + 14, y + 7), text, font=font, fill=text_color)
    return pw, ph


def create_title_frame(title: str, category: str, angle: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)
    bg = _get_bg(category, angle, VIDEO_WIDTH, VIDEO_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=155)

    # Top accent bar
    draw.rectangle([0, 0, VIDEO_WIDTH, 6], fill=primary)

    # Channel name + category pill
    draw.text((30, 22), CHANNEL_NAME.upper(), font=_font(28, bold=True), fill=primary)
    _pill(draw, 30, 64, category.upper(), _font(22, bold=True), primary, (0, 0, 0))

    # Main title centered
    title_font_size = 62 if len(title) < 40 else 50 if len(title) < 60 else 42
    title_font = _font(title_font_size, bold=True)
    lines = _wrap(title, title_font, VIDEO_WIDTH - 80, draw)
    _center_block(draw, lines, title_font, VIDEO_HEIGHT // 2 - 40, title_font_size + 14, TEXT_COLOR, VIDEO_WIDTH)

    # Accent bar under title
    total_h = len(lines) * (title_font_size + 14)
    bar_y = VIDEO_HEIGHT // 2 - 40 + total_h // 2 + 20
    draw.rectangle([VIDEO_WIDTH // 2 - 80, bar_y, VIDEO_WIDTH // 2 + 80, bar_y + 4], fill=accent)

    # Handle + tagline at bottom
    handle_font = _font(38, bold=True)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=handle_font)
    hx = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((hx + 2, VIDEO_HEIGHT - 95), CHANNEL_HANDLE, font=handle_font, fill=(0, 0, 0))
    draw.text((hx, VIDEO_HEIGHT - 97), CHANNEL_HANDLE, font=handle_font, fill=accent)

    draw.rectangle([0, VIDEO_HEIGHT - 6, VIDEO_WIDTH, VIDEO_HEIGHT], fill=primary)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_point_frame(number: int, point: str, category: str, angle: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)
    bg = _get_bg(category, f"{angle}_pt{number}", VIDEO_WIDTH, VIDEO_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=165)

    draw.rectangle([0, 0, VIDEO_WIDTH, 6], fill=primary)
    draw.text((30, 22), CHANNEL_NAME.upper(), font=_font(24, bold=True), fill=primary)

    # Large ghost number
    num_str = f"0{number}" if number < 10 else str(number)
    big_font = _font(200, bold=True)
    draw.text((20, VIDEO_HEIGHT // 2 - 180), num_str, font=big_font, fill=(primary[0], primary[1], primary[2]))

    draw.rectangle([30, VIDEO_HEIGHT // 2 + 50, VIDEO_WIDTH - 30, VIDEO_HEIGHT // 2 + 55], fill=accent)

    point_font = _font(48, bold=True)
    lines = _wrap(point, point_font, VIDEO_WIDTH - 80, draw)
    y = VIDEO_HEIGHT // 2 + 75
    for line in lines:
        draw.text((32 + 2, y + 2), line, font=point_font, fill=(0, 0, 0))
        draw.text((32, y), line, font=point_font, fill=TEXT_COLOR)
        y += 64

    draw.rectangle([0, VIDEO_HEIGHT - 6, VIDEO_WIDTH, VIDEO_HEIGHT], fill=primary)
    img.save(output_path)
    return output_path


def create_hook_frame(hook_text: str, category: str, angle: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)
    bg = _get_bg(category, f"{angle}_hook", VIDEO_WIDTH, VIDEO_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=160)

    draw.rectangle([0, 0, VIDEO_WIDTH, 6], fill=primary)
    draw.text((30, 22), CHANNEL_NAME.upper(), font=_font(28, bold=True), fill=primary)

    # "DID YOU KNOW?" badge
    badge_font = _font(24, bold=True)
    _pill(draw, 30, 64, "DID YOU KNOW?", badge_font, accent, (0, 0, 0))

    hook_font = _font(50, bold=True)
    lines = _wrap(hook_text, hook_font, VIDEO_WIDTH - 80, draw)
    _center_block(draw, lines, hook_font, VIDEO_HEIGHT // 2, 66, TEXT_COLOR, VIDEO_WIDTH)

    draw.rectangle([0, VIDEO_HEIGHT - 6, VIDEO_WIDTH, VIDEO_HEIGHT], fill=primary)
    img.save(output_path)
    return output_path


def create_outro_frame(category: str, angle: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)
    bg = _get_bg(category, f"{angle}_outro", VIDEO_WIDTH, VIDEO_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=165)

    draw.rectangle([0, 0, VIDEO_WIDTH, 6], fill=primary)
    draw.rectangle([0, VIDEO_HEIGHT - 6, VIDEO_WIDTH, VIDEO_HEIGHT], fill=primary)

    ty_font = _font(80, bold=True)
    ty = "Subscribe!"
    bbox = draw.textbbox((0, 0), ty, font=ty_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x + 2, VIDEO_HEIGHT // 2 - 172), ty, font=ty_font, fill=(0, 0, 0))
    draw.text((x, VIDEO_HEIGHT // 2 - 175), ty, font=ty_font, fill=primary)

    sub_font = _font(40, bold=True)
    sub = "Daily money tips — in Hinglish"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, VIDEO_HEIGHT // 2 - 60), sub, font=sub_font, fill=TEXT_COLOR)

    handle_font = _font(44, bold=True)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=handle_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x + 2, VIDEO_HEIGHT // 2 + 28), CHANNEL_HANDLE, font=handle_font, fill=(0, 0, 0))
    draw.text((x, VIDEO_HEIGHT // 2 + 25), CHANNEL_HANDLE, font=handle_font, fill=accent)

    bell_font = _font(28, bold=False)
    bell = "Notification bell ON karo — kal phir milenge!"
    bbox = draw.textbbox((0, 0), bell, font=bell_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, VIDEO_HEIGHT // 2 + 120), bell, font=bell_font, fill=(180, 180, 180))

    img.save(output_path)
    return output_path
