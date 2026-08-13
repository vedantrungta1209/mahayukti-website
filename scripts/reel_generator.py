"""
MahaYukti — Kinetic Text Reel Generator (v2)
BBC-style: pure black, large white text, saffron accent, phrases appear progressively.
No slideshows. No navy/gold. Phrases animate in, voices sound human.
Output: 1080×1920 MP4 — Instagram Reels / Facebook Reels / YouTube Shorts
"""
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import requests

from PIL import Image, ImageDraw, ImageFont

# ── Brand (NOT navy/gold — new identity) ───────────────────────────────────
BG      = (8,   8,   8)       # near-black, slightly warm
WHITE   = (255, 255, 255)
SAFFRON = (255, 107,  53)     # India saffron — vibrant, not corporate
DIM     = (160, 160, 160)     # dimmed text for previous phrases
HANDLE_COLOR = (120, 120, 120)

W, H    = 1080, 1920
FPS     = 30
FADE_FRAMES = 12   # 0.4s fade-in per phrase at 30fps

_FONT_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
_FONT_REG = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    for p in (_FONT_BOLD if bold else _FONT_REG):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(text: str, font, max_w: int, draw) -> list[str]:
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textbbox((0, 0), test, font=font)[2] > max_w and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def _audio_dur(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", path],
        capture_output=True, text=True,
    )
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 25.0


def _tts_elevenlabs(text: str, path: str) -> bool:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        return False
    voice_id = "EXAVITQu4vr4xnSDxMaL"   # Sarah — warm, clear
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": key, "Content-Type": "application/json",
                     "Accept": "audio/mpeg"},
            json={"text": text, "model_id": "eleven_turbo_v2_5",
                  "voice_settings": {"stability": 0.52, "similarity_boost": 0.78,
                                     "style": 0.12, "use_speaker_boost": True}},
            timeout=60,
        )
        r.raise_for_status()
        Path(path).write_bytes(r.content)
        print("  ElevenLabs voice ✓")
        return True
    except Exception as e:
        print(f"  ElevenLabs failed ({e}) — trying edge-tts")
        return False


async def _tts_edge(text: str, path: str):
    try:
        import edge_tts
        comm = edge_tts.Communicate(text, voice="en-IN-NeerjaNeural", rate="+5%")
        await comm.save(path)
        print("  edge-tts voice ✓")
    except Exception as e:
        raise RuntimeError(f"edge-tts failed: {e}")


def _tts(text: str, path: str):
    if not _tts_elevenlabs(text, path):
        asyncio.run(_tts_edge(text, path))


def _ambient(seed: int, path: str, duration: float) -> bool:
    presets = [
        (110.0, 146.8, 220.0, 55), (130.8, 174.6, 261.6, 60),
        (98.0,  130.8, 196.0, 58), (146.8, 220.0, 293.7, 62),
    ]
    bass, mid, high, bpm = presets[seed % len(presets)]
    pulse = bpm / 60.0
    expr = (
        f"0.12*sin({bass}*2*PI*t)*sin({pulse}*2*PI*t+0.1)+"
        f"0.09*sin({mid}*2*PI*t)*sin({pulse*1.3}*2*PI*t+0.4)+"
        f"0.06*sin({high}*2*PI*t)*sin({pulse*0.7}*2*PI*t+0.8)"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100",
           "-t", str(duration), "-c:a", "aac", "-b:a", "128k", path]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def _mix(voice: str, music: str, out: str) -> bool:
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-i", voice, "-i", music,
           "-filter_complex",
           "[1:a]volume=0.06,aloop=loop=-1:size=2e+09[m];[0:a][m]amix=inputs=2:duration=first[out]",
           "-map", "[out]", "-c:a", "aac", "-b:a", "192k", out]
    return subprocess.run(cmd, capture_output=True).returncode == 0


# ── Script generator — Claude writes kinetic-text-optimised phrases ─────────

def _build_phrases(content: dict) -> list[dict]:
    """
    Ask Claude to write 6-8 short phrases for a kinetic text reel.
    Returns list of {text, size, color} dicts.
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return _fallback_phrases(content)

    post_type = content.get("post_type", "morning")
    headline  = content.get("image_headline", "")
    excerpt   = content.get("excerpt", "")
    subdomain = content.get("subdomain", "")
    domain    = content.get("domain", "")

    if post_type in ("client", "morning"):
        audience_brief = (
            f"Audience: professionals and individuals in India who need expert guidance on "
            f"{subdomain or domain}. Goal: drive them to register at mahayukti.com "
            f"as a client/member. Show the pain point, then show the solution."
        )
        cta = "Register at mahayukti.com"
    else:
        audience_brief = (
            f"Audience: senior Indian professionals and SME experts in {subdomain or domain}. "
            f"Goal: drive them to apply at mahayukti.com as an advisor/expert member. "
            f"Show the value of monetising their expertise."
        )
        cta = "Apply at mahayukti.com"

    prompt = f"""You write punchy kinetic-text scripts for Instagram Reels.
Style: BBC-inspired — bold, confident, human, non-corporate. NOT AI-sounding.
Each phrase appears one at a time on a black screen in large white text.

Context:
{audience_brief}
Headline: {headline}
Brief: {excerpt}

Write EXACTLY 7 phrases (NO more, NO less). Rules:
- Phrase 1: 3-5 word HOOK. Shocking or relatable. No explanation yet.
- Phrase 2-3: The problem or insight. 5-10 words each. Real and specific.
- Phrase 4-5: The solution / what Mahayukti does. Confident, not salesy.
- Phrase 6: Social proof or credibility (e.g. "Vetted. Verified. Accountable.")
- Phrase 7: CTA — exactly this: "{cta}"

Each phrase: plain text, no emojis, no hashtags, no punctuation except full stops.
Return JSON: {{"phrases": ["phrase1", "phrase2", ..., "phrase7"], "voice_script": "natural spoken version of all 7 phrases combined into 25-35 words for TTS"}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 400,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        text = r.json()["content"][0]["text"]
        import re
        m = re.search(r'\{.*\}', text, re.DOTALL)
        data = json.loads(m.group())
        phrases = data.get("phrases", [])[:7]
        voice   = data.get("voice_script", " ".join(phrases))
        print(f"  Script: {len(phrases)} phrases")
        return [{"text": p, "voice": voice if i == 0 else None} for i, p in enumerate(phrases)]
    except Exception as e:
        print(f"  Claude script failed ({e}) — using fallback")
        return _fallback_phrases(content)


def _fallback_phrases(content: dict) -> list[dict]:
    post_type = content.get("post_type", "morning")
    headline  = content.get("image_headline", "Your problem deserves the right expert")
    excerpt   = content.get("excerpt", "India's advisory ecosystem is broken")
    if post_type in ("client", "morning"):
        phrases = [
            headline[:50],
            excerpt[:60],
            "Most consultants give generic advice.",
            "You need the exact specialist who has done this before.",
            "Mahayukti matches you to that person.",
            "Vetted. Verified. Accountable.",
            "Register at mahayukti.com",
        ]
    else:
        phrases = [
            "Your expertise is worth more than your salary.",
            excerpt[:60],
            "Most professionals never monetise their real knowledge.",
            "Mahayukti connects you to clients who need exactly you.",
            "India's vetted advisory network. Built for specialists.",
            "Vetted. Verified. Earning.",
            "Apply at mahayukti.com",
        ]
    voice = " ".join(p for p in phrases[:6]) + " Visit mahayukti dot com."
    return [{"text": p, "voice": voice if i == 0 else None} for i, p in enumerate(phrases)]


# ── Frame renderer ──────────────────────────────────────────────────────────

def _render_frame(phrases_shown: list[str], active_idx: int,
                  alpha_frac: float) -> np.ndarray:
    """
    Render one video frame.
    phrases_shown: all phrases up to and including current one
    active_idx: index of the currently animating phrase
    alpha_frac: 0.0→1.0 fade progress of the active phrase
    """
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Saffron top bar (4px, barely there)
    draw.rectangle([(0, 0), (W, 4)], fill=SAFFRON)

    # Handle — bottom right, always visible
    h_font = _font(28, bold=False)
    draw.text((W - 280, H - 55), "@wearemahayukti", fill=HANDLE_COLOR, font=h_font)

    if not phrases_shown:
        return np.array(img)

    total = len(phrases_shown)
    is_cta = (active_idx == total - 1)

    # Layout: distribute phrases in the content zone (60px top → H-80px bottom)
    zone_top    = 80
    zone_bottom = H - 80
    zone_h      = zone_bottom - zone_top

    # Font sizes — first phrase is BIG hook, last is CTA (saffron), rest medium
    def get_font(idx, n_phrases):
        if idx == 0:
            return _font(110, bold=True)     # hook: massive
        if idx == n_phrases - 1:
            return _font(80, bold=True)      # CTA
        return _font(72, bold=True)          # body

    # Measure all shown phrases to compute total height
    max_w = W - 100   # 50px padding each side
    line_gap = 16     # between lines within a phrase
    phrase_gap = 48   # between phrases

    rendered = []   # list of (lines, font, color, is_active)
    for i, ph in enumerate(phrases_shown):
        fn   = get_font(i, total)
        col  = SAFFRON if i == total - 1 else WHITE
        dim  = SAFFRON if i == total - 1 else DIM
        is_a = (i == active_idx)
        lines = _wrap(ph, fn, max_w, draw)
        rendered.append((lines, fn, col if is_a else dim, is_a))

    # Compute total block height
    total_h = 0
    for lines, fn, col, is_a in rendered:
        bbox_h = fn.size + 8  # approx line height
        total_h += bbox_h * len(lines) + line_gap * (len(lines) - 1)
        total_h += phrase_gap
    total_h = max(total_h - phrase_gap, 1)

    # Vertically center the block
    start_y = zone_top + (zone_h - total_h) // 2
    y = max(start_y, zone_top)

    for phrase_i, (lines, fn, col, is_a) in enumerate(rendered):
        line_h = fn.size + 8
        for ln in lines:
            bbox = draw.textbbox((0, 0), ln, font=fn)
            tw   = bbox[2] - bbox[0]
            x    = (W - tw) // 2

            if is_a and alpha_frac < 1.0:
                # Fade: blend between BG and target color
                r = int(BG[0] + (col[0] - BG[0]) * alpha_frac)
                g = int(BG[1] + (col[1] - BG[1]) * alpha_frac)
                b = int(BG[2] + (col[2] - BG[2]) * alpha_frac)
                draw.text((x, y), ln, font=fn, fill=(r, g, b))
            else:
                draw.text((x, y), ln, font=fn, fill=col)
            y += line_h + line_gap
        y += phrase_gap

    return np.array(img)


# ── Video writer using ffmpeg raw pipe ──────────────────────────────────────

def _write_video(frames_iter, n_frames: int, fps: int, audio_path: str, out_path: str):
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24",
        "-r", str(fps), "-i", "pipe:0",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for frame in frames_iter:
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()


def _gen_frames(phrases: list[str], total_duration: float, fps: int):
    """
    Yield numpy frames. Each phrase gets equal time. It fades in, then holds.
    """
    n = len(phrases)
    if n == 0:
        return

    secs_per_phrase = total_duration / n
    hold_frames = int(secs_per_phrase * fps)

    shown = []
    for i, phrase in enumerate(phrases):
        shown = phrases[:i + 1]
        for f in range(hold_frames):
            if f < FADE_FRAMES:
                alpha = f / FADE_FRAMES
            else:
                alpha = 1.0
            frame = _render_frame(shown, i, alpha)
            yield frame


# ── Upload helper ───────────────────────────────────────────────────────────

def _upload_reel(reel_path: str, post_id: str, gh_token: str) -> str:
    import base64
    repo    = "vedantrungta1209/mahayukti-website"
    fname   = f"reel-{post_id}.mp4"
    api_url = f"https://api.github.com/repos/{repo}/contents/images/{fname}"
    headers = {"Authorization": f"token {gh_token}",
               "Accept": "application/vnd.github.v3+json"}

    encoded = base64.b64encode(Path(reel_path).read_bytes()).decode()
    check   = requests.get(api_url, headers=headers)
    sha     = check.json().get("sha") if check.status_code == 200 else None

    payload = {"message": f"reel: {fname}", "content": encoded, "branch": "main"}
    if sha:
        payload["sha"] = sha

    r = requests.put(api_url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return f"https://mahayukti.com/images/{fname}"


# ── Public API (same signature as old generator) ───────────────────────────

def generate_reel(content: dict, post_id: str, gh_token: str) -> tuple:
    """Returns (local_reel_path, public_url)."""
    tmp      = tempfile.mkdtemp()
    voice_p  = os.path.join(tmp, "voice.mp3")
    music_p  = os.path.join(tmp, "music.aac")
    audio_p  = os.path.join(tmp, "audio.mp3")
    reel_p   = f"/tmp/reel-{post_id}.mp4"

    try:
        print("\n🎬 Generating kinetic text reel...")

        # 1. Build phrase list via Claude
        phrase_data = _build_phrases(content)
        phrases     = [p["text"] for p in phrase_data]
        voice_text  = next((p["voice"] for p in phrase_data if p.get("voice")), " ".join(phrases))

        # 2. Generate voice
        print("  Generating voice...")
        _tts(voice_text, voice_p)
        duration = _audio_dur(voice_p) + 1.5   # small tail

        # 3. Background music
        print("  Generating ambient music...")
        import hashlib
        seed = int(hashlib.md5(post_id.encode()).hexdigest()[:8], 16) % 1000
        if _ambient(seed, music_p, duration):
            if not _mix(voice_p, music_p, audio_p):
                shutil.copy2(voice_p, audio_p)
        else:
            shutil.copy2(voice_p, audio_p)

        # 4. Render frames and write video
        print("  Rendering kinetic text frames...")
        total_frames = int(duration * FPS)
        _write_video(
            _gen_frames(phrases, duration, FPS),
            total_frames, FPS, audio_p, reel_p,
        )
        print(f"  Reel: {reel_p} ({duration:.1f}s)")

        # 5. Upload to GitHub CDN
        print("  Uploading reel...")
        reel_url = _upload_reel(reel_p, post_id, gh_token)
        print(f"  URL: {reel_url}")

        return reel_p, reel_url

    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"Reel generation failed: {e}") from e

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
