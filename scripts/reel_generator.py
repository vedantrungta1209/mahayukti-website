"""
MahaYukti Advisory — reel generator.
Unique Pollinations AI background per domain, overlaid with brand navy/gold treatment.
Output: 1080×1920 MP4 for Instagram Reels / Facebook Reels / YouTube Shorts
"""
import asyncio
import base64
import hashlib
import io
import os
import shutil
import subprocess
import tempfile
import time
from urllib.parse import quote

import numpy as np
import requests
import edge_tts

import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

try:
    from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
except ImportError:
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

from PIL import Image, ImageDraw, ImageFont

# ── Brand constants ────────────────────────────────────────────────────────
NAVY  = (11,  27,  58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (6,   15,  35)

REEL_W, REEL_H = 1080, 1920

# Domain-specific accent colors (used as pill + highlight, inside the navy brand)
_DOMAIN_ACCENTS = {
    "Legal & Judiciary":         (212, 175, 55),   # deep gold
    "Finance & Banking":         (16,  185, 129),  # emerald
    "Technology":                (56,  189, 248),  # sky blue
    "Cybersecurity":             (239, 68,  68),   # red alert
    "Medicine & Healthcare":     (52,  211, 153),  # mint green
    "Intelligence & Research":   (148, 163, 184),  # silver
    "Crisis Management":         (251, 146, 60),   # orange
    # Member domains
    "Senior Lawyers & Advocates":         (212, 175, 55),
    "Finance & Banking Professionals":    (16,  185, 129),
    "Technology Leaders":                 (56,  189, 248),
    "Cybersecurity Experts":              (239, 68,  68),
    "Medical & Healthcare Professionals": (52,  211, 153),
    "Intelligence & Research Professionals": (148, 163, 184),
}

# Domain-specific Pollinations background prompts — professional, cinematic
_DOMAIN_PROMPTS = {
    "Legal & Judiciary":         "supreme court india law books scales justice dark dramatic vertical no text no people",
    "Finance & Banking":         "india stock exchange financial charts trading floor dark dramatic vertical no text no people",
    "Technology":                "server room data center blue neon india tech futuristic dark vertical no text no people",
    "Cybersecurity":             "cyber security dark matrix red neon threat intelligence india vertical no text no people",
    "Medicine & Healthcare":     "modern hospital india medical laboratory healthcare dark teal vertical no text no people",
    "Intelligence & Research":   "intelligence analysis dark room india map geopolitical dramatic vertical no text no people",
    "Crisis Management":         "crisis management india corporate boardroom dramatic tension dark vertical no text no people",
    "Senior Lawyers & Advocates": "supreme court advocate india law dark gold dramatic vertical no text no people",
    "Finance & Banking Professionals": "chartered accountant office india finance emerald dark vertical no text no people",
    "Technology Leaders":        "cto tech leader india digital transformation dark blue vertical no text no people",
    "Cybersecurity Experts":     "ciso security expert india dark cyber operations vertical no text no people",
    "Medical & Healthcare Professionals": "senior doctor specialist india hospital dark mint vertical no text no people",
    "Intelligence & Research Professionals": "intelligence analyst india research dark silver dramatic vertical no text no people",
}

_FONT_PATHS_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",       # macOS
    "/System/Library/Fonts/Arial Bold.ttf",
]
_FONT_PATHS_REG = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",       # macOS
    "/System/Library/Fonts/Arial.ttf",
]
_AMBIENT_PRESETS = [
    (110.0, 146.8, 220.0, 55),
    (130.8, 174.6, 261.6, 60),
    (98.0,  130.8, 196.0, 58),
    (146.8, 220.0, 293.7, 62),
    (123.5, 185.0, 246.9, 57),
]


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = _FONT_PATHS_BOLD if bold else _FONT_PATHS_REG
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _seed(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 1_000_000


def _accent(domain: str) -> tuple:
    return _DOMAIN_ACCENTS.get(domain, GOLD)


def _fetch_bg(domain: str, post_id: str) -> Image.Image | None:
    prompt = _DOMAIN_PROMPTS.get(
        domain,
        "professional india advisory network dark dramatic cinematic vertical no text no people",
    )
    seed = _seed(f"{domain}:{post_id}")
    encoded = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={REEL_W}&height={REEL_H}&seed={seed}&nologo=true&model=flux"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=50)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                return img.resize((REEL_W, REEL_H), Image.LANCZOS)
        except Exception as e:
            print(f"  Pollinations attempt {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(3)
    return None


def _navy_overlay(img: Image.Image, opacity: int = 130) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Deep navy gradient overlay preserving the AI background underneath."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    w, h = img.size
    for y in range(h):
        t = y / h
        # Strong navy at bottom, lighter at top
        alpha = int(100 + 100 * t)
        r = int(NAVY[0] * (0.4 + 0.6 * t))
        g = int(NAVY[1] * (0.4 + 0.6 * t))
        b = int(NAVY[2] * (0.4 + 0.6 * t))
        draw_ov.line([(0, y), (w, y)], fill=(r, g, b, alpha))
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    result = base.convert("RGB")
    return result, ImageDraw.Draw(result)


def _wrap(text: str, font, max_w: int, draw) -> list[str]:
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


def _pill(draw, x, y, text, font, bg_color, text_color=(0, 0, 0)):
    bbox = draw.textbbox((0, 0), text, font=font)
    pw, ph = bbox[2] - bbox[0] + 28, bbox[3] - bbox[1] + 14
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=bg_color)
    draw.text((x + 14, y + 7), text, font=font, fill=text_color)
    return pw, ph


def _brand_header(draw, accent_color):
    """Compact brand header — logo left, domain tag right."""
    # Top gold bar
    draw.rectangle([(0, 0), (REEL_W, 5)], fill=GOLD)
    # Header area
    draw.rectangle([(0, 5), (REEL_W, 120)], fill=DARK)
    draw.rectangle([(0, 118), (REEL_W, 122)], fill=accent_color)
    # Brand name
    draw.text((40, 18), "MAHAYUKTI", fill=GOLD, font=_font(60, bold=True))
    draw.text((40, 82), "India's Expert Advisory Network", fill=LIGHT, font=_font(24, bold=False))


def _brand_footer(draw):
    """Footer with CTA and handle."""
    draw.rectangle([(0, REEL_H - 145), (REEL_W, REEL_H - 5)], fill=DARK)
    draw.rectangle([(0, REEL_H - 147), (REEL_W, REEL_H - 143)], fill=GOLD)
    draw.rectangle([(0, REEL_H - 5), (REEL_W, REEL_H)], fill=GOLD)
    cta_font = _font(48, bold=True)
    bbox = draw.textbbox((0, 0), "mahayukti.com", font=cta_font)
    draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, REEL_H - 128), "mahayukti.com", fill=GOLD, font=cta_font)
    h_font = _font(30, bold=False)
    bbox = draw.textbbox((0, 0), "@WeAreMahayukti", font=h_font)
    draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, REEL_H - 68), "@WeAreMahayukti", fill=LIGHT, font=h_font)


def _content_zone() -> tuple[int, int]:
    """Returns (top_y, bottom_y) of usable content area between header and footer."""
    return 140, REEL_H - 160


# ── Slide builders ─────────────────────────────────────────────────────────

def _make_hook_slide(headline: str, domain: str, bg: Image.Image) -> np.ndarray:
    img, draw = _navy_overlay(bg.copy())
    accent = _accent(domain)
    _brand_header(draw, accent)
    _brand_footer(draw)

    # Domain pill
    _pill(draw, 40, 136, domain.upper(), _font(22, bold=True), accent, (0, 0, 0))

    top, bot = 200, REEL_H - 180
    zone_mid = (top + bot) // 2

    h_font = _font(90, bold=True)
    lines = _wrap(headline, h_font, REEL_W - 80, draw)[:4]
    line_h = 108
    total_h = len(lines) * line_h
    y = zone_mid - total_h // 2

    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=h_font)
        x = (REEL_W - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), ln, font=h_font, fill=(0, 0, 0))
        draw.text((x, y), ln, font=h_font, fill=WHITE)
        y += line_h

    return np.array(img)


def _make_body_slide(headline: str, body: str, domain: str, bg: Image.Image) -> np.ndarray:
    img, draw = _navy_overlay(bg.copy())
    accent = _accent(domain)
    _brand_header(draw, accent)
    _brand_footer(draw)

    top, bot = 140, REEL_H - 160
    zone_mid = (top + bot) // 2

    h_font = _font(68, bold=True)
    b_font = _font(44, bold=False)

    h_lines = _wrap(headline, h_font, REEL_W - 80, draw)[:3]
    b_lines = _wrap(body, b_font, REEL_W - 80, draw)[:5]
    line_h, gap, b_line_h = 84, 32, 56

    total_h = len(h_lines) * line_h + (gap + len(b_lines) * b_line_h if b_lines else 0)
    y = zone_mid - total_h // 2

    for ln in h_lines:
        bbox = draw.textbbox((0, 0), ln, font=h_font)
        x = (REEL_W - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), ln, font=h_font, fill=(0, 0, 0))
        draw.text((x, y), ln, font=h_font, fill=WHITE)
        y += line_h

    if b_lines:
        draw.rectangle([(REEL_W // 2 - 80, y + 8), (REEL_W // 2 + 80, y + 13)], fill=accent)
        y += gap
        for ln in b_lines:
            bbox = draw.textbbox((0, 0), ln, font=b_font)
            x = (REEL_W - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), ln, font=b_font, fill=LIGHT)
            y += b_line_h

    return np.array(img)


def _make_steps_slide(title: str, steps: list[str], domain: str, bg: Image.Image) -> np.ndarray:
    img, draw = _navy_overlay(bg.copy())
    accent = _accent(domain)
    _brand_header(draw, accent)
    _brand_footer(draw)

    t_font = _font(52, bold=True)
    s_font = _font(42, bold=False)
    n_font = _font(72, bold=True)

    bbox = draw.textbbox((0, 0), title.upper(), font=t_font)
    draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, 165), title.upper(), fill=accent, font=t_font)
    draw.rectangle([(REEL_W // 2 - 80, 230), (REEL_W // 2 + 80, 235)], fill=accent)

    y = 268
    for i, step in enumerate(steps[:3], 1):
        draw.ellipse([(44, y), (128, y + 84)], fill=accent)
        n_bbox = draw.textbbox((0, 0), str(i), font=n_font)
        draw.text((86 - (n_bbox[2] - n_bbox[0]) // 2, y + 4), str(i), fill=DARK, font=n_font)
        step_y = y + 12
        for line in _wrap(step, s_font, REEL_W - 170, draw)[:2]:
            draw.text((154, step_y), line, font=s_font, fill=WHITE)
            step_y += 52
        y += 190

    return np.array(img)


def _make_cta_slide(post_type: str, domain: str, bg: Image.Image) -> np.ndarray:
    img, draw = _navy_overlay(bg.copy(), opacity=155)
    accent = _accent(domain)
    _brand_header(draw, accent)
    _brand_footer(draw)

    top, bot = 140, REEL_H - 160
    zone_mid = (top + bot) // 2

    if post_type == "morning":
        line1, line2 = "HAVE A COMPLEX", "PROBLEM?"
        sub1 = "Describe it at mahayukti.com"
        sub2 = "Get matched to the exact expert."
        cta  = "Sign up FREE →"
    else:
        line1, line2 = "YOUR EXPERTISE", "HAS VALUE."
        sub1 = "Apply to join at mahayukti.com"
        sub2 = "Get matched with clients who need you."
        cta  = "Apply now →"

    h_font   = _font(88, bold=True)
    s_font   = _font(44, bold=False)
    cta_font = _font(50, bold=True)

    y = zone_mid - 280
    for line in [line1, line2]:
        bbox = draw.textbbox((0, 0), line, font=h_font)
        x = (REEL_W - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, font=h_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=h_font, fill=WHITE)
        y += 108

    y += 16
    draw.rectangle([(REEL_W // 2 - 80, y), (REEL_W // 2 + 80, y + 5)], fill=accent)
    y += 36

    for line in [sub1, sub2]:
        bbox = draw.textbbox((0, 0), line, font=s_font)
        x = (REEL_W - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=s_font, fill=LIGHT)
        y += 60

    y += 24
    bbox = draw.textbbox((0, 0), cta, font=cta_font)
    bw = bbox[2] - bbox[0] + 60
    bx = (REEL_W - bw) // 2
    draw.rounded_rectangle([(bx, y), (bx + bw, y + 74)], radius=37, fill=accent)
    draw.text((bx + 30, y + 12), cta, fill=DARK, font=cta_font)

    return np.array(img)


# ── Audio helpers ──────────────────────────────────────────────────────────

async def _tts(text: str, path: str):
    comm = edge_tts.Communicate(text, voice="en-IN-NeerjaNeural", rate="+5%")
    await comm.save(path)


def _generate_ambient(seed: int, output_path: str, duration: float = 120.0) -> bool:
    preset = _AMBIENT_PRESETS[seed % len(_AMBIENT_PRESETS)]
    bass, mid, high, bpm = preset
    pulse = bpm / 60.0
    expr = (
        f"0.15*sin({bass}*2*PI*t)*sin({pulse}*2*PI*t+0.1)+"
        f"0.11*sin({mid}*2*PI*t)*sin({pulse*1.3}*2*PI*t+0.4)+"
        f"0.07*sin({high}*2*PI*t)*sin({pulse*0.7}*2*PI*t+0.8)"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100",
        "-t", str(duration), "-c:a", "aac", "-b:a", "128k", output_path,
    ]
    try:
        return subprocess.run(cmd, capture_output=True).returncode == 0
    except Exception:
        return False


def _mix_audio(voice: str, music: str, output: str) -> bool:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", voice, "-i", music,
        "-filter_complex",
        "[1:a]volume=0.07,aloop=loop=-1:size=2e+09[m];[0:a][m]amix=inputs=2:duration=first[out]",
        "-map", "[out]", "-c:a", "aac", "-b:a", "192k", output,
    ]
    try:
        return subprocess.run(cmd, capture_output=True).returncode == 0
    except Exception:
        return False


def _build_reel_script(content: dict) -> str:
    post_type = content.get("post_type", "client")
    subdomain = content.get("subdomain", "")
    headline  = content.get("image_headline", "")
    excerpt   = content.get("excerpt", "")

    if post_type in ("client", "morning"):
        return (
            f"{headline}. "
            f"{excerpt} "
            f"Mahayukti is India's vetted professional advisory network. "
            f"When you have a complex problem in {subdomain} — or any domain — "
            f"Mahayukti connects you to the exact verified specialist for that need. "
            f"Not a generalist. The one expert in India who has handled this before. "
            f"Here is how it works. "
            f"One — describe your problem at mahayukti dot com. "
            f"Two — Mahayukti matches you to the right specialist. "
            f"Three — work directly with that expert, with full accountability. "
            f"Stop settling for the wrong advice. "
            f"Visit mahayukti dot com and describe your problem today."
        )
    else:
        return (
            f"{headline}. "
            f"{excerpt} "
            f"Mahayukti is India's vetted professional advisory network — "
            f"and we are building it with the best professionals in the country. "
            f"If you are a senior expert in {subdomain}, "
            f"Mahayukti connects you directly to clients who need exactly your expertise. "
            f"Here is how joining works. "
            f"One — apply at mahayukti dot com with your credentials. "
            f"Two — get vetted by the Mahayukti team. "
            f"Three — receive introductions to clients who need you, and earn from your expertise. "
            f"Your knowledge has value beyond your current role. "
            f"Apply to join at mahayukti dot com today."
        )


def generate_reel(content: dict, post_id: str, gh_token: str) -> tuple:
    """Returns (local_reel_path, public_url)."""
    domain    = content.get("domain", "")
    post_type = content.get("post_type", "morning")
    headline  = content.get("image_headline", "")
    excerpt   = content.get("excerpt", "")
    subtext   = content.get("image_subtext", "")

    tmp        = tempfile.mkdtemp()
    voice_raw  = os.path.join(tmp, "voice_raw.mp3")
    music_path = os.path.join(tmp, "music.aac")
    audio_path = os.path.join(tmp, "audio.mp3")
    reel_path  = f"/tmp/reel-{post_id}.mp4"

    try:
        print("\n  Fetching Pollinations background...")
        bg = _fetch_bg(domain, post_id)
        if bg is None:
            print("  Pollinations unavailable — using brand gradient fallback.")
            bg = Image.new("RGB", (REEL_W, REEL_H), NAVY)
            draw_bg = ImageDraw.Draw(bg)
            for y in range(REEL_H):
                t = y / REEL_H
                draw_bg.line([(0, y), (REEL_W, y)], fill=(
                    int(NAVY[0] + (DARK[0] - NAVY[0]) * t),
                    int(NAVY[1] + (DARK[1] - NAVY[1]) * t),
                    int(NAVY[2] + (DARK[2] - NAVY[2]) * t),
                ))

        if post_type in ("client", "morning"):
            steps = [
                "Describe your problem at mahayukti.com",
                "Get matched to the exact verified specialist",
                "Work directly — with full accountability",
            ]
            problem_body   = excerpt or subtext
            solution_head  = "Mahayukti fixes this"
            solution_body  = "India's vetted advisory network — the exact specialist for your exact need."
        else:
            steps = [
                "Apply at mahayukti.com with your credentials",
                "Get vetted by the Mahayukti team",
                "Receive client introductions — earn from your expertise",
            ]
            problem_body   = excerpt or subtext
            solution_head  = "Join Mahayukti"
            solution_body  = "India's vetted advisory network — where top professionals get matched with clients."

        frames = [
            _make_hook_slide(headline, domain, bg),
            _make_body_slide("The problem", problem_body, domain, bg),
            _make_body_slide(solution_head, solution_body, domain, bg),
            _make_steps_slide("How it works", steps, domain, bg),
            _make_cta_slide(post_type, domain, bg),
        ]

        print("  Generating voiceover...")
        script = _build_reel_script(content)
        asyncio.run(_tts(script, voice_raw))

        print("  Synthesising background music...")
        seed = _seed(post_id)
        try:
            ffprobe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", voice_raw],
                capture_output=True, text=True,
            )
            import json as _json
            voice_dur = float(_json.loads(ffprobe.stdout)["format"]["duration"]) + 5.0
        except Exception:
            voice_dur = 120.0

        if _generate_ambient(seed, music_path, duration=voice_dur):
            if _mix_audio(voice_raw, music_path, audio_path):
                print("  Music mixed in.")
            else:
                import shutil as _sh
                _sh.copy2(voice_raw, audio_path)
        else:
            import shutil as _sh
            _sh.copy2(voice_raw, audio_path)

        print("  Composing reel...")
        audio = AudioFileClip(audio_path)
        duration  = audio.duration
        per_slide = max(duration / 5, 5.0)

        try:
            clips = [ImageClip(f).with_duration(per_slide) for f in frames]
        except AttributeError:
            clips = [ImageClip(f).set_duration(per_slide) for f in frames]

        final = concatenate_videoclips(clips, method="compose")
        try:
            final = final.with_audio(audio.with_duration(per_slide * 5))
        except AttributeError:
            final = final.set_audio(audio.set_duration(per_slide * 5))

        final.write_videofile(reel_path, fps=25, codec="libx264", audio_codec="aac",
                              preset="ultrafast", logger=None)
        print(f"  Reel composed: {reel_path}")

        print("  Uploading reel to repo...")
        reel_url = _upload_reel(reel_path, post_id, gh_token)
        return reel_path, reel_url

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _upload_reel(reel_path: str, post_id: str, gh_token: str) -> str:
    repo     = "vedantrungta1209/mahayukti-website"
    filename = f"reel-{post_id}.mp4"
    api_url  = f"https://api.github.com/repos/{repo}/contents/images/{filename}"
    headers  = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"}

    with open(reel_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    check = requests.get(api_url, headers=headers)
    sha   = check.json().get("sha") if check.status_code == 200 else None

    payload = {"message": f"Reel: {filename}", "content": encoded, "branch": "main"}
    if sha:
        payload["sha"] = sha

    r = requests.put(api_url, headers=headers, json=payload)
    r.raise_for_status()
    url = f"https://mahayukti.com/images/{filename}"
    print(f"  Reel uploaded: {url}")
    return url
