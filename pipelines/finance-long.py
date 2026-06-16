#!/usr/bin/env python3
"""
Mahayukti Finance — LONG-FORM pipeline
Pexels stock footage • Runs on GitHub Actions runner (no GPU needed)
"""
import asyncio, json, os, re, subprocess, sys, time, requests
from pathlib import Path

# ── Secrets ───────────────────────────────────────────────────────────────────
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
YT_TOKEN_JSON = os.environ["YOUTUBE_FINANCE_TOKEN_JSON"]
GH_TOKEN      = os.environ["GH_TOKEN"]
PEXELS_KEY    = os.environ["PEXELS_API_KEY"]

# ── Clone repo for configs + counter ─────────────────────────────────────────
GH_REPO  = "vedantrungta1209/mahayukti-website"
REPO_DIR = Path("/tmp/repo")
subprocess.run([
    "git", "clone", f"https://{GH_TOKEN}@github.com/{GH_REPO}.git",
    str(REPO_DIR), "--depth=5"
], check=True)

sys.path.insert(0, str(REPO_DIR / "channels"))
from configs import finance as cfg

MODE = "long"
COUNTER_FILE = REPO_DIR / f"channels/counters/{cfg.CHANNEL_ID}_{MODE}.txt"

def read_counter():
    try: return int(COUNTER_FILE.read_text().strip())
    except: return 0

def push_counter(idx):
    COUNTER_FILE.write_text(str(idx))
    for cmd in [
        ["git", "-C", str(REPO_DIR), "config", "user.name", "gh-actions-bot"],
        ["git", "-C", str(REPO_DIR), "config", "user.email", "bot@mahayukti"],
        ["git", "-C", str(REPO_DIR), "add", str(COUNTER_FILE)],
        ["git", "-C", str(REPO_DIR), "commit", "-m", f"chore: {cfg.CHANNEL_ID} {MODE} counter [skip ci]"],
        ["git", "-C", str(REPO_DIR), "pull", "--rebase", "origin", "main"],
        ["git", "-C", str(REPO_DIR), "push"],
    ]:
        subprocess.run(cmd, check=True)

idx   = read_counter()
topic = cfg.LONG_TOPICS[idx % len(cfg.LONG_TOPICS)]
print(f"\n🎥 LONG [{idx}]: {topic['name']}")

# ── Generate script ───────────────────────────────────────────────────────────
import anthropic
print("✍️  Generating script…")
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

prompt = f"""You create deeply engaging YouTube documentary scripts for {cfg.CHANNEL_NAME} ({cfg.CHANNEL_HANDLE}).
Niche: {cfg.NICHE}
Topic: {topic['name']}
Angle: {topic.get('angle', '')}
Category: {topic.get('category', 'General')}

Write a 12-15 minute video (1800-2200 words narration). Return ONLY valid JSON, no markdown fences:
{{
  "youtube_title": "Max 70 chars, keyword-rich, emoji",
  "youtube_description": "400-word description with timestamps and 12 hashtags",
  "tags": ["tag1","tag2"],
  "sections": [
    {{
      "heading": "Section title",
      "narration": "280-340 words, flows naturally when read aloud",
      "search_queries": [
        "2-3 word Pexels search for clip 1 (e.g. 'stock market chart', 'indian rupee')",
        "2-3 word Pexels search for clip 2"
      ]
    }}
  ]
}}
6-7 sections. Section 1: dramatic hook. 2 search_queries per section."""

resp = client.messages.create(
    model="claude-opus-4-5", max_tokens=8000,
    messages=[{"role": "user", "content": prompt}]
)
script  = json.loads(re.search(r'\{.*\}', resp.content[0].text, re.DOTALL).group())
sections = script["sections"]
print(f"   title   : {script['youtube_title']}")
print(f"   sections: {len(sections)}")

# ── TTS — single event loop ───────────────────────────────────────────────────
import edge_tts
print("🎙️  Synthesising audio…")
WORK      = Path("/tmp/finance_long")
AUDIO_DIR = WORK / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def ffprobe_dur(path):
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture_output=True, text=True)
    return float(r.stdout.strip())

async def synth_all():
    for i, sec in enumerate(sections):
        ap = AUDIO_DIR / f"section_{i:02d}.mp3"
        await edge_tts.Communicate(sec["narration"], cfg.VOICE).save(str(ap))
        sec["audio_path"] = str(ap)
        print(f"  section {i}: {sec['heading']}")

asyncio.run(synth_all())
for sec in sections:
    sec["dur"] = ffprobe_dur(sec["audio_path"])
    print(f"  dur: {sec['dur']:.0f}s — {sec['heading']}")

# ── Download Pexels clips ─────────────────────────────────────────────────────
print("🎬  Downloading stock footage…")
CLIPS_DIR = WORK / "clips"
CLIPS_DIR.mkdir(exist_ok=True)

HEADERS   = {"Authorization": PEXELS_KEY}
FALLBACKS = ["stock market india", "personal finance india", "investment money",
             "business professional", "indian economy", "financial planning"]

def download_clip(query, save_path, fallback_idx=0):
    queries = [query] + FALLBACKS[fallback_idx % len(FALLBACKS):]
    for q in queries[:3]:
        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers=HEADERS,
                params={"query": q, "per_page": 10, "orientation": "landscape"},
                timeout=15
            )
            r.raise_for_status()
            videos = [v for v in r.json().get("videos", []) if v.get("duration", 0) >= 5]
            if not videos:
                continue
            files = sorted(videos[0].get("video_files", []),
                           key=lambda f: f.get("width", 0) * f.get("height", 0), reverse=True)
            chosen = next((f for f in files if f.get("width", 9999) <= 1920), files[0])
            dl = requests.get(chosen["link"], stream=True, timeout=60)
            dl.raise_for_status()
            with open(save_path, "wb") as fp:
                for chunk in dl.iter_content(8192):
                    fp.write(chunk)
            print(f"  ✓ '{q}' → {chosen.get('width')}x{chosen.get('height')}")
            return
        except Exception as e:
            print(f"  ⚠ '{q}': {e}")
            time.sleep(1)
    raise RuntimeError(f"No Pexels clip found for '{query}'")

for i, sec in enumerate(sections):
    sec["clip_paths"] = []
    queries = sec.get("search_queries", [f"finance {sec['heading']}"])
    for j, q in enumerate(queries):
        cp = CLIPS_DIR / f"sec_{i:02d}_clip_{j:02d}.mp4"
        download_clip(q, cp, fallback_idx=(i + j))
        sec["clip_paths"].append(str(cp))

# ── Generate Yukti portrait overlay (right-side anchor) ──────────────────────
print("🎭  Fetching Yukti overlay…")
YUKTI_PNG  = None
YUKTI_W, YUKTI_H = 560, 720   # portrait — fits right 44% of 1280×720

try:
    from PIL import Image as _PILImage, ImageDraw as _PILDraw
    import io as _io
    from urllib.parse import quote as _quote
    _YUKTI_PROMPT = (
        "candid portrait photograph of a 29 year old Indian woman, financial professional, "
        "natural warm confident smile, sharp intelligent eyes, subtle bindi, natural wavy black hair, "
        "wearing a deep teal blazer with gold threading, shot on Canon EOS R5 85mm f1.4 lens, "
        "shallow depth of field, natural studio lighting with soft rim light, ultra photorealistic, "
        "skin pores visible, natural imperfections, not AI generated, editorial photography quality, "
        "Vogue India style"
    )
    _yukti_url = (
        f"https://image.pollinations.ai/prompt/{_quote(_YUKTI_PROMPT)}"
        f"?width={YUKTI_W}&height={YUKTI_H}&seed=55901&nologo=true&model=flux-realism"
    )
    _r = requests.get(_yukti_url, timeout=90)
    _r.raise_for_status()
    _img = _PILImage.open(_io.BytesIO(_r.content)).convert("RGBA").resize((YUKTI_W, YUKTI_H))
    # Gradient fade on left edge so she blends into the text area
    _fade_w = 200
    _mask   = _PILImage.new("L", (YUKTI_W, YUKTI_H), 255)
    _md     = _PILDraw.Draw(_mask)
    for _x in range(_fade_w):
        _md.line([(_x, 0), (_x, YUKTI_H)], fill=int(255 * (_x / _fade_w) ** 1.8))
    _img.putalpha(_mask)
    YUKTI_PNG = WORK / "yukti_overlay.png"
    _img.save(str(YUKTI_PNG))
    print(f"  ✓ yukti overlay saved ({YUKTI_W}x{YUKTI_H})")
except Exception as _e:
    print(f"  ⚠ Yukti fetch failed, continuing without: {_e}")

# ── Compose with FFmpeg ───────────────────────────────────────────────────────
print("🎞️  Composing…")
COMP_DIR = WORK / "composed"
SEG_DIR  = COMP_DIR / "segments"
SEG_DIR.mkdir(parents=True, exist_ok=True)

def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-y"] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{r.stderr[-2000:]}")

section_segs = []
for i, sec in enumerate(sections):
    clips     = sec["clip_paths"]
    audio     = sec["audio_path"]
    dur       = sec["dur"]
    clip_dur  = dur / len(clips)
    sub_segs  = []

    for j, clip in enumerate(clips):
        sub_audio = SEG_DIR / f"sub_{i:02d}_{j:02d}.mp3"
        ffmpeg("-i", audio,
               "-ss", str(j * clip_dur), "-t", str(clip_dur),
               "-c:a", "copy", str(sub_audio))

        sub_seg = SEG_DIR / f"seg_{i:02d}_{j:02d}.mp4"
        if YUKTI_PNG and YUKTI_PNG.exists():
            # Yukti overlaid on right side: W-w positions PNG flush with right edge
            ffmpeg(
                "-stream_loop", "-1", "-i", clip,
                "-i", str(sub_audio),
                "-i", str(YUKTI_PNG),
                "-filter_complex",
                "[0:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720[bg];"
                "[bg][2:v]overlay=W-w:0[out]",
                "-map", "[out]", "-map", "1:a",
                "-shortest",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                "-r", "30",
                str(sub_seg)
            )
        else:
            ffmpeg(
                "-stream_loop", "-1", "-i", clip,
                "-i", str(sub_audio),
                "-map", "0:v", "-map", "1:a",
                "-shortest",
                "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                "-r", "30",
                str(sub_seg)
            )
        sub_segs.append(str(sub_seg))

    sec_seg = SEG_DIR / f"section_{i:02d}.mp4"
    if len(sub_segs) == 1:
        Path(sub_segs[0]).rename(sec_seg)
    else:
        lst = SEG_DIR / f"sec_{i:02d}_list.txt"
        lst.write_text("\n".join(f"file '{p}'" for p in sub_segs))
        ffmpeg("-f", "concat", "-safe", "0", "-i", str(lst),
               "-c", "copy", str(sec_seg))
    section_segs.append(str(sec_seg))
    print(f"  ✓ section {i} ({dur:.0f}s)")

final_list = COMP_DIR / "final_list.txt"
final_list.write_text("\n".join(f"file '{p}'" for p in section_segs))
raw_video  = COMP_DIR / "raw.mp4"
ffmpeg("-f", "concat", "-safe", "0", "-i", str(final_list),
       "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", str(raw_video))

final_video = COMP_DIR / "final.mp4"
font = next((p for p in [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
] if Path(p).exists()), None)

if font:
    drawtext = (
        f"fontfile={font}:text='{cfg.CHANNEL_NAME}':"
        f"fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h-60:"
        f"box=1:boxcolor=0x00C864AA:boxborderw=12"
    )
    ffmpeg("-i", str(raw_video), "-vf", f"drawtext={drawtext}",
           "-c:v", "libx264", "-preset", "fast", "-crf", "22",
           "-c:a", "copy", str(final_video))
else:
    import shutil; shutil.copy(raw_video, final_video)

print(f"  ✓ final: {final_video}")

# ── Upload to YouTube ─────────────────────────────────────────────────────────
print("🚀  Uploading to YouTube…")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

token_data = json.loads(YT_TOKEN_JSON)
creds = Credentials(
    token=token_data.get("token"),
    refresh_token=token_data["refresh_token"],
    token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
    client_id=token_data["client_id"],
    client_secret=token_data["client_secret"],
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

yt  = build("youtube", "v3", credentials=creds)
req = yt.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title":       script["youtube_title"][:100],
            "description": script["youtube_description"][:5000],
            "tags":        script["tags"][:500],
            "categoryId":  "22",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    },
    media_body=MediaFileUpload(str(final_video), mimetype="video/mp4",
                               resumable=True, chunksize=8*1024*1024),
)
response = None
while response is None:
    status, response = req.next_chunk()
    if status: print(f"  {int(status.progress()*100)}%")

print(f"  ✓ https://youtu.be/{response['id']}")
push_counter(idx + 1)
print(f"\n✅  Done. Counter → {idx + 1}")
