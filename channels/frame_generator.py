"""
Generic frame generator — accepts cfg object instead of importing config.
Pollinations.ai backgrounds (free, no key needed).
"""
import hashlib
import io
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


def _palette(category: str, cfg) -> tuple:
    return cfg.CATEGORY_PALETTES.get(
        category, (cfg.BG_COLOR, cfg.BG_COLOR_2, cfg.PRIMARY_COLOR, cfg.ACCENT_COLOR)
    )


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
                return img.resize((width, height), Image.LANCZOS)
        except Exception as e:
            print(f"  Pollinations attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def _font(size: int, bold: bool, cfg) -> ImageFont.FreeTypeFont:
    paths = cfg.BOLD_FONT_PATHS if bold else cfg.REGULAR_FONT_PATHS
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


def _get_bg(category: str, topic_name: str, w: int, h: int, cfg) -> Image.Image:
    portrait = h > w
    prompt = cfg.bg_prompt(category, topic_name, portrait)
    seed = _seed(f"{category}:{topic_name}")
    bg = _fetch_bg(prompt, seed, w, h)
    if bg is None:
        bg1, bg2, _, _ = _palette(category, cfg)
        bg = _fallback_bg(w, h, bg1, bg2)
    return bg


# ── Short frames (portrait 1080×1920) ─────────────────────────────────────

def create_short_title_frame(topic_name: str, category: str, output_path: str, cfg) -> str:
    _, _, primary, accent = _palette(category, cfg)

    bg = _get_bg(category, topic_name, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg)
    img, draw = _dark_overlay(bg, opacity=155)

    draw.rectangle([0, 0, cfg.SHORT_WIDTH, 6], fill=primary)

    ch_font = _font(28, bold=True, cfg=cfg)
    draw.text((30, 22), cfg.CHANNEL_NAME.upper(), font=ch_font, fill=primary)

    cat_font = _font(26, bold=True, cfg=cfg)
    _pill(draw, 30, 64, category.upper(), cat_font, primary, (0, 0, 0))

    name_font_size = 80 if len(topic_name) < 12 else 60 if len(topic_name) < 18 else 48
    name_font = _font(name_font_size, bold=True, cfg=cfg)
    lines = _wrap(topic_name, name_font, cfg.SHORT_WIDTH - 80, draw)
    line_h = name_font_size + 16

    total_h = len(lines) * line_h
    center_y = cfg.SHORT_HEIGHT // 2 - 40
    _center_block(draw, lines, name_font, center_y, line_h, cfg.TEXT_COLOR, cfg.SHORT_WIDTH, shadow=True)

    bar_y = center_y + total_h // 2 + 20
    draw.rectangle([cfg.SHORT_WIDTH // 2 - 80, bar_y, cfg.SHORT_WIDTH // 2 + 80, bar_y + 4], fill=accent)

    handle_font = _font(42, bold=True, cfg=cfg)
    bbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=handle_font)
    x = (cfg.SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x + 2, cfg.SHORT_HEIGHT - 90), cfg.CHANNEL_HANDLE, font=handle_font, fill=(0, 0, 0))
    draw.text((x, cfg.SHORT_HEIGHT - 92), cfg.CHANNEL_HANDLE, font=handle_font, fill=accent)
    draw.rectangle([0, cfg.SHORT_HEIGHT - 6, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT], fill=primary)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_short_info_frame(label: str, text: str, category: str, topic_name: str, output_path: str, cfg) -> str:
    _, _, primary, accent = _palette(category, cfg)

    bg = _get_bg(category, f"{topic_name}_{label}", cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg)
    img, draw = _dark_overlay(bg, opacity=165)

    draw.rectangle([0, 0, cfg.SHORT_WIDTH, 6], fill=primary)

    lab_font = _font(22, bold=True, cfg=cfg)
    _pill(draw, 28, 24, label, lab_font, primary, (0, 0, 0))

    text_font = _font(54, bold=True, cfg=cfg)
    lines = _wrap(text, text_font, cfg.SHORT_WIDTH - 80, draw)
    _center_block(draw, lines, text_font, cfg.SHORT_HEIGHT // 2, 72, cfg.TEXT_COLOR, cfg.SHORT_WIDTH)

    handle_font = _font(40, bold=True, cfg=cfg)
    hbbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=handle_font)
    hx = (cfg.SHORT_WIDTH - (hbbox[2] - hbbox[0])) // 2
    draw.text((hx + 2, cfg.SHORT_HEIGHT - 88), cfg.CHANNEL_HANDLE, font=handle_font, fill=(0, 0, 0))
    draw.text((hx, cfg.SHORT_HEIGHT - 90), cfg.CHANNEL_HANDLE, font=handle_font, fill=accent)
    draw.rectangle([0, cfg.SHORT_HEIGHT - 6, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


def create_short_cta_frame(category: str, topic_name: str, output_path: str, cfg) -> str:
    _, _, primary, accent = _palette(category, cfg)

    bg = _get_bg(category, f"{topic_name}_cta", cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg)
    img, draw = _dark_overlay(bg, opacity=170)

    draw.rectangle([0, 0, cfg.SHORT_WIDTH, 6], fill=primary)
    draw.rectangle([0, cfg.SHORT_HEIGHT - 6, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT], fill=primary)

    cta1_font = _font(64, bold=True, cfg=cfg)
    for text, color, y in [
        (cfg.CTA_LINE1, cfg.TEXT_COLOR, cfg.SHORT_HEIGHT // 2 - 220),
        (cfg.CTA_LINE2, accent,         cfg.SHORT_HEIGHT // 2 - 140),
    ]:
        bbox = draw.textbbox((0, 0), text, font=cta1_font)
        x = (cfg.SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), text, font=cta1_font, fill=(0, 0, 0, 160))
        draw.text((x, y), text, font=cta1_font, fill=color)

    h_font = _font(72, bold=True, cfg=cfg)
    bbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=h_font)
    x = (cfg.SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x + 3, cfg.SHORT_HEIGHT // 2 + 15), cfg.CHANNEL_HANDLE, font=h_font, fill=(0, 0, 0, 160))
    draw.text((x, cfg.SHORT_HEIGHT // 2 + 12), cfg.CHANNEL_HANDLE, font=h_font, fill=primary)

    sub_font = _font(30, bold=False, cfg=cfg)
    sub = cfg.CTA_SUBTEXT
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    x = (cfg.SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, cfg.SHORT_HEIGHT // 2 + 130), sub, font=sub_font, fill=(180, 180, 180))

    img.save(output_path)
    return output_path


# ── Long-form frames (landscape 1920×1080) ────────────────────────────────

def create_long_intro_frame(title: str, category: str, output_path: str, cfg) -> str:
    _, _, primary, accent = _palette(category, cfg)

    bg = _get_bg(category, f"intro_{title}", cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg)
    img, draw = _dark_overlay(bg, opacity=160)

    draw.text((30, 25), cfg.CHANNEL_NAME.upper(), font=_font(28, bold=False, cfg=cfg), fill=primary)
    badge_font = _font(24, bold=True, cfg=cfg)
    _pill(draw, 30, 62, cfg.LONG_INTRO_BADGE, badge_font, primary, (0, 0, 0))

    title_font = _font(64, bold=True, cfg=cfg)
    lines = _wrap(title, title_font, cfg.LONG_WIDTH - 200, draw)
    _center_block(draw, lines, title_font, cfg.LONG_HEIGHT // 2, 82, cfg.TEXT_COLOR, cfg.LONG_WIDTH)

    handle_font = _font(32, bold=False, cfg=cfg)
    bbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=handle_font)
    draw.text(
        ((cfg.LONG_WIDTH - (bbox[2] - bbox[0])) // 2, cfg.LONG_HEIGHT - 56),
        cfg.CHANNEL_HANDLE, font=handle_font, fill=accent,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_long_section_frame(rank: int, section_name: str, key_points: list[str],
                               summary: str, category: str, output_path: str, cfg) -> str:
    _, _, primary, accent = _palette(category, cfg)

    bg = _get_bg(category, f"{section_name}_rank{rank}", cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg)
    img, draw = _dark_overlay(bg, opacity=165)

    # Ghost rank number
    rank_font = _font(220, bold=True, cfg=cfg)
    rank_str  = f"0{rank}" if rank < 10 else str(rank)
    draw.text((25, cfg.LONG_HEIGHT // 2 - 170), rank_str, font=rank_font, fill=(*primary[:3], 60))
    draw.text((3, cfg.LONG_HEIGHT // 2 - 170), rank_str, font=rank_font, fill=primary)

    name_font = _font(72, bold=True, cfg=cfg)
    draw.text((300, cfg.LONG_HEIGHT // 2 - 145), section_name, font=name_font, fill=cfg.TEXT_COLOR)
    draw.rectangle([300, cfg.LONG_HEIGHT // 2 - 32, cfg.LONG_WIDTH - 60, cfg.LONG_HEIGHT // 2 - 27], fill=accent)

    pt_font = _font(36, bold=False, cfg=cfg)
    y = cfg.LONG_HEIGHT // 2 - 10
    for pt in key_points[:3]:
        if pt:
            draw.text((300, y), f"  {pt}", font=pt_font, fill=cfg.TEXT_COLOR)
            y += 52

    verdict_font = _font(28, bold=False, cfg=cfg)
    draw.text((300, y + 14), summary[:100], font=verdict_font, fill=accent)
    draw.text((30, 25), cfg.CHANNEL_NAME.upper(), font=_font(24, bold=False, cfg=cfg), fill=primary)

    img.save(output_path)
    return output_path


def create_long_outro_frame(category: str, output_path: str, cfg) -> str:
    _, _, primary, accent = _palette(category, cfg)

    bg = _get_bg(category, "outro_subscribe", cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg)
    img, draw = _dark_overlay(bg, opacity=160)

    ty_font = _font(96, bold=True, cfg=cfg)
    for text, color, y in [
        (cfg.OUTRO_LINE1, primary,       cfg.LONG_HEIGHT // 2 - 162),
        (cfg.OUTRO_LINE2, cfg.TEXT_COLOR, cfg.LONG_HEIGHT // 2 - 30),
    ]:
        bbox = draw.textbbox((0, 0), text, font=ty_font)
        x = (cfg.LONG_WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x + 3, y + 3), text, font=ty_font, fill=(0, 0, 0, 160))
        draw.text((x, y), text, font=ty_font, fill=color)

    h_font = _font(42, bold=False, cfg=cfg)
    bbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=h_font)
    x = (cfg.LONG_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, cfg.LONG_HEIGHT // 2 + 58), cfg.CHANNEL_HANDLE, font=h_font, fill=accent)

    bell_font = _font(28, bold=False, cfg=cfg)
    bbox = draw.textbbox((0, 0), cfg.OUTRO_BELL_TEXT, font=bell_font)
    x = (cfg.LONG_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, cfg.LONG_HEIGHT // 2 + 128), cfg.OUTRO_BELL_TEXT, font=bell_font, fill=(160, 160, 160))

    img.save(output_path)
    return output_path


def create_thumbnail(title: str, category: str, output_path: str, cfg) -> str:
    _, _, primary, accent = _palette(category, cfg)

    tw, th = 1280, 720
    bg = _fetch_bg(cfg.bg_prompt(category, title, portrait=False), _seed(f"thumb:{title}"), tw, th)
    if bg is None:
        bg1, bg2, _, _ = _palette(category, cfg)
        bg = _fallback_bg(tw, th, bg1, bg2)

    img, draw = _dark_overlay(bg, opacity=150)

    draw.text((30, 20), cfg.CHANNEL_NAME.upper(), font=_font(32, bold=True, cfg=cfg), fill=primary)

    title_font = _font(68, bold=True, cfg=cfg)
    lines = _wrap(title, title_font, tw - 120, draw)
    _center_block(draw, lines, title_font, th // 2, 84, cfg.TEXT_COLOR, tw)

    draw.rectangle([0, th - 8, tw, th], fill=primary)
    draw.text((30, th - 56), cfg.CHANNEL_HANDLE, font=_font(34, bold=False, cfg=cfg), fill=accent)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path
