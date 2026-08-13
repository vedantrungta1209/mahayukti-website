#!/usr/bin/env python3
"""
Mahayukti Finance — SHORT pipeline
ElevenLabs TTS • Pexels stock footage • Trending topic detection
Runs on GitHub Actions runner (no GPU needed).
"""
import asyncio, json, os, re, subprocess, sys, time, requests, urllib.parse, urllib.request
from pathlib import Path

# ── Secrets ───────────────────────────────────────────────────────────────────
ANTHROPIC_KEY      = os.environ["ANTHROPIC_API_KEY"]
YT_TOKEN_JSON      = os.environ["YOUTUBE_FINANCE_TOKEN_JSON"]
GH_TOKEN           = os.environ["GH_TOKEN"]
PEXELS_KEY         = os.environ["PEXELS_API_KEY"]
ELEVENLABS_KEY     = os.environ.get("ELEVENLABS_API_KEY", "")

# ── Clone repo for configs + counter ─────────────────────────────────────────
GH_REPO  = "vedantrungta1209/mahayukti-website"
REPO_DIR = Path("/tmp/repo")
subprocess.run([
    "git", "clone", f"https://{GH_TOKEN}@github.com/{GH_REPO}.git",
    str(REPO_DIR), "--depth=5"
], check=True)

sys.path.insert(0, str(REPO_DIR / "channels"))
from configs import finance as cfg

MODE = "short"
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

# ── Trending topic detection ──────────────────────────────────────────────────
def get_trending_topic(static_topics, static_idx):
    """Try YouTube autocomplete for a trending finance topic. Fall back to static."""
    seeds = getattr(cfg, "TRENDING_SEEDS", [
        "mutual fund india 2025", "income tax india 2025",
        "stock market today india", "best investment india 2025",
    ])
    seen = set()
    trending_terms = []
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    for seed in seeds[:3]:
        try:
            url = (
                "https://suggestqueries.google.com/complete/search"
                f"?client=youtube&ds=yt&q={urllib.parse.quote(seed)}&hl=en&gl=IN"
            )
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
            for item in (data[1] if len(data) > 1 else []):
                term = item[0] if isinstance(item, list) else str(item)
                if term and term.lower() not in seen and len(term) > 10:
                    seen.add(term.lower())
                    trending_terms.append(term)
        except Exception as e:
            print(f"  Trending skip '{seed}': {e}")

    if trending_terms:
        # Check if any trending term overlaps with a static topic
        for term in trending_terms[:8]:
            term_words = set(term.lower().split())
            for t in static_topics:
                topic_words = set(t["name"].lower().split())
                if len(topic_words & term_words) >= 2:
                    print(f"  Trending match: '{term}' → '{t['name']}'")
                    return t
        # No match — use top trending term as ad-hoc topic
        top = trending_terms[0]
        print(f"  Using live trending: '{top}'")
        return {"name": top, "category": "Trending"}

    return static_topics[static_idx % len(static_topics)]

idx   = read_counter()
topic = get_trending_topic(cfg.SHORT_TOPICS, idx)
print(f"\n📱 SHORT [{idx}]: {topic['name']}")

# ── Generate script ───────────────────────────────────────────────────────────
import anthropic
print("✍️  Generating script…")
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

prompt = f"""You create viral YouTube Shorts scripts for {cfg.CHANNEL_NAME} ({cfg.CHANNEL_HANDLE}).
Niche: {cfg.NICHE}
Topic: {topic['name']}
Category: {topic.get('category', 'General')}

Write a 55-60 second Short. Return ONLY valid JSON, no markdown fences:
{{
  "youtube_title": "Max 60 chars, punchy, emoji, stops scroll",
  "youtube_description": "80-word description + 6 hashtags",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "scenes": [
    {{
      "narration": "8-12 words max, punchy, spoken aloud, no filler",
      "search_query": "2-3 words for Pexels stock footage (e.g. 'stock market', 'indian rupee', 'mutual fund')"
    }}
  ]
}}
Rules:
- 8-10 scenes, ~55 sec total
- Scene 1: brutal hook — shocking stat or bold claim in first 3 words
- Scenes 2-8: one tight insight per scene, rapid delivery
- Last scene: micro-CTA ("Follow for daily finance tips")
- Use specific numbers, percentages, rupee amounts — makes it credible
- No filler: no "okay so", "basically", "right?"
"""

resp = client.messages.create(
    model="claude-opus-4-5", max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)
script = json.loads(re.search(r'\{.*\}', resp.content[0].text, re.DOTALL).group())
scenes = script["scenes"]
print(f"   title : {script['youtube_title']}")
print(f"   scenes: {len(scenes)}")

# ── TTS — ElevenLabs primary, edge-tts fallback ──────────────────────────────
print("🎙️  Synthesising audio…")
WORK      = Path("/tmp/finance_short")
AUDIO_DIR = WORK / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

EL_VOICE_ID = getattr(cfg, "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

def ffprobe_dur(path):
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture_output=True, text=True)
    return float(r.stdout.strip())

def synth_elevenlabs(text, output_path):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{EL_VOICE_ID}",
        headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json",
                 "Accept": "audio/mpeg"},
        json={
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.80, "style": 0.15},
        },
        timeout=60,
    )
    r.raise_for_status()
    Path(output_path).write_bytes(r.content)

async def synth_edge(text, output_path):
    import edge_tts
    await edge_tts.Communicate(text, cfg.VOICE).save(str(output_path))

use_elevenlabs = bool(ELEVENLABS_KEY)
print(f"  TTS engine: {'ElevenLabs' if use_elevenlabs else 'edge-tts'}")

for i, scene in enumerate(scenes):
    ap = AUDIO_DIR / f"scene_{i:02d}.mp3"
    if use_elevenlabs:
        try:
            synth_elevenlabs(scene["narration"], ap)
        except Exception as e:
            print(f"  EL failed ({e}), falling back to edge-tts")
            asyncio.run(synth_edge(scene["narration"], ap))
    else:
        asyncio.run(synth_edge(scene["narration"], ap))
    scene["audio_path"] = str(ap)
    scene["dur"] = ffprobe_dur(ap)
    print(f"  [{i}] {scene['dur']:.1f}s — {scene['narration'][:50]}")

# ── Download Pexels clips ─────────────────────────────────────────────────────
print("🎬  Downloading stock footage…")
CLIPS_DIR = WORK / "clips"
CLIPS_DIR.mkdir(exist_ok=True)

HEADERS   = {"Authorization": PEXELS_KEY}
FALLBACKS = ["stock market india", "personal finance", "indian money rupee",
             "business investment", "bank savings", "financial planning india"]

def download_clip(query, save_path, orientation="portrait", fallback_idx=0):
    queries = [query] + FALLBACKS[fallback_idx % len(FALLBACKS):]
    for q in queries[:3]:
        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers=HEADERS,
                params={"query": q, "per_page": 10, "orientation": orientation},
                timeout=15
            )
            r.raise_for_status()
            videos = [v for v in r.json().get("videos", []) if v.get("duration", 0) >= 4]
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

for i, scene in enumerate(scenes):
    clip_path = CLIPS_DIR / f"clip_{i:02d}.mp4"
    download_clip(scene.get("search_query", "finance"), clip_path,
                  orientation="portrait", fallback_idx=i)
    scene["clip_path"] = str(clip_path)

# ── Generate Yukti portrait overlay ──────────────────────────────────────────
print("🎭  Fetching Yukti overlay…")
YUKTI_PNG  = None
YUKTI_W, YUKTI_H = 480, 440   # portrait — fits bottom 52% of 480×852

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
    _fade_h = 260
    _mask   = _PILImage.new("L", (YUKTI_W, YUKTI_H), 255)
    _md     = _PILDraw.Draw(_mask)
    for _y in range(_fade_h):
        _md.line([(0, _y), (YUKTI_W, _y)], fill=int(255 * (_y / _fade_h) ** 1.8))
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

seg_paths = []
for i, scene in enumerate(scenes):
    seg = SEG_DIR / f"seg_{i:02d}.mp4"
    if YUKTI_PNG and YUKTI_PNG.exists():
        # Overlay Yukti in bottom portion; H-h positions PNG at bottom of frame
        ffmpeg(
            "-stream_loop", "-1", "-i", scene["clip_path"],
            "-i", scene["audio_path"],
            "-i", str(YUKTI_PNG),
            "-filter_complex",
            "[0:v]scale=480:852:force_original_aspect_ratio=increase,crop=480:852[bg];"
            "[bg][2:v]overlay=0:H-h[out]",
            "-map", "[out]", "-map", "1:a",
            "-shortest",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30",
            str(seg)
        )
    else:
        ffmpeg(
            "-stream_loop", "-1", "-i", scene["clip_path"],
            "-i", scene["audio_path"],
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            "-vf", "scale=480:852:force_original_aspect_ratio=increase,crop=480:852",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30",
            str(seg)
        )
    seg_paths.append(str(seg))
    print(f"  ✓ seg {i}")

concat_list = COMP_DIR / "list.txt"
concat_list.write_text("\n".join(f"file '{p}'" for p in seg_paths))
raw_video   = COMP_DIR / "raw.mp4"
ffmpeg("-f", "concat", "-safe", "0", "-i", str(concat_list),
       "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", str(raw_video))

final_video = COMP_DIR / "final.mp4"
font = next((p for p in [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
] if Path(p).exists()), None)

if font:
    drawtext = (
        f"fontfile={font}:text='{cfg.CHANNEL_NAME}':"
        f"fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h-80:"
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

yt    = build("youtube", "v3", credentials=creds)
title = script["youtube_title"]
if "#Shorts" not in title:
    title += " #Shorts"

req = yt.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title":       title[:100],
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

yt_id = response['id']
print(f"  ✓ https://youtu.be/{yt_id}")
push_counter(idx + 1)

# Cross-post to Instagram Reels + Facebook Reels + LinkedIn (non-fatal)
try:
    import sys as _sys
    _sys.path.insert(0, str(REPO_DIR))
    from channels.social_cross_poster import cross_post_short

    topic_name = script.get("youtube_title", cfg.SHORT_TOPICS[idx % len(cfg.SHORT_TOPICS)]["name"])
    ig_cap = (
        f"{script['youtube_title']}\n\n"
        f"{script.get('youtube_description', '')[:250]}\n\n"
        f"Follow @mahayuktifinance for daily finance tips 💰\n\n"
        f"#PersonalFinance #IndiaFinance #MutualFunds #StockMarket #MoneyTips "
        f"#FinanceIndia #WealthBuilding #Mahayukti #FinancialFreedom #Investing"
    )
    li_text = (
        f"New short on @mahayuktifinance: {topic_name}\n\n"
        f"Quick take for Indian investors — watch here: https://youtu.be/{yt_id}\n\n"
        f"#PersonalFinance #IndiaFinance #Investing #Mahayukti"
    )
    cross_post_short(str(final_video), ig_cap, li_text)
except Exception as _e:
    print(f"⚠️  Social cross-post failed (non-fatal): {_e}")

print(f"\n✅  Done. Counter → {idx + 1}")
