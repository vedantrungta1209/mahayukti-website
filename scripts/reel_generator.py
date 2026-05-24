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

REEL_W, REEL_H = 1080, 1920
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ── 1. Voiceover via edge-tts (free, no API key) ──────────────────────────

async def _tts(text: str, path: str):
    comm = edge_tts.Communicate(text, voice="en-IN-NeerjaNeural", rate="+5%")
    await comm.save(path)


def generate_voice(text: str, path: str):
    asyncio.run(_tts(text, path))
    print(f"  Voice saved: {path}")


# ── 2. Slide renderer ─────────────────────────────────────────────────────

def _make_slide(headline: str, body: str = "", tag: str = "") -> np.ndarray:
    img  = Image.new("RGB", (REEL_W, REEL_H), NAVY)
    draw = ImageDraw.Draw(img)

    # Subtle diagonal texture
    for i in range(0, REEL_W + REEL_H, 60):
        draw.line([(i, 0), (0, i)], fill=(15, 32, 68), width=1)

    # Gold border bars
    draw.rectangle([(0, 0),              (REEL_W, 8)],       fill=GOLD)
    draw.rectangle([(0, REEL_H - 8),     (REEL_W, REEL_H)], fill=GOLD)

    # Logo header (top 160px)
    draw.rectangle([(0, 0), (REEL_W, 160)], fill=(8, 20, 45))
    draw.rectangle([(0, 158), (REEL_W, 162)], fill=GOLD)
    draw.text((55, 28), "MAHAYUKTI",                             fill=GOLD,  font=_font(FONT_BOLD, 64))
    draw.text((55, 104), "India's Premier Professional Network", fill=LIGHT, font=_font(FONT_REG,  30))

    # Domain tag (right side of header)
    if tag:
        draw.text((REEL_W - 55 - len(tag) * 16, 60), tag.upper(), fill=GOLD, font=_font(FONT_BOLD, 28))

    # Text zone: y 200–1750
    zone_top, zone_bot = 200, 1750
    zone_mid = (zone_top + zone_bot) // 2

    # Headline — large, centered vertically in zone
    h_lines = textwrap.wrap(headline.upper(), 18)[:4]
    line_h  = 112
    total_h = len(h_lines) * line_h + (40 if body else 0) + (len(textwrap.wrap(body, 36)[:5]) * 58 if body else 0)
    y = zone_mid - total_h // 2

    for ln in h_lines:
        bbox = draw.textbbox((0, 0), ln, font=_font(FONT_BOLD, 96))
        w    = bbox[2] - bbox[0]
        draw.text(((REEL_W - w) // 2, y), ln, fill=WHITE, font=_font(FONT_BOLD, 96))
        y += line_h

    # Gold rule
    if body:
        draw.rectangle([(REEL_W // 2 - 80, y + 12), (REEL_W // 2 + 80, y + 17)], fill=GOLD)
        y += 52

        for ln in textwrap.wrap(body, 36)[:5]:
            bbox = draw.textbbox((0, 0), ln, font=_font(FONT_REG, 48))
            w    = bbox[2] - bbox[0]
            draw.text(((REEL_W - w) // 2, y), ln, fill=LIGHT, font=_font(FONT_REG, 48))
            y += 60

    # Footer CTA
    draw.rectangle([(0, 1780), (REEL_W, 1912)], fill=(8, 20, 45))
    draw.rectangle([(0, 1780), (REEL_W, 1784)], fill=GOLD)
    cta = "mahayukti.com"
    bbox = draw.textbbox((0, 0), cta, font=_font(FONT_BOLD, 52))
    draw.text(((REEL_W - (bbox[2] - bbox[0])) // 2, 1836), cta, fill=GOLD, font=_font(FONT_BOLD, 52))

    return np.array(img)


# ── 3. Compose reel from 4 slides ─────────────────────────────────────────

def compose_reel(audio_path: str, content: dict, out_path: str):
    audio    = AudioFileClip(audio_path)
    duration = audio.duration
    per_slide = max(duration / 4, 6.0)  # minimum 6s per slide

    domain   = content.get("domain", "")
    headline = content.get("image_headline", "")
    subtext  = content.get("image_subtext", "")

    # Extract clean sentences from linkedin_text
    linkedin = content.get("linkedin_text", "").replace("\n", " ")
    sentences = [s.strip() for s in linkedin.split(". ") if len(s.strip()) > 20]
    sent1 = sentences[0][:80] if sentences else subtext
    sent2 = sentences[1][:80] if len(sentences) > 1 else "MahaYukti connects you to the exact specialist."

    slides = [
        (headline,  "",      domain),
        (sent1,     "",      ""),
        (sent2,     subtext, ""),
        ("Connect now", "Find your specialist at mahayukti.com", ""),
    ]

    clips = [ImageClip(_make_slide(h, b, t)).set_duration(per_slide) for h, b, t in slides]
    final = concatenate_videoclips(clips, method="compose").set_audio(
        audio.set_duration(per_slide * 4)
    )
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

    script = (
        content.get("image_headline", "") + ". "
        + ". ".join(
            s.strip()
            for s in content.get("linkedin_text", "").replace("\n", " ").split(". ")
            if len(s.strip()) > 20
        )[:280]
        + ". Visit mahayukti dot com."
    )

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
