"""
MahaYukti reel generator — local animated slides + edge-tts voiceover.
No external AI APIs. Reliable, fast, fully local.
Output: 1080x1920 vertical MP4 for Instagram Reels / YouTube Shorts / Facebook Reels
"""

import asyncio, os, shutil, textwrap, time
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

# ── Brand ──────────────────────────────────────────────────────────────────
NAVY  = (11,  27,  58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (8,   20,  45)

REEL_W, REEL_H = 1080, 1920
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _centered_text(draw, text: str, y: int, font, color, max_w: int = REEL_W - 80):
    """Draw centered text, returns new y after drawing."""
    for line in textwrap.wrap(text, width=28):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (REEL_W - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += bbox[3] - bbox[1] + 14
    return y


def _base_slide(tag: str = "") -> tuple:
    """Create the base canvas with header and footer. Returns (img, draw)."""
    img  = Image.new("RGB", (REEL_W, REEL_H), NAVY)
    draw = ImageDraw.Draw(img)

    # Diagonal texture
    for i in range(0, REEL_W + REEL_H, 60):
        draw.line([(i, 0), (0, i)], fill=(15, 32, 68), width=1)

    # Top + bottom gold bars
    draw.rectangle([(0, 0), (REEL_W, 8)], fill=GOLD)
    draw.rectangle([(0, REEL_H - 8), (REEL_W, REEL_H)], fill=GOLD)

    # Header block
    draw.rectangle([(0, 0), (REEL_W, 168)], fill=DARK)
    draw.rectangle([(0, 166), (REEL_W, 170)], fill=GOLD)
    draw.text((50, 24), "MAHAYUKTI", fill=GOLD, font=_font(FONT_BOLD, 72))
    draw.text((50, 108), "India's Expert Advisory Network", fill=LIGHT, font=_font(FONT_REG, 28))

    if tag:
        tag_font = _font(FONT_BOLD, 24)
        bbox = draw.textbbox((0, 0), tag.upper(), font=tag_font)
        tx = REEL_W - (bbox[2] - bbox[0]) - 50
        draw.text((tx, 60), tag.upper(), fill=GOLD, font=tag_font)

    # Footer block
    draw.rectangle([(0, 1780), (REEL_W, REEL_H - 8)], fill=DARK)
    draw.rectangle([(0, 1780), (REEL_W, 1784)], fill=GOLD)
    cta_font = _font(FONT_BOLD, 46)
    bbox = draw.textbbox((0, 0), "mahayukti.com", font=cta_font)
    draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, 1806), "mahayukti.com", fill=GOLD, font=cta_font)
    h_font = _font(FONT_REG, 32)
    bbox = draw.textbbox((0, 0), "@WeAreMahayukti", font=h_font)
    draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, 1864), "@WeAreMahayukti", fill=LIGHT, font=h_font)

    return img, draw


def _make_hook_slide(headline: str, tag: str = "") -> np.ndarray:
    """Slide 1 — big punchy hook, no body text."""
    img, draw = _base_slide(tag)
    zone_mid = (200 + 1780) // 2

    h_font  = _font(FONT_BOLD, 100)
    lines   = textwrap.wrap(headline.upper(), 14)[:3]
    line_h  = 118
    total_h = len(lines) * line_h
    y = zone_mid - total_h // 2

    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=h_font)
        draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, y), ln, fill=WHITE, font=h_font)
        y += line_h

    return np.array(img)


def _make_body_slide(headline: str, body: str, tag: str = "") -> np.ndarray:
    """Slide 2/3 — medium headline + supporting body text."""
    img, draw = _base_slide(tag)
    zone_mid = (200 + 1780) // 2

    h_font = _font(FONT_BOLD, 72)
    b_font = _font(FONT_REG,  46)

    h_lines = textwrap.wrap(headline.upper(), 18)[:3]
    b_lines = textwrap.wrap(body, 34)[:5]
    line_h  = 88
    gap     = 36
    b_line_h = 58

    total_h = (len(h_lines) * line_h) + (gap + len(b_lines) * b_line_h if b_lines else 0)
    y = zone_mid - total_h // 2

    for ln in h_lines:
        bbox = draw.textbbox((0, 0), ln, font=h_font)
        draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, y), ln, fill=WHITE, font=h_font)
        y += line_h

    if b_lines:
        draw.rectangle([(REEL_W // 2 - 70, y + 10), (REEL_W // 2 + 70, y + 15)], fill=GOLD)
        y += gap
        for ln in b_lines:
            bbox = draw.textbbox((0, 0), ln, font=b_font)
            draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, y), ln, fill=LIGHT, font=b_font)
            y += b_line_h

    return np.array(img)


def _make_steps_slide(title: str, steps: list[str]) -> np.ndarray:
    """Slide 4 — numbered steps (how it works)."""
    img, draw = _base_slide()

    t_font = _font(FONT_BOLD, 54)
    s_font = _font(FONT_REG,  44)
    n_font = _font(FONT_BOLD, 80)

    # Title
    bbox = draw.textbbox((0, 0), title.upper(), font=t_font)
    draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, 220), title.upper(), fill=GOLD, font=t_font)
    draw.rectangle([(REEL_W // 2 - 70, 294), (REEL_W // 2 + 70, 299)], fill=GOLD)

    y = 340
    for i, step in enumerate(steps[:3], 1):
        # Number circle
        draw.ellipse([(50, y), (134, y + 84)], fill=GOLD)
        n_bbox = draw.textbbox((0, 0), str(i), font=n_font)
        draw.text((92 - (n_bbox[2] - n_bbox[0]) // 2, y + 2), str(i), fill=DARK, font=n_font)

        # Step text
        step_y = y + 16
        for line in textwrap.wrap(step, 26)[:2]:
            draw.text((160, step_y), line, font=s_font, fill=WHITE)
            step_y += 52
        y += 160

    return np.array(img)


def _make_cta_slide(post_type: str) -> np.ndarray:
    """Slide 5 — final CTA."""
    img, draw = _base_slide()
    zone_mid = (200 + 1780) // 2

    if post_type == "morning":
        line1 = "HAVE A COMPLEX"
        line2 = "PROBLEM?"
        sub   = "Describe it at mahayukti.com"
        sub2  = "Get matched to the exact expert."
        cta   = "Sign up FREE →"
    else:
        line1 = "YOUR EXPERTISE"
        line2 = "HAS VALUE."
        sub   = "Apply to join at mahayukti.com"
        sub2  = "Get matched with clients who need you."
        cta   = "Apply now →"

    h_font  = _font(FONT_BOLD, 96)
    s_font  = _font(FONT_REG,  46)
    cta_font = _font(FONT_BOLD, 52)

    y = zone_mid - 260
    for line in [line1, line2]:
        bbox = draw.textbbox((0, 0), line, font=h_font)
        draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, y), line, fill=WHITE, font=h_font)
        y += 114

    y += 20
    draw.rectangle([(REEL_W // 2 - 70, y), (REEL_W // 2 + 70, y + 5)], fill=GOLD)
    y += 36

    for line in [sub, sub2]:
        bbox = draw.textbbox((0, 0), line, font=s_font)
        draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, y), line, fill=LIGHT, font=s_font)
        y += 62

    y += 30
    # CTA pill
    bbox = draw.textbbox((0, 0), cta, font=cta_font)
    bw = bbox[2] - bbox[0] + 60
    bx = (REEL_W - bw) // 2
    draw.rectangle([(bx, y), (bx + bw, y + 76)], fill=GOLD)
    draw.text((bx + 30, y + 12), cta, fill=DARK, font=cta_font)

    return np.array(img)


# ── 1. Voiceover via edge-tts ─────────────────────────────────────────────

async def _tts(text: str, path: str):
    comm = edge_tts.Communicate(text, voice="en-IN-NeerjaNeural", rate="+5%")
    await comm.save(path)


def generate_voice(text: str, path: str):
    asyncio.run(_tts(text, path))
    print(f"  Voice saved: {path}")


# ── 2. Build reel script from content ─────────────────────────────────────

def _build_reel_script(content: dict) -> str:
    post_type = content.get("post_type", "client")
    domain    = content.get("domain", "")
    subdomain = content.get("subdomain", "")
    headline  = content.get("image_headline", "")
    excerpt   = content.get("excerpt", "")

    if post_type == "client" or post_type == "morning":
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


# ── 3. Compose reel — 5 structured slides ────────────────────────────────

def compose_reel(audio_path: str, content: dict, out_path: str):
    audio     = AudioFileClip(audio_path)
    duration  = audio.duration
    per_slide = max(duration / 5, 5.0)

    post_type = content.get("post_type", "client")
    domain    = content.get("domain", "")
    headline  = content.get("image_headline", "")
    excerpt   = content.get("excerpt", "")
    subtext   = content.get("image_subtext", "")

    if post_type in ("client", "morning"):
        steps = [
            "Describe your problem at mahayukti.com",
            "Get matched to the exact verified specialist",
            "Work directly — with full accountability",
        ]
        problem_body = excerpt or subtext
        solution_headline = "Mahayukti fixes this"
        solution_body = "India's vetted advisory network — connecting you to the exact specialist for your exact need."
    else:
        steps = [
            "Apply at mahayukti.com with your credentials",
            "Get vetted by the Mahayukti team",
            "Receive client introductions — earn from your expertise",
        ]
        problem_body = excerpt or subtext
        solution_headline = "Join Mahayukti"
        solution_body = "India's vetted advisory network — where top professionals get matched with clients who need them."

    frames = [
        _make_hook_slide(headline, domain),
        _make_body_slide("The problem", problem_body, ""),
        _make_body_slide(solution_headline, solution_body, ""),
        _make_steps_slide("How it works", steps),
        _make_cta_slide(post_type),
    ]

    try:
        clips = [ImageClip(f).with_duration(per_slide) for f in frames]
    except AttributeError:
        clips = [ImageClip(f).set_duration(per_slide) for f in frames]

    final = concatenate_videoclips(clips, method="compose")
    try:
        final = final.with_audio(audio.with_duration(per_slide * 5))
    except AttributeError:
        final = final.set_audio(audio.set_duration(per_slide * 5))

    final.write_videofile(
        out_path, fps=25, codec="libx264", audio_codec="aac",
        preset="ultrafast", logger=None,
    )
    print(f"  Reel composed: {out_path}")


# ── 4. Upload to GitHub Releases (free public CDN) ────────────────────────

def upload_reel(reel_path: str, post_id: str, gh_token: str) -> str:
    repo    = "vedantrungta1209/mahayukti-website"
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    tag      = f"reels-{post_id}-{int(time.time())}"
    filename = f"reel-{post_id}.mp4"

    rel = requests.post(
        f"https://api.github.com/repos/{repo}/releases",
        headers=headers,
        json={"tag_name": tag, "name": tag, "body": "Auto-generated reel", "draft": False},
    )
    rel.raise_for_status()
    upload_url = rel.json()["upload_url"].replace("{?name,label}", "")

    with open(reel_path, "rb") as f:
        up = requests.post(
            f"{upload_url}?name={filename}",
            headers={**headers, "Content-Type": "video/mp4"},
            data=f,
        )
        up.raise_for_status()

    public_url = up.json()["browser_download_url"]
    print(f"  Reel uploaded: {public_url}")
    return public_url


# ── Main entry ─────────────────────────────────────────────────────────────

def generate_reel(content: dict, post_id: str, gh_token: str) -> tuple:
    """Returns (local_reel_path, public_github_url)."""
    import tempfile

    script = _build_reel_script(content)

    tmp        = tempfile.mkdtemp()
    audio_path = os.path.join(tmp, "voice.mp3")
    reel_path  = f"/tmp/reel-{post_id}.mp4"

    try:
        print("\n  Generating voiceover...")
        generate_voice(script, audio_path)

        print("  Composing animated slides reel...")
        compose_reel(audio_path, content, reel_path)

        print("  Uploading reel to GitHub Releases...")
        reel_url = upload_reel(reel_path, post_id, gh_token)
        return reel_path, reel_url

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
