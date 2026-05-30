"""
Frame generator — unique AI backgrounds via Pollinations.ai (free, no key).
Every video gets a distinct visual identity based on tool category.
"""
import hashlib
import io
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import (
    SHORT_WIDTH, SHORT_HEIGHT, LONG_WIDTH, LONG_HEIGHT,
    TEXT_COLOR, SUBTLE_COLOR, CHANNEL_NAME, CHANNEL_HANDLE,
    BOLD_FONT_PATHS, REGULAR_FONT_PATHS, CATEGORY_PALETTES,
    BG_COLOR, BG_COLOR_2, PRIMARY_COLOR, ACCENT_COLOR,
)

_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


def _palette(category: str) -> tuple:
    return CATEGORY_PALETTES.get(category, (BG_COLOR, BG_COLOR_2, PRIMARY_COLOR, ACCENT_COLOR))


def _seed(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 1_000_000


def _fetch_bg(prompt: str, seed: int, width: int, height: int, retries: int = 3) -> Image.Image | None:
    encoded = quote(prompt)
    url = f"{_POLLINATIONS_BASE}/{encoded}?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=45)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                if img.size == (width, height) or True:
                    return img.resize((width, height), Image.LANCZOS)
        except Exception as e:
            print(f"  Pollinations attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def _category_bg_prompt(category: str, tool_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Productivity":     f"futuristic workspace holographic screens floating data streams neon blue purple {orientation} cinematic no text no people",
        "Writing":          f"magical glowing manuscript pages floating text particles purple gold light {orientation} cinematic no text no people",
        "Image AI":         f"ai generated art gallery neon pink vibrant colors creative explosion digital art {orientation} cinematic no text no people",
        "Video AI":         f"cinematic film frames floating orange golden light motion blur futuristic {orientation} no text no people",
        "Voice AI":         f"sound waves visualization teal cyan blue neon glow abstract frequency {orientation} cinematic no text no people",
        "Music AI":         f"music notes floating purple magenta neon glow abstract sound visualization {orientation} cinematic no text no people",
        "Coding AI":        f"matrix green code rain terminal dark background emerald neon glow {orientation} cinematic no text no people",
        "Automation AI":    f"interconnected nodes gears automation blueprint electric blue dark {orientation} cinematic no text no people",
        "Presentation AI":  f"sleek modern boardroom holographic presentation teal gold professional {orientation} cinematic no text no people",
        "Meeting AI":       f"futuristic conference room holographic avatars green lime dark {orientation} cinematic no text no people",
        "Research AI":      f"infinite library books floating particles blue deep space knowledge {orientation} cinematic no text no people",
        "Search":           f"search light beams data universe constellation blue cyan {orientation} cinematic no text no people",
        "Indian AI":        f"saffron golden indian geometric patterns futuristic tech mandala orange {orientation} cinematic no text no people",
        "3D/Video AI":      f"three dimensional neon wireframe objects floating purple cyan {orientation} cinematic no text no people",
        "Chatbot AI":       f"chat bubbles floating neon blue purple ai brain neural network {orientation} cinematic no text no people",
        "AI Hub":           f"multiple ai logos floating central hub teal green nodes connected {orientation} cinematic no text no people",
        "AI Platform":      f"cloud computing data center blue neon servers futuristic {orientation} cinematic no text no people",
        "Visual AI":        f"colorful kaleidoscope visual explosion pink rose gold digital art {orientation} cinematic no text no people",
        "Transcription AI": f"sound to text waveforms words floating green teal dark background {orientation} cinematic no text no people",
    }
    base = prompts.get(category, f"futuristic ai technology abstract neon dark background {orientation} cinematic no text no people")
    return base


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


def _center_block(draw, lines, font, center_y, line_h, color, width, shadow=True):
    total_h = len(lines) * line_h
    y = center_y - total_h // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        if shadow:
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), line, font=font, fill=color)
        y += line_h


def _dark_overlay(img: Image.Image, opacity: int = 140) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, opacity))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    result = base.convert("RGB")
    draw = ImageDraw.Draw(result)
    return result, draw


def _gradient_overlay(img: Image.Image, color1: tuple, color2: tuple, opacity: int = 120) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    w, h = img.size
    for y in range(h):
        t = y / h
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        a = int(opacity * (0.3 + 0.7 * t))
        draw_ov.line([(0, y), (w, y)], fill=(r, g, b, a))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    result = base.convert("RGB")
    return result, ImageDraw.Draw(result)


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


def _pill(draw, x, y, text, font, bg_color, text_color=(0, 0, 0)):
    bbox = draw.textbbox((0, 0), text, font=font)
    pw, ph = bbox[2] - bbox[0] + 28, bbox[3] - bbox[1] + 14
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=bg_color)
    draw.text((x + 14, y + 7), text, font=font, fill=text_color)
    return pw, ph


def _get_bg(category: str, tool_name: str, w: int, h: int) -> Image.Image:
    portrait = h > w
    prompt = _category_bg_prompt(category, tool_name, portrait)
    seed = _seed(f"{category}:{tool_name}")
    bg = _fetch_bg(prompt, seed, w, h)
    if bg is None:
        bg1, bg2, _, _ = _palette(category)
        bg = _fallback_bg(w, h, bg1, bg2)
    return bg


# ── Short frames (1080 × 1920) ────────────────────────────────────────────

def create_short_title_frame(tool_name: str, category: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)

    bg = _get_bg(category, tool_name, SHORT_WIDTH, SHORT_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=155)

    # Top glow bar
    draw.rectangle([0, 0, SHORT_WIDTH, 6], fill=primary)

    # Channel name
    ch_font = _font(28, bold=True)
    draw.text((30, 22), CHANNEL_NAME.upper(), font=ch_font, fill=primary)

    # Category pill
    cat_font = _font(26, bold=True)
    _pill(draw, 30, 64, category.upper(), cat_font, primary, (0, 0, 0))

    # Tool name — large, centered with glow effect
    name_font_size = 80 if len(tool_name) < 12 else 60 if len(tool_name) < 18 else 48
    name_font = _font(name_font_size, bold=True)
    lines = _wrap(tool_name, name_font, SHORT_WIDTH - 80, draw)
    line_h = name_font_size + 16

    # Glow: draw blurred shadow behind text
    total_h = len(lines) * line_h
    center_y = SHORT_HEIGHT // 2 - 40
    _center_block(draw, lines, name_font, center_y, line_h, TEXT_COLOR, SHORT_WIDTH, shadow=True)

    # Accent divider
    bar_y = center_y + total_h // 2 + 20
    draw.rectangle([SHORT_WIDTH // 2 - 80, bar_y, SHORT_WIDTH // 2 + 80, bar_y + 4], fill=accent)

    # Handle at bottom — large and bright
    handle_font = _font(42, bold=True)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=handle_font)
    x = (SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x + 2, SHORT_HEIGHT - 90), CHANNEL_HANDLE, font=handle_font, fill=(0, 0, 0))
    draw.text((x, SHORT_HEIGHT - 92), CHANNEL_HANDLE, font=handle_font, fill=accent)
    draw.rectangle([0, SHORT_HEIGHT - 6, SHORT_WIDTH, SHORT_HEIGHT], fill=primary)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_short_info_frame(label: str, text: str, category: str, tool_name: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)

    bg = _get_bg(category, f"{tool_name}_{label}", SHORT_WIDTH, SHORT_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=165)

    draw.rectangle([0, 0, SHORT_WIDTH, 6], fill=primary)

    # Label pill top
    lab_font = _font(22, bold=True)
    _pill(draw, 28, 24, label, lab_font, primary, (0, 0, 0))

    # Main text
    text_font = _font(54, bold=True)
    lines = _wrap(text, text_font, SHORT_WIDTH - 80, draw)
    _center_block(draw, lines, text_font, SHORT_HEIGHT // 2, 72, TEXT_COLOR, SHORT_WIDTH)

    handle_font2 = _font(40, bold=True)
    hbbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=handle_font2)
    hx = (SHORT_WIDTH - (hbbox[2] - hbbox[0])) // 2
    draw.text((hx + 2, SHORT_HEIGHT - 88), CHANNEL_HANDLE, font=handle_font2, fill=(0, 0, 0))
    draw.text((hx, SHORT_HEIGHT - 90), CHANNEL_HANDLE, font=handle_font2, fill=accent)
    draw.rectangle([0, SHORT_HEIGHT - 6, SHORT_WIDTH, SHORT_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


def create_short_cta_frame(category: str, tool_name: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)

    bg = _get_bg(category, f"{tool_name}_cta", SHORT_WIDTH, SHORT_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=170)

    draw.rectangle([0, 0, SHORT_WIDTH, 6], fill=primary)
    draw.rectangle([0, SHORT_HEIGHT - 6, SHORT_WIDTH, SHORT_HEIGHT], fill=primary)

    cta1_font = _font(64, bold=True)
    cta1, cta2 = "Follow for", "daily AI tools"
    for text, color, y in [
        (cta1, TEXT_COLOR, SHORT_HEIGHT // 2 - 220),
        (cta2, accent,     SHORT_HEIGHT // 2 - 140),
    ]:
        bbox = draw.textbbox((0, 0), text, font=cta1_font)
        x = (SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), text, font=cta1_font, fill=(0, 0, 0, 160))
        draw.text((x, y), text, font=cta1_font, fill=color)

    h_font = _font(76, bold=True)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=h_font)
    x = (SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x + 3, SHORT_HEIGHT // 2 + 15), CHANNEL_HANDLE, font=h_font, fill=(0, 0, 0, 160))
    draw.text((x, SHORT_HEIGHT // 2 + 12), CHANNEL_HANDLE, font=h_font, fill=primary)

    sub_font = _font(32, bold=False)
    sub = "New AI tool every single day"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    x = (SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, SHORT_HEIGHT // 2 + 130), sub, font=sub_font, fill=(180, 180, 180))

    img.save(output_path)
    return output_path


# ── Long-form frames (1920 × 1080) ───────────────────────────────────────

def create_long_intro_frame(title: str, category: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)

    bg = _get_bg(category, f"intro_{title}", LONG_WIDTH, LONG_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=160)

    draw.text((30, 25), CHANNEL_NAME.upper(), font=_font(28, bold=False), fill=primary)
    badge_font = _font(24, bold=True)
    _pill(draw, 30, 62, "TOP 5 AI TOOLS THIS WEEK", badge_font, primary, (0, 0, 0))

    title_font = _font(64, bold=True)
    lines = _wrap(title, title_font, LONG_WIDTH - 200, draw)
    _center_block(draw, lines, title_font, LONG_HEIGHT // 2, 82, TEXT_COLOR, LONG_WIDTH)

    handle_font = _font(32, bold=False)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=handle_font)
    draw.text(((LONG_WIDTH - (bbox[2] - bbox[0])) // 2, LONG_HEIGHT - 56), CHANNEL_HANDLE, font=handle_font, fill=accent)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_long_tool_frame(rank: int, tool_name: str, key_points: list[str],
                            india_verdict: str, category: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)

    bg = _get_bg(category, f"{tool_name}_rank{rank}", LONG_WIDTH, LONG_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=165)

    # Large ghost rank number
    rank_font = _font(220, bold=True)
    rank_str = f"0{rank}" if rank < 10 else str(rank)
    draw.text((25, LONG_HEIGHT // 2 - 170), rank_str, font=rank_font, fill=(*primary[:3], 60) if True else primary)

    name_font = _font(72, bold=True)
    draw.text((3, LONG_HEIGHT // 2 - 170), rank_str, font=rank_font, fill=(primary[0], primary[1], primary[2]))
    # Tool name right of rank
    draw.text((300, LONG_HEIGHT // 2 - 145), tool_name, font=name_font, fill=TEXT_COLOR)

    draw.rectangle([300, LONG_HEIGHT // 2 - 32, LONG_WIDTH - 60, LONG_HEIGHT // 2 - 27], fill=accent)

    pt_font = _font(36, bold=False)
    y = LONG_HEIGHT // 2 - 10
    for pt in key_points[:3]:
        if pt:
            draw.text((300, y), f"  {pt}", font=pt_font, fill=TEXT_COLOR)
            y += 52

    verdict_font = _font(28, bold=False)
    draw.text((300, y + 14), f"India: {india_verdict}", font=verdict_font, fill=accent)
    draw.text((30, 25), CHANNEL_NAME.upper(), font=_font(24, bold=False), fill=primary)

    img.save(output_path)
    return output_path


def create_long_outro_frame(category: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)

    bg = _get_bg(category, "outro_subscribe", LONG_WIDTH, LONG_HEIGHT)
    img, draw = _dark_overlay(bg, opacity=160)

    ty_font = _font(96, bold=True)
    ty = "Subscribe for more!"
    bbox = draw.textbbox((0, 0), ty, font=ty_font)
    x = (LONG_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x + 3, LONG_HEIGHT // 2 - 162), ty, font=ty_font, fill=(0, 0, 0, 160))
    draw.text((x, LONG_HEIGHT // 2 - 165), ty, font=ty_font, fill=primary)

    sub_font = _font(48, bold=True)
    sub = "New AI tools every week"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    x = (LONG_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, LONG_HEIGHT // 2 - 30), sub, font=sub_font, fill=TEXT_COLOR)

    h_font = _font(42, bold=False)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=h_font)
    x = (LONG_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, LONG_HEIGHT // 2 + 58), CHANNEL_HANDLE, font=h_font, fill=accent)

    bell_font = _font(28, bold=False)
    bell = "Ring the bell  — new video every Mon, Wed & Fri"
    bbox = draw.textbbox((0, 0), bell, font=bell_font)
    x = (LONG_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, LONG_HEIGHT // 2 + 128), bell, font=bell_font, fill=(160, 160, 160))

    img.save(output_path)
    return output_path


# ── Thumbnail for long-form ────────────────────────────────────────────────

def create_thumbnail(title: str, category: str, output_path: str) -> str:
    _, _, primary, accent = _palette(category)

    # Thumbnail is 1280×720
    tw, th = 1280, 720
    prompt = _category_bg_prompt(category, title, portrait=False)
    seed = _seed(f"thumb:{title}")
    bg = _fetch_bg(prompt, seed, tw, th)
    if bg is None:
        bg1, bg2, _, _ = _palette(category)
        bg = _fallback_bg(tw, th, bg1, bg2)

    img, draw = _dark_overlay(bg, opacity=150)

    # Channel name top-left
    draw.text((30, 20), CHANNEL_NAME.upper(), font=_font(32, bold=True), fill=primary)

    # Big title centered
    title_font = _font(68, bold=True)
    lines = _wrap(title, title_font, tw - 120, draw)
    _center_block(draw, lines, title_font, th // 2, 84, TEXT_COLOR, tw)

    # Bottom bar
    draw.rectangle([0, th - 8, tw, th], fill=primary)
    draw.text((30, th - 56), CHANNEL_HANDLE, font=_font(34, bold=False), fill=accent)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path
