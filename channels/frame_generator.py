"""
Generic frame generator — accepts cfg object, used by all topic channels.
Design: Pollinations.ai background as hero, frosted glass cards for text,
thin edge gradients only — background stays vivid.
"""
import hashlib
import io
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


# ── Palette / background ──────────────────────────────────────────────────────

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


def _fallback_bg(w: int, h: int, bg1: tuple, bg2: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(bg1[0] + (bg2[0] - bg1[0]) * t)
        g = int(bg1[1] + (bg2[1] - bg1[1]) * t)
        b = int(bg1[2] + (bg2[2] - bg1[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _get_bg(category: str, topic_name: str, w: int, h: int, cfg) -> Image.Image:
    portrait = h > w
    prompt = cfg.bg_prompt(category, topic_name, portrait)
    seed = _seed(f"{category}:{topic_name}")
    bg = _fetch_bg(prompt, seed, w, h)
    if bg is None:
        bg1, bg2, _, _ = _palette(category, cfg)
        bg = _fallback_bg(w, h, bg1, bg2)
    return bg


# ── Overlay helpers ───────────────────────────────────────────────────────────

def _edge_gradients(img: Image.Image, color: tuple,
                    top_pct: float = 0.18, bot_pct: float = 0.28) -> Image.Image:
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
                  alpha: int = 165, radius: int = 28) -> Image.Image:
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


# ── Typography ────────────────────────────────────────────────────────────────

def _font(size: int, bold: bool, cfg) -> ImageFont.FreeTypeFont:
    paths = cfg.BOLD_FONT_PATHS if bold else cfg.REGULAR_FONT_PATHS
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


def _text_center(draw, text, font, cx, y, color, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = cx - (bbox[2] - bbox[0]) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=color)


def _block_center(draw, lines, font, center_y, line_h, color, canvas_w, shadow=True):
    total_h = (len(lines) - 1) * line_h
    y = center_y - total_h // 2
    for line in lines:
        _text_center(draw, line, font, canvas_w // 2, y, color, shadow)
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


# ── Short frames (portrait 1080×1920) ─────────────────────────────────────────

def create_short_title_frame(topic_name: str, category: str, output_path: str,
                              cfg, slide_idx: int = 0, total_slides: int = 5) -> str:
    bg1, _, primary, accent = _palette(category, cfg)

    img = _get_bg(category, topic_name, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg)
    img = _edge_gradients(img, bg1, top_pct=0.20, bot_pct=0.32)

    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, cfg.SHORT_WIDTH, 6], fill=primary)
    draw.text((44, 24), cfg.CHANNEL_NAME.upper(), font=_font(30, True, cfg), fill=(255, 255, 255))
    _pill(draw, 44, 70, f"  {category.upper()}  ", _font(26, True, cfg), primary, (0, 0, 0))

    # Frosted card
    pad = 48
    card_w = cfg.SHORT_WIDTH - 2 * pad
    card_h = int(cfg.SHORT_HEIGHT * 0.36)
    card_x = pad
    card_y = int(cfg.SHORT_HEIGHT * 0.32)

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=168, radius=28)
    draw = ImageDraw.Draw(img)

    # Channel badge inside card
    lbl_font = _font(30, True, cfg)
    lbbox = draw.textbbox((0, 0), cfg.LONG_INTRO_BADGE, font=lbl_font)
    lx = (cfg.SHORT_WIDTH - (lbbox[2] - lbbox[0])) // 2
    draw.text((lx, card_y + 26), cfg.LONG_INTRO_BADGE, font=lbl_font, fill=accent)
    rule_y = card_y + 74
    draw.rectangle([card_x + 44, rule_y, card_x + card_w - 44, rule_y + 4], fill=accent)

    # Topic name
    name_size = 72 if len(topic_name) <= 20 else 56 if len(topic_name) <= 32 else 44
    name_font = _font(name_size, True, cfg)
    lines = _wrap(topic_name, name_font, card_w - 56, draw)
    line_h = name_size + 12
    text_cy = rule_y + (card_h - 78) // 2 + 22
    _block_center(draw, lines, name_font, text_cy, line_h, (255, 255, 255), cfg.SHORT_WIDTH)

    # Bottom
    dots_y = int(cfg.SHORT_HEIGHT * 0.82)
    _progress_dots(draw, total_slides, slide_idx, cfg.SHORT_WIDTH // 2, dots_y, primary)

    hbbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=_font(46, True, cfg))
    hx = (cfg.SHORT_WIDTH - (hbbox[2] - hbbox[0])) // 2
    draw.text((hx + 2, cfg.SHORT_HEIGHT - 108), cfg.CHANNEL_HANDLE, font=_font(46, True, cfg), fill=(0, 0, 0))
    draw.text((hx, cfg.SHORT_HEIGHT - 110), cfg.CHANNEL_HANDLE, font=_font(46, True, cfg), fill=accent)
    draw.rectangle([0, cfg.SHORT_HEIGHT - 6, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT], fill=primary)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_short_info_frame(label: str, text: str, category: str, topic_name: str,
                             output_path: str, cfg,
                             slide_idx: int = 1, total_slides: int = 5) -> str:
    bg1, _, primary, accent = _palette(category, cfg)

    img = _get_bg(category, f"{topic_name}_{label}", cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg)
    img = _edge_gradients(img, bg1, top_pct=0.18, bot_pct=0.30)

    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, cfg.SHORT_WIDTH, 6], fill=primary)
    draw.text((44, 22), cfg.CHANNEL_NAME.upper(), font=_font(28, True, cfg), fill=(255, 255, 255))

    # Floating label pill above card
    pad = 48
    card_w = cfg.SHORT_WIDTH - 2 * pad
    card_h = int(cfg.SHORT_HEIGHT * 0.38)
    card_x = pad
    card_y = int(cfg.SHORT_HEIGHT * 0.30)

    _pill(draw, card_x, card_y - 58, f"  {label}  ", _font(30, True, cfg), primary, (0, 0, 0))

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=170, radius=28)
    draw = ImageDraw.Draw(img)

    text_font = _font(58, True, cfg)
    lines = _wrap(text, text_font, card_w - 56, draw)
    _block_center(draw, lines, text_font, card_y + card_h // 2, 72, (255, 255, 255), cfg.SHORT_WIDTH)

    dots_y = int(cfg.SHORT_HEIGHT * 0.82)
    _progress_dots(draw, total_slides, slide_idx, cfg.SHORT_WIDTH // 2, dots_y, primary)

    hbbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=_font(42, True, cfg))
    hx = (cfg.SHORT_WIDTH - (hbbox[2] - hbbox[0])) // 2
    draw.text((hx + 2, cfg.SHORT_HEIGHT - 102), cfg.CHANNEL_HANDLE, font=_font(42, True, cfg), fill=(0, 0, 0))
    draw.text((hx, cfg.SHORT_HEIGHT - 104), cfg.CHANNEL_HANDLE, font=_font(42, True, cfg), fill=accent)
    draw.rectangle([0, cfg.SHORT_HEIGHT - 6, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


def create_short_cta_frame(category: str, topic_name: str, output_path: str,
                            cfg, slide_idx: int = 4, total_slides: int = 5) -> str:
    bg1, _, primary, accent = _palette(category, cfg)

    img = _get_bg(category, f"{topic_name}_cta", cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT, cfg)
    img = _edge_gradients(img, bg1, top_pct=0.20, bot_pct=0.32)

    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, cfg.SHORT_WIDTH, 6], fill=primary)
    draw.text((44, 22), cfg.CHANNEL_NAME.upper(), font=_font(28, True, cfg), fill=(255, 255, 255))

    pad = 48
    card_w = cfg.SHORT_WIDTH - 2 * pad
    card_h = int(cfg.SHORT_HEIGHT * 0.44)
    card_x = pad
    card_y = int(cfg.SHORT_HEIGHT * 0.28)

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=170, radius=28)
    draw = ImageDraw.Draw(img)

    cy = card_y + 64
    _text_center(draw, cfg.CTA_LINE2.upper(), _font(88, True, cfg),
                 cfg.SHORT_WIDTH // 2, cy, accent, shadow=True)

    cy += 112
    draw.rectangle([card_x + 56, cy, card_x + card_w - 56, cy + 4], fill=primary)

    cy += 26
    _text_center(draw, cfg.CHANNEL_HANDLE, _font(92, True, cfg),
                 cfg.SHORT_WIDTH // 2, cy, (255, 255, 255), shadow=True)

    cy += 116
    _text_center(draw, cfg.CTA_SUBTEXT, _font(36, False, cfg),
                 cfg.SHORT_WIDTH // 2, cy, (210, 210, 210), shadow=True)

    dots_y = int(cfg.SHORT_HEIGHT * 0.83)
    _progress_dots(draw, total_slides, slide_idx, cfg.SHORT_WIDTH // 2, dots_y, primary)
    draw.rectangle([0, cfg.SHORT_HEIGHT - 6, cfg.SHORT_WIDTH, cfg.SHORT_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


# ── Long-form frames (landscape 1920×1080) ────────────────────────────────────

def create_long_intro_frame(title: str, category: str, output_path: str, cfg) -> str:
    bg1, _, primary, accent = _palette(category, cfg)

    img = _get_bg(category, f"intro_{title}", cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg)
    img = _edge_gradients(img, bg1, top_pct=0.22, bot_pct=0.30)

    card_x, card_w = 80, cfg.LONG_WIDTH - 160
    card_h = int(cfg.LONG_HEIGHT * 0.52)
    card_y = cfg.LONG_HEIGHT // 2 - card_h // 2

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=160, radius=20)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, cfg.LONG_WIDTH, 6], fill=primary)
    draw.text((32, 20), cfg.CHANNEL_NAME.upper(), font=_font(28, True, cfg), fill=(255, 255, 255))
    _pill(draw, 32, 58, f"  {cfg.LONG_INTRO_BADGE}  ", _font(22, True, cfg), primary, (0, 0, 0))

    title_font = _font(64, True, cfg)
    lines = _wrap(title, title_font, card_w - 80, draw)
    _block_center(draw, lines, title_font, cfg.LONG_HEIGHT // 2, 82, (255, 255, 255), cfg.LONG_WIDTH)

    hbbox = draw.textbbox((0, 0), cfg.CHANNEL_HANDLE, font=_font(32, False, cfg))
    draw.text(((cfg.LONG_WIDTH - (hbbox[2] - hbbox[0])) // 2, cfg.LONG_HEIGHT - 52),
              cfg.CHANNEL_HANDLE, font=_font(32, False, cfg), fill=accent)

    draw.rectangle([0, cfg.LONG_HEIGHT - 6, cfg.LONG_WIDTH, cfg.LONG_HEIGHT], fill=primary)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_long_section_frame(rank: int, section_name: str, key_points: list[str],
                               summary: str, category: str, output_path: str, cfg) -> str:
    bg1, _, primary, accent = _palette(category, cfg)

    img = _get_bg(category, f"{section_name}_rank{rank}", cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg)
    img = _edge_gradients(img, bg1, top_pct=0.22, bot_pct=0.32)

    # Ghost chapter number
    ghost_font = _font(260, True, cfg)
    rank_str = f"0{rank}" if rank < 10 else str(rank)
    ghost_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ghost_draw = ImageDraw.Draw(ghost_layer)
    ghost_draw.text((20, cfg.LONG_HEIGHT // 2 - 185), rank_str, font=ghost_font,
                    fill=(*primary, 40))
    img = img.convert("RGBA")
    img.alpha_composite(ghost_layer)
    img = img.convert("RGB")

    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, cfg.LONG_WIDTH, 6], fill=primary)
    draw.text((32, 18), cfg.CHANNEL_NAME.upper(), font=_font(24, True, cfg), fill=(255, 255, 255))

    content_x = 260
    card_w = cfg.LONG_WIDTH - content_x - 60
    card_h = int(cfg.LONG_HEIGHT * 0.62)
    card_y = cfg.LONG_HEIGHT // 2 - card_h // 2

    img = _frosted_card(img, content_x, card_y, card_w, card_h, alpha=158, radius=18)
    draw = ImageDraw.Draw(img)

    name_font = _font(72, True, cfg)
    draw.text((content_x + 28, card_y + 28), section_name, font=name_font, fill=(255, 255, 255))
    nbbox = draw.textbbox((0, 0), section_name, font=name_font)
    uw = min(nbbox[2] - nbbox[0] + 10, card_w - 56)
    draw.rectangle([content_x + 28, card_y + 112, content_x + 28 + uw, card_y + 116], fill=accent)

    pt_font = _font(38, False, cfg)
    y = card_y + 132
    for pt in key_points[:3]:
        if pt:
            draw.text((content_x + 36, y), f"›  {pt}", font=pt_font, fill=(240, 240, 240))
            y += 58

    if summary:
        draw.text((content_x + 36, y + 14), summary[:100],
                  font=_font(30, False, cfg), fill=accent)

    draw.rectangle([0, cfg.LONG_HEIGHT - 6, cfg.LONG_WIDTH, cfg.LONG_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


def create_long_outro_frame(category: str, output_path: str, cfg) -> str:
    bg1, _, primary, accent = _palette(category, cfg)

    img = _get_bg(category, "outro_subscribe", cfg.LONG_WIDTH, cfg.LONG_HEIGHT, cfg)
    img = _edge_gradients(img, bg1, top_pct=0.22, bot_pct=0.32)

    card_x, card_w = 100, cfg.LONG_WIDTH - 200
    card_h = int(cfg.LONG_HEIGHT * 0.54)
    card_y = cfg.LONG_HEIGHT // 2 - card_h // 2

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=160, radius=20)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, cfg.LONG_WIDTH, 6], fill=primary)

    cy = card_y + 52
    _text_center(draw, cfg.OUTRO_LINE1, _font(88, True, cfg), cfg.LONG_WIDTH // 2, cy, primary)
    cy += 108
    _text_center(draw, cfg.OUTRO_LINE2, _font(40, False, cfg),
                 cfg.LONG_WIDTH // 2, cy, (230, 230, 230), shadow=False)
    cy += 60
    draw.rectangle([card_x + 80, cy, card_x + card_w - 80, cy + 3], fill=accent)
    cy += 24
    _text_center(draw, cfg.CHANNEL_HANDLE, _font(46, True, cfg), cfg.LONG_WIDTH // 2, cy, accent)
    cy += 68
    _text_center(draw, cfg.OUTRO_BELL_TEXT, _font(28, False, cfg),
                 cfg.LONG_WIDTH // 2, cy, (160, 160, 160), shadow=False)

    draw.rectangle([0, cfg.LONG_HEIGHT - 6, cfg.LONG_WIDTH, cfg.LONG_HEIGHT], fill=primary)

    img.save(output_path)
    return output_path


def create_thumbnail(title: str, category: str, output_path: str, cfg) -> str:
    bg1, _, primary, accent = _palette(category, cfg)
    tw, th = 1280, 720

    bg = _fetch_bg(cfg.bg_prompt(category, title, portrait=False),
                   _seed(f"thumb:{title}"), tw, th)
    if bg is None:
        bg = _fallback_bg(tw, th, bg1, cfg.BG_COLOR_2)

    img = _edge_gradients(bg, bg1, top_pct=0.24, bot_pct=0.36)

    card_x, card_w = 60, tw - 120
    card_h = int(th * 0.52)
    card_y = th // 2 - card_h // 2 + 10

    img = _frosted_card(img, card_x, card_y, card_w, card_h, alpha=155, radius=18)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, tw, 6], fill=primary)
    draw.text((32, 18), cfg.CHANNEL_NAME.upper(), font=_font(30, True, cfg), fill=(255, 255, 255))

    title_font = _font(64, True, cfg)
    lines = _wrap(title, title_font, card_w - 60, draw)
    _block_center(draw, lines, title_font, th // 2 + 10, 78, (255, 255, 255), tw)

    draw.rectangle([0, th - 6, tw, th], fill=primary)
    draw.text((32, th - 46), cfg.CHANNEL_HANDLE, font=_font(30, False, cfg), fill=accent)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path
