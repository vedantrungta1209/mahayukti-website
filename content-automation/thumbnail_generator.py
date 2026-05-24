from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import CHANNEL_NAME, CHANNEL_HANDLE, BOLD_FONT_PATHS, REGULAR_FONT_PATHS

THUMB_W = 1280
THUMB_H = 720


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = BOLD_FONT_PATHS if bold else REGULAR_FONT_PATHS
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > max_w and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def generate_thumbnail(title: str, thumb_text: str, output_path: str) -> str:
    img = Image.new("RGB", (THUMB_W, THUMB_H), (13, 17, 23))
    draw = ImageDraw.Draw(img)

    # Dark-to-purple gradient background
    for y in range(THUMB_H):
        t = y / THUMB_H
        r = int(13 + (35 - 13) * t)
        g = int(17 + (10 - 17) * t)
        b = int(23 + (60 - 23) * t)
        draw.line([(0, y), (THUMB_W, y)], fill=(r, g, b))

    # Left green bar + right gold bar (dual accent)
    draw.rectangle([0, 0, 10, THUMB_H], fill=(0, 211, 149))
    draw.rectangle([THUMB_W - 10, 0, THUMB_W, THUMB_H], fill=(255, 180, 0))

    # Large ghost "₹" in background for visual depth
    ghost_font = _get_font(500, bold=True)
    draw.text((THUMB_W - 350, THUMB_H // 2 - 280), "₹", font=ghost_font, fill=(0, 211, 149))
    # Blend by drawing a semi-transparent overlay rectangle
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (13, 17, 23, 180))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Main thumbnail text — large bold
    main_font = _get_font(110, bold=True)
    lines = _wrap(thumb_text, main_font, THUMB_W - 80, draw)
    line_h = 130
    total_h = len(lines) * line_h
    y = THUMB_H // 2 - total_h // 2 - 30

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=main_font)
        lw = bbox[2] - bbox[0]
        # Drop shadow
        draw.text((32 + (THUMB_W - 80 - lw) // 2 + 3, y + 3), line, font=main_font, fill=(0, 0, 0))
        # Main text
        draw.text((32 + (THUMB_W - 80 - lw) // 2, y), line, font=main_font, fill=(255, 255, 255))
        y += line_h

    # Gold-on-dark category badge top-left
    badge_font = _get_font(30, bold=True)
    badge_text = "MAHAYUKTI FINANCE"
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw = bbox[2] - bbox[0] + 32
    bh = bbox[3] - bbox[1] + 18
    draw.rectangle([26, 26, 26 + bw, 26 + bh], fill=(13, 17, 23))
    draw.text((42, 33), badge_text, font=badge_font, fill=(255, 180, 0))

    # Channel handle bottom-left
    handle_font = _get_font(36, bold=False)
    draw.text((26, THUMB_H - 58), CHANNEL_HANDLE, font=handle_font, fill=(0, 211, 149))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95)
    print(f"  Thumbnail saved: {output_path}")
    return output_path
