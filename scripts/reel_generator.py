"""
Talking-head reel generator for MahaYukti.
Stack: edge-tts (voice) → SadTalker on HuggingFace (talking head) → moviepy (compose)
Output: 1080×1920 vertical MP4 for Instagram Reels / YouTube Shorts
"""

import asyncio, os, shutil, tempfile, textwrap, json, base64
import numpy as np
import requests
import edge_tts
from gradio_client import Client, handle_file
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, ColorClip, ImageClip,
)
from PIL import Image, ImageDraw, ImageFont

# ── Brand ──────────────────────────────────────────────────────────────────
NAVY  = (11,  27,  58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)

REEL_W, REEL_H = 1080, 1920

ASSETS   = os.path.join(os.path.dirname(__file__), "assets")
AVATAR   = os.path.join(ASSETS, "avatar.jpg")

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ── 1. Voice ───────────────────────────────────────────────────────────────

async def _tts(text: str, path: str):
    comm = edge_tts.Communicate(text, voice="en-IN-NeerjaNeural", rate="+5%")
    await comm.save(path)

def generate_voice(text: str, path: str):
    asyncio.run(_tts(text, path))
    print("  Voice saved:", path)

# ── 2. Talking head via SadTalker (HuggingFace, free) ─────────────────────

SADTALKER_SPACES = [
    "vinthony/SadTalker",
    "fffiloni/SadTalker",
]

def generate_talking_head(audio_path: str, out_path: str):
    for space in SADTALKER_SPACES:
        try:
            print(f"  Trying SadTalker space: {space}")
            client = Client(space, verbose=False)
            result = client.predict(
                source_image=handle_file(AVATAR),
                driven_audio=handle_file(audio_path),
                preprocess="crop",
                still_mode=True,
                use_enhancer=False,
                batch_size=1,
                size=256,
                pose_style=0,
                exp_scale=1.0,
                api_name="/test",
            )
            video_file = result[0] if isinstance(result, (list, tuple)) else result
            shutil.copy(video_file, out_path)
            print("  Talking head saved:", out_path)
            return
        except Exception as e:
            print(f"  Space {space} failed: {e}")
    raise RuntimeError("All SadTalker spaces failed. Add avatar.jpg and retry.")

# ── 3. Overlay helpers ─────────────────────────────────────────────────────

def _font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def make_header(duration: float) -> ImageClip:
    img  = Image.new("RGB", (REEL_W, 130), NAVY)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 126), (REEL_W, 130)], fill=GOLD)
    draw.text((40, 22), "MAHAYUKTI", fill=GOLD,  font=_font(FONT_BOLD, 52))
    draw.text((40, 84), "India's Premier Professional Network",
              fill=LIGHT, font=_font(FONT_REG, 26))
    return ImageClip(np.array(img)).set_duration(duration)

def make_lower_third(headline: str, duration: float) -> ImageClip:
    H    = 220
    img  = Image.new("RGBA", (REEL_W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (REEL_W, H)], fill=(*NAVY, 225))
    draw.rectangle([(0, 0), (REEL_W, 5)], fill=(*GOLD, 255))

    for i, line in enumerate(textwrap.wrap(headline.upper(), 28)[:2]):
        draw.text((40, 18 + i * 58), line, fill=WHITE, font=_font(FONT_BOLD, 44))

    draw.text((40, 148), "mahayukti.com", fill=GOLD, font=_font(FONT_REG, 32))
    return (
        ImageClip(np.array(img), ismask=False)
        .set_duration(duration)
        .set_position((0, REEL_H - H))
    )

# ── 4. Compose final 9:16 reel ─────────────────────────────────────────────

def compose_reel(th_path: str, audio_path: str, headline: str, out_path: str):
    th    = VideoFileClip(th_path)
    audio = AudioFileClip(audio_path)
    dur   = audio.duration

    # Scale talking head to fill width
    th = th.resize(width=REEL_W - 40)
    th = th.loop(duration=dur) if th.duration < dur else th.subclip(0, dur)

    # Available vertical space between header (130px) and lower-third (220px)
    available = REEL_H - 130 - 220
    th_y = 130 + (available - th.h) // 2

    bg     = ColorClip(size=(REEL_W, REEL_H), color=NAVY, duration=dur)
    header = make_header(dur).set_position((0, 0))
    th_pos = th.set_position(((REEL_W - th.w) // 2, th_y))
    lower  = make_lower_third(headline, dur)

    final = CompositeVideoClip([bg, header, th_pos, lower], size=(REEL_W, REEL_H))
    final = final.set_audio(audio)
    final.write_videofile(
        out_path, fps=25, codec="libx264", audio_codec="aac",
        preset="ultrafast", logger=None,
    )
    print("  Reel composed:", out_path)

# ── 5. Upload reel to GitHub Releases (free public CDN) ───────────────────

def upload_reel(reel_path: str, post_id: str, gh_token: str) -> str:
    repo    = "vedantrungta1209/mahayukti-website"
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    tag = f"reels-{post_id}"

    # Create release
    rel = requests.post(
        f"https://api.github.com/repos/{repo}/releases",
        headers=headers,
        json={"tag_name": tag, "name": tag, "body": "Auto-generated reel", "draft": False},
    )
    if rel.status_code not in (200, 201, 422):
        rel.raise_for_status()

    # Get upload URL (handle existing release)
    if rel.status_code == 422:
        rel = requests.get(
            f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
            headers=headers,
        )
        rel.raise_for_status()
    upload_url = rel.json()["upload_url"].replace("{?name,label}", "")

    filename = f"reel-{post_id}.mp4"
    with open(reel_path, "rb") as f:
        up = requests.post(
            f"{upload_url}?name={filename}",
            headers={**headers, "Content-Type": "video/mp4"},
            data=f,
        )
        up.raise_for_status()

    public_url = up.json()["browser_download_url"]
    print("  Reel uploaded:", public_url)
    return public_url

# ── Main entry ─────────────────────────────────────────────────────────────

def generate_reel(content: dict, post_id: str, gh_token: str) -> str:
    """Returns public URL of the uploaded reel."""
    if not os.path.exists(AVATAR):
        raise FileNotFoundError(
            "scripts/assets/avatar.jpg missing. "
            "Add a clear front-facing photo (any size, JPG)."
        )

    script   = content["instagram_caption"].split("#")[0].strip()
    headline = content["image_headline"]

    tmp      = tempfile.mkdtemp()
    audio    = os.path.join(tmp, "voice.mp3")
    th_vid   = os.path.join(tmp, "talking_head.mp4")
    reel     = f"/tmp/reel-{post_id}.mp4"

    try:
        print("\n🎙️  Generating voiceover...")
        generate_voice(script, audio)

        print("🤖  Generating talking head (SadTalker)...")
        generate_talking_head(audio, th_vid)

        print("🎬  Composing reel...")
        compose_reel(th_vid, audio, headline, reel)

        print("☁️   Uploading reel...")
        url = upload_reel(reel, post_id, gh_token)
        return url

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
