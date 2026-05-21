from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT,
    BG_COLOR, BG_COLOR_2, PRIMARY_COLOR, ACCENT_COLOR, TEXT_COLOR, SUBTLE_COLOR,
    BOLD_FONT_PATHS, REGULAR_FONT_PATHS, CHANNEL_NAME,
)


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = BOLD_FONT_PATHS if bold else REGULAR_FONT_PATHS
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _gradient_bg(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    for y in range(h):
        t = y / h
        r = int(BG_COLOR[0] + (BG_COLOR_2[0] - BG_COLOR[0]) * t)
        g = int(BG_COLOR[1] + (BG_COLOR_2[1] - BG_COLOR[1]) * t)
        b = int(BG_COLOR[2] + (BG_COLOR_2[2] - BG_COLOR[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _chrome_accents(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    # Left accent bar
    draw.rectangle([0, 0, 8, h], fill=PRIMARY_COLOR)
    # Bottom accent bar
    draw.rectangle([0, h - 6, w, h], fill=PRIMARY_COLOR)
    # Top-right decorative dot grid
    for i in range(6):
        for j in range(4):
            x, y = w - 120 + i * 20, 30 + j * 20
            draw.ellipse([x, y, x + 6, y + 6], fill=(PRIMARY_COLOR[0], PRIMARY_COLOR[1], PRIMARY_COLOR[2]))
    # Diagonal accent lines bottom-right
    for k in range(4):
        offset = k * 30
        draw.line([(w - 200 + offset, h), (w, h - 200 + offset)], fill=(255, 255, 255, 20), width=1)


def _channel_tag(draw: ImageDraw.ImageDraw, channel: str) -> None:
    font = _get_font(30, bold=False)
    draw.text((30, 30), channel.upper(), font=font, fill=PRIMARY_COLOR)


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


def _center_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    center_y: int,
    line_height: int,
    color: tuple,
) -> None:
    total_h = len(lines) * line_height
    y = center_y - total_h // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += line_height


def _new_frame() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    _gradient_bg(draw, VIDEO_WIDTH, VIDEO_HEIGHT)
    _chrome_accents(draw, VIDEO_WIDTH, VIDEO_HEIGHT)
    return img, draw


def create_title_frame(title: str, channel: str, output_path: str) -> str:
    img, draw = _new_frame()
    _channel_tag(draw, channel)

    # "PERSONAL FINANCE" label
    label_font = _get_font(34, bold=False)
    draw.text((30, 70), "PERSONAL FINANCE  |  HINDI", font=label_font, fill=SUBTLE_COLOR)

    # Main title
    title_font = _get_font(76, bold=True)
    lines = _wrap(title, title_font, VIDEO_WIDTH - 120, draw)
    _center_text_block(draw, lines, title_font, VIDEO_HEIGHT // 2 - 40, 96, TEXT_COLOR)

    # Divider under title
    total_h = len(lines) * 96
    bar_y = VIDEO_HEIGHT // 2 - 40 - total_h // 2 + total_h + 28
    draw.rectangle(
        [VIDEO_WIDTH // 2 - 90, bar_y, VIDEO_WIDTH // 2 + 90, bar_y + 5],
        fill=ACCENT_COLOR,
    )

    # Bottom subscribe line
    sub_font = _get_font(32, bold=False)
    sub = "Subscribe for daily money tips  |  Like & Share"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, VIDEO_HEIGHT - 70), sub, font=sub_font, fill=SUBTLE_COLOR)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def create_point_frame(number: int, point: str, channel: str, output_path: str) -> str:
    img, draw = _new_frame()
    _channel_tag(draw, channel)

    # Large background number (decorative)
    num_str = f"0{number}" if number < 10 else str(number)
    big_font = _get_font(260, bold=True)
    draw.text((30, VIDEO_HEIGHT // 2 - 200), num_str, font=big_font, fill=PRIMARY_COLOR)

    # Horizontal accent line separating number from text
    draw.rectangle([30, VIDEO_HEIGHT // 2 + 80, VIDEO_WIDTH - 30, VIDEO_HEIGHT // 2 + 85], fill=ACCENT_COLOR)

    # Point text below the line
    point_font = _get_font(62, bold=True)
    lines = _wrap(point, point_font, VIDEO_WIDTH - 100, draw)
    y = VIDEO_HEIGHT // 2 + 110
    for line in lines:
        draw.text((40, y), line, font=point_font, fill=TEXT_COLOR)
        y += 80

    img.save(output_path)
    return output_path


def create_hook_frame(hook_text: str, channel: str, output_path: str) -> str:
    img, draw = _new_frame()
    _channel_tag(draw, channel)

    # "DID YOU KNOW?" badge
    badge_font = _get_font(28, bold=True)
    draw.rectangle([30, 70, 240, 108], fill=ACCENT_COLOR)
    draw.text((44, 78), "DID YOU KNOW?", font=badge_font, fill=TEXT_COLOR)

    # Hook text centered
    hook_font = _get_font(58, bold=True)
    lines = _wrap(hook_text, hook_font, VIDEO_WIDTH - 120, draw)
    _center_text_block(draw, lines, hook_font, VIDEO_HEIGHT // 2, 76, TEXT_COLOR)

    img.save(output_path)
    return output_path


def create_outro_frame(channel: str, output_path: str) -> str:
    img, draw = _new_frame()

    # "Thank You!" large
    ty_font = _get_font(100, bold=True)
    ty = "Thank You!"
    bbox = draw.textbbox((0, 0), ty, font=ty_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, VIDEO_HEIGHT // 2 - 180), ty, font=ty_font, fill=PRIMARY_COLOR)

    # Subscribe line
    sub_font = _get_font(52, bold=True)
    sub = "Subscribe for daily finance tips"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, VIDEO_HEIGHT // 2 - 40), sub, font=sub_font, fill=TEXT_COLOR)

    # Channel handle
    handle_font = _get_font(46, bold=False)
    handle = f"@{channel.lower().replace(' ', '')}"
    bbox = draw.textbbox((0, 0), handle, font=handle_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, VIDEO_HEIGHT // 2 + 50), handle, font=handle_font, fill=ACCENT_COLOR)

    # Bell reminder
    bell_font = _get_font(36, bold=False)
    bell = "Notification bell ON karo — kal phir milenge!"
    bbox = draw.textbbox((0, 0), bell, font=bell_font)
    x = (VIDEO_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, VIDEO_HEIGHT // 2 + 130), bell, font=bell_font, fill=SUBTLE_COLOR)

    img.save(output_path)
    return output_path
