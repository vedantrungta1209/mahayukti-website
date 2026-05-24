from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import (
    SHORT_WIDTH, SHORT_HEIGHT, LONG_WIDTH, LONG_HEIGHT,
    BG_COLOR, BG_COLOR_2, PRIMARY_COLOR, ACCENT_COLOR,
    TEXT_COLOR, SUBTLE_COLOR, CARD_COLOR,
    CHANNEL_NAME, CHANNEL_HANDLE,
    BOLD_FONT_PATHS, REGULAR_FONT_PATHS,
)


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = BOLD_FONT_PATHS if bold else REGULAR_FONT_PATHS
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _gradient(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    for y in range(h):
        t = y / h
        r = int(BG_COLOR[0] + (BG_COLOR_2[0] - BG_COLOR[0]) * t)
        g = int(BG_COLOR[1] + (BG_COLOR_2[1] - BG_COLOR[1]) * t)
        b = int(BG_COLOR[2] + (BG_COLOR_2[2] - BG_COLOR[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _accents_short(draw: ImageDraw.ImageDraw) -> None:
    w, h = SHORT_WIDTH, SHORT_HEIGHT
    draw.rectangle([0, 0, 6, h], fill=PRIMARY_COLOR)
    draw.rectangle([0, h - 5, w, h], fill=PRIMARY_COLOR)
    # Cyan dot grid top-right
    for i in range(5):
        for j in range(8):
            x, y = w - 100 + i * 18, 40 + j * 18
            draw.ellipse([x, y, x + 5, y + 5], fill=ACCENT_COLOR)


def _accents_long(draw: ImageDraw.ImageDraw) -> None:
    w, h = LONG_WIDTH, LONG_HEIGHT
    draw.rectangle([0, 0, 6, h], fill=PRIMARY_COLOR)
    draw.rectangle([0, h - 5, w, h], fill=PRIMARY_COLOR)
    for i in range(6):
        for j in range(4):
            x, y = w - 120 + i * 18, 30 + j * 18
            draw.ellipse([x, y, x + 5, y + 5], fill=ACCENT_COLOR)


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
        draw.text((x, y), line, font=font, fill=color)
        y += line_h


# ── Short frames (1080 × 1920) ────────────────────────────────────────────

def _new_short() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (SHORT_WIDTH, SHORT_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    _gradient(draw, SHORT_WIDTH, SHORT_HEIGHT)
    _accents_short(draw)
    return img, draw


def _short_header(draw: ImageDraw.ImageDraw, label: str) -> None:
    draw.text((28, 28), CHANNEL_NAME.upper(), font=_font(22, bold=False), fill=PRIMARY_COLOR)
    badge_font = _font(20, bold=True)
    bbox = draw.textbbox((0, 0), label, font=badge_font)
    bw = bbox[2] - bbox[0] + 24
    draw.rectangle([28, 60, 28 + bw, 94], fill=PRIMARY_COLOR)
    draw.text((40, 66), label, font=badge_font, fill=(0, 0, 0))


def create_short_title_frame(tool_name: str, category: str, output_path: str) -> str:
    img, draw = _new_short()
    _short_header(draw, "AI TOOL OF THE DAY")

    # Category pill
    cat_font = _font(26, bold=False)
    draw.text((28, 110), category.upper(), font=cat_font, fill=ACCENT_COLOR)

    # Tool name — large, centered
    name_font = _font(86, bold=True)
    lines = _wrap(tool_name, name_font, SHORT_WIDTH - 80, draw)
    _center_block(draw, lines, name_font, SHORT_HEIGHT // 2 - 60, 106, TEXT_COLOR, SHORT_WIDTH)

    # Divider
    total_h = len(lines) * 106
    bar_y = SHORT_HEIGHT // 2 - 60 - total_h // 2 + total_h + 24
    draw.rectangle([SHORT_WIDTH // 2 - 60, bar_y, SHORT_WIDTH // 2 + 60, bar_y + 4], fill=ACCENT_COLOR)

    # Handle
    handle_font = _font(28, bold=False)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=handle_font)
    x = (SHORT_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, SHORT_HEIGHT - 70), CHANNEL_HANDLE, font=handle_font, fill=PRIMARY_COLOR)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_short_info_frame(label: str, text: str, output_path: str) -> str:
    img, draw = _new_short()
    _short_header(draw, label)

    # Main text centered
    text_font = _font(52, bold=True)
    lines = _wrap(text, text_font, SHORT_WIDTH - 80, draw)
    _center_block(draw, lines, text_font, SHORT_HEIGHT // 2, 68, TEXT_COLOR, SHORT_WIDTH)

    draw.text((28, SHORT_HEIGHT - 70), CHANNEL_HANDLE, font=_font(28, bold=False), fill=PRIMARY_COLOR)

    img.save(output_path)
    return output_path


def create_short_cta_frame(output_path: str) -> str:
    img, draw = _new_short()

    # "Follow for daily AI tools"
    cta1_font = _font(62, bold=True)
    cta1 = "Follow for"
    cta2 = "daily AI tools"
    bbox = draw.textbbox((0, 0), cta1, font=cta1_font)
    draw.text(((SHORT_WIDTH - (bbox[2] - bbox[0])) // 2, SHORT_HEIGHT // 2 - 200), cta1, font=cta1_font, fill=TEXT_COLOR)
    bbox = draw.textbbox((0, 0), cta2, font=cta1_font)
    draw.text(((SHORT_WIDTH - (bbox[2] - bbox[0])) // 2, SHORT_HEIGHT // 2 - 120), cta2, font=cta1_font, fill=ACCENT_COLOR)

    # Handle large
    h_font = _font(72, bold=True)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=h_font)
    draw.text(((SHORT_WIDTH - (bbox[2] - bbox[0])) // 2, SHORT_HEIGHT // 2 + 20), CHANNEL_HANDLE, font=h_font, fill=PRIMARY_COLOR)

    sub_font = _font(30, bold=False)
    sub = "New AI tool every day"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    draw.text(((SHORT_WIDTH - (bbox[2] - bbox[0])) // 2, SHORT_HEIGHT // 2 + 130), sub, font=sub_font, fill=SUBTLE_COLOR)

    img.save(output_path)
    return output_path


# ── Long-form frames (1920 × 1080) ───────────────────────────────────────

def _new_long() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (LONG_WIDTH, LONG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    _gradient(draw, LONG_WIDTH, LONG_HEIGHT)
    _accents_long(draw)
    return img, draw


def create_long_intro_frame(title: str, output_path: str) -> str:
    img, draw = _new_long()

    draw.text((30, 30), CHANNEL_NAME.upper(), font=_font(28, bold=False), fill=PRIMARY_COLOR)

    badge_font = _font(26, bold=True)
    draw.rectangle([30, 66, 340, 100], fill=PRIMARY_COLOR)
    draw.text((42, 72), "TOP 5 AI TOOLS THIS WEEK", font=badge_font, fill=(0, 0, 0))

    title_font = _font(68, bold=True)
    lines = _wrap(title, title_font, LONG_WIDTH - 200, draw)
    _center_block(draw, lines, title_font, LONG_HEIGHT // 2, 86, TEXT_COLOR, LONG_WIDTH)

    handle_font = _font(32, bold=False)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=handle_font)
    draw.text(((LONG_WIDTH - (bbox[2] - bbox[0])) // 2, LONG_HEIGHT - 60), CHANNEL_HANDLE, font=handle_font, fill=ACCENT_COLOR)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_long_tool_frame(rank: int, tool_name: str, key_points: list[str], india_verdict: str, output_path: str) -> str:
    img, draw = _new_long()

    # Large rank number (decorative)
    rank_font = _font(220, bold=True)
    draw.text((30, LONG_HEIGHT // 2 - 160), f"0{rank}" if rank < 10 else str(rank), font=rank_font, fill=PRIMARY_COLOR)

    # Tool name
    name_font = _font(72, bold=True)
    draw.text((320, LONG_HEIGHT // 2 - 140), tool_name, font=name_font, fill=TEXT_COLOR)

    # Divider
    draw.rectangle([320, LONG_HEIGHT // 2 - 30, LONG_WIDTH - 60, LONG_HEIGHT // 2 - 25], fill=ACCENT_COLOR)

    # Key points
    pt_font = _font(38, bold=False)
    y = LONG_HEIGHT // 2
    for pt in key_points[:3]:
        draw.text((320, y), f"  {pt}", font=pt_font, fill=TEXT_COLOR)
        y += 54

    # India verdict
    verdict_font = _font(30, bold=False)
    draw.text((320, y + 16), f"India: {india_verdict}", font=verdict_font, fill=ACCENT_COLOR)

    draw.text((30, 30), CHANNEL_NAME.upper(), font=_font(24, bold=False), fill=PRIMARY_COLOR)

    img.save(output_path)
    return output_path


def create_long_outro_frame(output_path: str) -> str:
    img, draw = _new_long()

    ty_font = _font(96, bold=True)
    ty = "Subscribe for more!"
    bbox = draw.textbbox((0, 0), ty, font=ty_font)
    draw.text(((LONG_WIDTH - (bbox[2] - bbox[0])) // 2, LONG_HEIGHT // 2 - 160), ty, font=ty_font, fill=PRIMARY_COLOR)

    sub_font = _font(48, bold=True)
    sub = "New AI tools every week"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    draw.text(((LONG_WIDTH - (bbox[2] - bbox[0])) // 2, LONG_HEIGHT // 2 - 30), sub, font=sub_font, fill=TEXT_COLOR)

    h_font = _font(42, bold=False)
    bbox = draw.textbbox((0, 0), CHANNEL_HANDLE, font=h_font)
    draw.text(((LONG_WIDTH - (bbox[2] - bbox[0])) // 2, LONG_HEIGHT // 2 + 60), CHANNEL_HANDLE, font=h_font, fill=ACCENT_COLOR)

    bell_font = _font(30, bold=False)
    bell = "Ring the notification bell — new video every Mon, Wed & Fri"
    bbox = draw.textbbox((0, 0), bell, font=bell_font)
    draw.text(((LONG_WIDTH - (bbox[2] - bbox[0])) // 2, LONG_HEIGHT // 2 + 130), bell, font=bell_font, fill=SUBTLE_COLOR)

    img.save(output_path)
    return output_path
