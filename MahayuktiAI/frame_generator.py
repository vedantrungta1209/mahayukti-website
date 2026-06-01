"""
Frame generator — unique AI backgrounds via Pollinations.ai (free, no key).
Every video gets a distinct visual identity based on tool category.
Design principle: background is the hero. Text sits on frosted cards with
minimal overlay — Pollinations imagery should breathe through.
"""
import hashlib
import io
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from config import (
    SHORT_WIDTH, SHORT_HEIGHT, LONG_WIDTH, LONG_HEIGHT,
    TEXT_COLOR, SUBTLE_COLOR, CHANNEL_NAME, CHANNEL_HANDLE,
    BOLD_FONT_PATHS, REGULAR_FONT_PATHS, CATEGORY_PALETTES,
    BG_COLOR, BG_COLOR_2, PRIMARY_COLOR, ACCENT_COLOR,
)

_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


# ── Palette / background ──────────────────────────────────────────────────────

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
                return img.resize((width, height), Image.LANCZOS)
        except Exception as e:
            print(f"  Pollinations attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def _category_bg_prompt(category: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Productivity":     f"futuristic workspace holographic screens floating data neon blue purple {orientation} cinematic no text no people",
        "Writing":          f"glowing manuscript pages floating particles purple gold light {orientation} cinematic no text no people",
        "Image AI":         f"ai art gallery neon pink vibrant colors creative explosion {orientation} cinematic no text no people",
        "Video AI":         f"cinematic film frames floating orange golden light motion blur {orientation} no text no people",
        "Voice AI":         f"sound waves teal cyan blue neon glow frequency abstract {orientation} cinematic no text no people",
        "Music AI":         f"music notes floating purple magenta neon glow sound visualization {orientation} cinematic no text no people",
        "Coding AI":        f"matrix green code rain terminal emerald neon dark {orientation} cinematic no text no people",
        "Automation AI":    f"interconnected nodes gears electric blue automation blueprint {orientation} cinematic no text no people",
        "Presentation AI":  f"sleek boardroom holographic teal gold professional modern {orientation} cinematic no text no people",
        "Meeting AI":       f"futuristic conference room holographic avatars lime green dark {orientation} cinematic no text no people",
        "Research AI":      f"infinite library floating particles deep blue knowledge cosmos {orientation} cinematic no text no people",
        "Search":           f"search light beams data constellation blue cyan universe {orientation} cinematic no text no people",
        "Indian AI":        f"saffron golden indian geometric futuristic mandala orange {orientation} cinematic no text no people",
        "3D/Video AI":      f"neon wireframe objects floating purple cyan three dimensional {orientation} cinematic no text no people",
        "Chatbot AI":       f"chat bubbles neon blue purple ai neural network brain {orientation} cinematic no text no people",
        "AI Hub":           f"multiple nodes connected hub teal green ai central network {orientation} cinematic no text no people",
        "AI Platform":      f"cloud servers data center blue neon futuristic computing {orientation} cinematic no text no people",
        "Visual AI":        f"kaleidoscope colorful explosion pink rose gold digital art {orientation} cinematic no text no people",
        "Transcription AI": f"sound to text waveforms words floating green teal dark {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"futuristic ai neon abstract dark {orientation} cinematic no text no people")


def _fallback_bg(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _get_bg(category: str, seed_str: str, w: int, h: int) -> Image.Image:
    prompt = _category_bg_prompt(category, portrait=(h > w))
    bg = _fetch_bg(prompt, _seed(seed_str), w, h)
    if bg is None:
        bg1, bg2, _, _ = _palette(category)
        bg = _fallback_bg(w, h, bg1, bg2)
    return bg


# ── Overlay helpers ───────────────────────────────────────────────────────────

def _edge_gradients(img: Image.Image, color: tuple,
                    top_pct: float = 0.18, bot_pct: float = 0.28) -> Image.Image:
    """Thin dark gradients at top and bottom edges only — background stays vivid."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    top_h = int(h * top_pct)
    for y in range(top_h):
        a = int(210 * (1 - y / top_h) ** 1.6)
        draw.line([(0, y), (w, y)], fill=(*color, a))

    bot_h = int(h * bot_pct)
    for y in range(bot_h):
        a = int(230 * (y / bot_h) ** 1.4)
        draw.line([(0, h - bot_h + y), (w, h - bot_h + y)], fill=(*color, a))

    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def _frosted_card(img: Image.Image, x: int, y: int, w: int, h: int,
                  alpha: int = 160, radius: int = 28) -> Image.Image:
    """Frosted glass card: blur the bg region then overlay a dark tinted panel."""
    region = img.crop((x, y, x + w, y + h))
    blurred = region.filter(ImageFilter.GaussianBlur(radius=12))

    tint = Image.new("RGBA", (w, h), (0, 0, 0, alpha))
    blurred_rgba = blurred.convert("RGBA")
    blurred_rgba.alpha_composite(tint)
    result = blurred_rgba.convert("RGB")

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)

    out = img.copy()
    out.paste(result, (x, y), mask)
    return out


# ── Typography helpers ────────────────────────────────────────────────────────

def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = BOLD_FONT_PATHS if bold else REGULAR_FONT_PATHS
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int,
          draw: ImageDraw.ImageDraw) -> list[str]:
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


def _text_shadow(draw, x, y, text, font, color, shadow_offset=3, shadow_alpha=180):
    # Draw shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font,
              fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=color)


def _text_center(draw, text, font, cx, y, color, w, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = cx - (bbox[2] - bbox[0]) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=color)


def _block_center(draw, lines, font, center_y, line_h, color, canvas_w, shadow=True):
    total_h = (len(lines) - 1) * line_h
    y = center_y - total_h // 2
    for line in lines:
        _text_center(draw, line, font, canvas_w // 2, y, color, canvas_w, shadow)
        y += line_h


def _pill(draw, x, y, text, font, bg_color, text_color=(0, 0, 0)):
    bbox = draw.textbbox((0, 0), text, font=font)
    pw = bbox[2] - bbox[0] + 34
    ph = bbox[3] - bbox[1] + 16
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=bg_color)
    draw.text((x + 17, y + 8), text, font=font, fill=text_color)
    return pw, ph


def _progress_dots(draw, total, current, cx, y, primary):
    r, gap = 9, 24
    total_w = total * (2 * r) + (total - 1) * gap
    sx = cx - total_w // 2
    for i in range(total):
        color = primary if i == current else (60, 60, 60)
        x = sx + i * (2 * r + gap)
        draw.ellipse([x, y, x + 2 * r, y + 2 * r], fill=color)


# ── Short frames (1080 × 1920) ────────────────────────────────────────────────

def create_short_title_frame(tool_name: str, category: str, output_path: str,
                              slide_idx: int = 0, total_slides: int = 5) -> str:
    bg1, _, primary, accent = _palette(category)

    img = _get_bg(category, tool_name, SHORT_WIDTH, SHORT_HEIGHT)
    img = _edge_gradients(img, bg1, top_pct=0.20, bot_pct=0.32)
    draw = ImageDraw.Draw(img)

    # ── Top bar ──────────────────────────────────────────────────────────────
    draw.rectangle([0, 0, SHORT_WIDTH, 6], fill=primary)

    ch_font = _font(32, bold=True)
    draw.text((44, 24), CHANNEL_NAME.upper(), font=ch_font, fill=(255, 255, 255))

    cat_font = _font(26, bold=True)
    _pill(draw, 44, 72, f"  {category.upper()}  ", cat_font, primary, (0, 0, 0))

    # ── Center: frosted card with tool name ──────────────────────────────────
    card_pad = 48
    card_w   = SHORT_WIDTH - 2 * card_pad
    card_h   = int(SHORT_HEIGHT * 0.36)
    card_x   = card_pad
    card_y   = int(SHORT_HEIGHT * 0.32)

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=165, radius=28)
    draw = ImageDraw.Draw(img)

    # "AI TOOL OF THE DAY" — accent label at top of card
    lbl_font = _font(32, bold=True)
    lbl = "AI TOOL OF THE DAY"
    lbbox = draw.textbbox((0, 0), lbl, font=lbl_font)
    lx = (SHORT_WIDTH - (lbbox[2] - lbbox[0])) // 2
    draw.text((lx, card_y + 28), lbl, font=lbl_font, fill=accent)

    # Accent rule — thicker and more visible
    rule_y = card_y + 78
    draw.rectangle([card_x + 40, rule_y, card_x + card_w - 40, rule_y + 5], fill=accent)

    # Tool name — dominant, centered in lower 2/3 of card
    name_size = 108 if len(tool_name) <= 9 else 84 if len(tool_name) <= 15 else 64
    name_font = _font(name_size, bold=True)
    lines = _wrap(tool_name, name_font, card_w - 60, draw)
    line_h = name_size + 14
    text_cy = rule_y + (card_h - 70) // 2 + 20
    _block_center(draw, lines, name_font, text_cy, line_h, (255, 255, 255), SHORT_WIDTH)

    # ── Bottom zone ──────────────────────────────────────────────────────────
    dots_y = int(SHORT_HEIGHT * 0.82)
    _progress_dots(draw, total_slides, slide_idx, SHORT_WIDTH // 2, dots_y, primary)

    h_font = _font(48, bold=True)
    hbbox  = draw.textbbox((0, 0), CHANNEL_HANDLE, font=h_font)
    hx = (SHORT_WIDTH - (hbbox[2] - hbbox[0])) // 2
    draw.text((hx + 2, SHORT_HEIGHT - 108), CHANNEL_HANDLE, font=h_font, fill=(0, 0, 0))
    draw.text((hx, SHORT_HEIGHT - 110), CHANNEL_HANDLE, font=h_font, fill=accent)

    draw.rectangle([0, SHORT_HEIGHT - 6, SHORT_WIDTH, SHORT_HEIGHT], fill=primary)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_short_info_frame(label: str, text: str, category: str, tool_name: str,
                             output_path: str, slide_idx: int = 1,
                             total_slides: int = 5) -> str:
    bg1, _, primary, accent = _palette(category)

    img = _get_bg(category, f"{tool_name}_{label}", SHORT_WIDTH, SHORT_HEIGHT)
    img = _edge_gradients(img, bg1, top_pct=0.18, bot_pct=0.30)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SHORT_WIDTH, 6], fill=primary)
    ch_font = _font(30, bold=True)
    draw.text((44, 22), CHANNEL_NAME.upper(), font=ch_font, fill=(255, 255, 255))

    # ── Floating label badge (above card) ───────────────────────────────────
    card_pad = 48
    card_w   = SHORT_WIDTH - 2 * card_pad
    card_h   = int(SHORT_HEIGHT * 0.38)
    card_x   = card_pad
    card_y   = int(SHORT_HEIGHT * 0.30)

    lbl_font = _font(32, bold=True)
    lbl_w, lbl_h = _pill(draw, card_x, card_y - 58, f"  {label}  ", lbl_font, primary, (0, 0, 0))

    # ── Frosted card: text only ──────────────────────────────────────────────
    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=168, radius=28)
    draw = ImageDraw.Draw(img)

    text_font = _font(60, bold=True)
    lines = _wrap(text, text_font, card_w - 56, draw)
    line_h = 74
    text_cy = card_y + card_h // 2
    _block_center(draw, lines, text_font, text_cy, line_h, (255, 255, 255), SHORT_WIDTH)

    # ── Bottom ────────────────────────────────────────────────────────────────
    dots_y = int(SHORT_HEIGHT * 0.82)
    _progress_dots(draw, total_slides, slide_idx, SHORT_WIDTH // 2, dots_y, primary)

    h_font = _font(44, bold=True)
    hbbox  = draw.textbbox((0, 0), CHANNEL_HANDLE, font=h_font)
    hx = (SHORT_WIDTH - (hbbox[2] - hbbox[0])) // 2
    draw.text((hx + 2, SHORT_HEIGHT - 102), CHANNEL_HANDLE, font=h_font, fill=(0, 0, 0))
    draw.text((hx, SHORT_HEIGHT - 104), CHANNEL_HANDLE, font=h_font, fill=accent)

    draw.rectangle([0, SHORT_HEIGHT - 6, SHORT_WIDTH, SHORT_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


def create_short_cta_frame(category: str, tool_name: str, output_path: str,
                            slide_idx: int = 4, total_slides: int = 5) -> str:
    bg1, _, primary, accent = _palette(category)

    img = _get_bg(category, f"{tool_name}_cta", SHORT_WIDTH, SHORT_HEIGHT)
    img = _edge_gradients(img, bg1, top_pct=0.20, bot_pct=0.32)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, SHORT_WIDTH, 6], fill=primary)
    ch_font = _font(30, bold=True)
    draw.text((44, 22), CHANNEL_NAME.upper(), font=ch_font, fill=(255, 255, 255))

    # ── Frosted card ─────────────────────────────────────────────────────────
    card_pad = 48
    card_w   = SHORT_WIDTH - 2 * card_pad
    card_h   = int(SHORT_HEIGHT * 0.44)
    card_x   = card_pad
    card_y   = int(SHORT_HEIGHT * 0.28)

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=170, radius=28)
    draw = ImageDraw.Draw(img)

    # Stack: "Follow for" / "DAILY AI TOOLS" / rule / handle / sub
    cy = card_y + 64
    f2_font = _font(90, bold=True)
    _text_center(draw, "DAILY AI TOOLS", f2_font, SHORT_WIDTH // 2, cy, accent, SHORT_WIDTH, shadow=True)

    cy += 112
    draw.rectangle([card_x + 56, cy, card_x + card_w - 56, cy + 4], fill=primary)

    cy += 28
    h_font = _font(96, bold=True)
    _text_center(draw, CHANNEL_HANDLE, h_font, SHORT_WIDTH // 2, cy, (255, 255, 255), SHORT_WIDTH, shadow=True)

    cy += 116
    sub_font = _font(36, bold=False)
    _text_center(draw, "New AI tool every single day", sub_font,
                 SHORT_WIDTH // 2, cy, (210, 210, 210), SHORT_WIDTH, shadow=True)

    # ── Bottom ────────────────────────────────────────────────────────────────
    dots_y = int(SHORT_HEIGHT * 0.83)
    _progress_dots(draw, total_slides, slide_idx, SHORT_WIDTH // 2, dots_y, primary)

    draw.rectangle([0, SHORT_HEIGHT - 6, SHORT_WIDTH, SHORT_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


# ── Long-form frames (1920 × 1080) ───────────────────────────────────────────

def create_long_intro_frame(title: str, category: str, output_path: str) -> str:
    bg1, _, primary, accent = _palette(category)

    img = _get_bg(category, f"intro_{title}", LONG_WIDTH, LONG_HEIGHT)
    img = _edge_gradients(img, bg1, top_pct=0.22, bot_pct=0.30)

    card_x, card_w = 80, LONG_WIDTH - 160
    card_h = int(LONG_HEIGHT * 0.52)
    card_y = LONG_HEIGHT // 2 - card_h // 2

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=160, radius=20)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, LONG_WIDTH, 6], fill=primary)
    draw.text((32, 20), CHANNEL_NAME.upper(), font=_font(28, bold=True), fill=(255, 255, 255))
    _pill(draw, 32, 60, "  TOP 5 AI TOOLS THIS WEEK  ", _font(22, bold=True), primary, (0, 0, 0))

    title_font = _font(68, bold=True)
    lines = _wrap(title, title_font, card_w - 80, draw)
    _block_center(draw, lines, title_font, LONG_HEIGHT // 2, 84, (255, 255, 255), LONG_WIDTH)

    hbbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=_font(32, bold=False))
    draw.text(((LONG_WIDTH - (hbbox[2] - hbbox[0])) // 2, LONG_HEIGHT - 52),
              CHANNEL_HANDLE, font=_font(32, bold=False), fill=accent)

    draw.rectangle([0, LONG_HEIGHT - 6, LONG_WIDTH, LONG_HEIGHT], fill=primary)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_long_tool_frame(rank: int, tool_name: str, key_points: list[str],
                            india_verdict: str, category: str, output_path: str) -> str:
    bg1, _, primary, accent = _palette(category)

    img = _get_bg(category, f"{tool_name}_rank{rank}", LONG_WIDTH, LONG_HEIGHT)
    img = _edge_gradients(img, bg1, top_pct=0.22, bot_pct=0.32)

    rank_str = f"0{rank}" if rank < 10 else str(rank)

    # Ghost rank number (directly on bg before card)
    ghost_font = _font(260, bold=True)
    ghost_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ghost_draw = ImageDraw.Draw(ghost_layer)
    ghost_draw.text((20, LONG_HEIGHT // 2 - 185), rank_str, font=ghost_font,
                    fill=(*primary, 40))
    img = img.convert("RGBA")
    img.alpha_composite(ghost_layer)
    img = img.convert("RGB")

    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, LONG_WIDTH, 6], fill=primary)
    draw.text((32, 18), CHANNEL_NAME.upper(), font=_font(24, bold=True), fill=(255, 255, 255))

    # Content card on right side
    content_x = 260
    card_w = LONG_WIDTH - content_x - 60
    card_h = int(LONG_HEIGHT * 0.60)
    card_y = LONG_HEIGHT // 2 - card_h // 2

    img = _frosted_card(img, content_x, card_y, card_w, card_h, alpha=155, radius=18)
    draw = ImageDraw.Draw(img)

    # Tool name
    name_font = _font(72, bold=True)
    draw.text((content_x + 28, card_y + 28), tool_name, font=name_font, fill=(255, 255, 255))

    # Accent underline
    nbbox = draw.textbbox((0, 0), tool_name, font=name_font)
    uw = min(nbbox[2] - nbbox[0] + 10, card_w - 56)
    draw.rectangle([content_x + 28, card_y + 110, content_x + 28 + uw, card_y + 114], fill=accent)

    pt_font = _font(36, bold=False)
    y = card_y + 130
    for pt in key_points[:3]:
        if pt:
            draw.text((content_x + 36, y), f"›  {pt}", font=pt_font, fill=(240, 240, 240))
            y += 54

    draw.text((content_x + 36, y + 12),
              f"India: {india_verdict}", font=_font(28, bold=False), fill=accent)

    draw.rectangle([0, LONG_HEIGHT - 6, LONG_WIDTH, LONG_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


def create_long_outro_frame(category: str, output_path: str) -> str:
    bg1, _, primary, accent = _palette(category)

    img = _get_bg(category, "outro_subscribe", LONG_WIDTH, LONG_HEIGHT)
    img = _edge_gradients(img, bg1, top_pct=0.22, bot_pct=0.32)

    card_x, card_w = 100, LONG_WIDTH - 200
    card_h = int(LONG_HEIGHT * 0.54)
    card_y = LONG_HEIGHT // 2 - card_h // 2

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=160, radius=20)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, LONG_WIDTH, 6], fill=primary)

    cy = card_y + 56
    _text_center(draw, "Subscribe for more!", _font(88, bold=True),
                 LONG_WIDTH // 2, cy, primary, LONG_WIDTH)
    cy += 108
    _text_center(draw, "New AI tools every Mon, Wed & Fri", _font(38, bold=False),
                 LONG_WIDTH // 2, cy, (230, 230, 230), LONG_WIDTH, shadow=False)
    cy += 60
    draw.rectangle([card_x + 80, cy, card_x + card_w - 80, cy + 3], fill=accent)
    cy += 24
    _text_center(draw, CHANNEL_HANDLE, _font(48, bold=True),
                 LONG_WIDTH // 2, cy, accent, LONG_WIDTH)
    cy += 70
    _text_center(draw, "Ring the bell — never miss a drop", _font(28, bold=False),
                 LONG_WIDTH // 2, cy, (160, 160, 160), LONG_WIDTH, shadow=False)

    draw.rectangle([0, LONG_HEIGHT - 6, LONG_WIDTH, LONG_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


# ── Thumbnail (1280 × 720) ────────────────────────────────────────────────────

def create_thumbnail(title: str, category: str, output_path: str) -> str:
    bg1, _, primary, accent = _palette(category)
    tw, th = 1280, 720

    img = _get_bg(category, f"thumb:{title}", tw, th)
    img = _edge_gradients(img, bg1, top_pct=0.24, bot_pct=0.36)

    card_x, card_w = 60, tw - 120
    card_h = int(th * 0.52)
    card_y = th // 2 - card_h // 2 + 10

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=155, radius=18)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, tw, 6], fill=primary)
    draw.text((32, 18), CHANNEL_NAME.upper(), font=_font(30, bold=True), fill=(255, 255, 255))

    title_font = _font(64, bold=True)
    lines = _wrap(title, title_font, card_w - 60, draw)
    _block_center(draw, lines, title_font, th // 2 + 10, 78, (255, 255, 255), tw)

    draw.rectangle([0, th - 6, tw, th], fill=primary)
    draw.text((32, th - 46), CHANNEL_HANDLE, font=_font(30, bold=False), fill=accent)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path
