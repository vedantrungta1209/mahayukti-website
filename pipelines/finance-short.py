#!/usr/bin/env python3
"""
Mahayukti Finance — SHORT pipeline
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

idx   = read_counter()
topic = cfg.SHORT_TOPICS[idx % len(cfg.SHORT_TOPICS)]
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
  "youtube_title": "Max 60 chars, punchy, emoji",
  "youtube_description": "80-word description + 6 hashtags",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "scenes": [
    {{
      "narration": "8-12 words, punchy, spoken aloud",
      "search_query": "2-3 words for Pexels stock footage (e.g. 'stock market', 'indian rupee', 'mutual fund', 'tax planning')"
    }}
  ]
}}
8-10 scenes, ~55 sec total. Scene 1: brutal hook. Last scene: micro-CTA."""

resp = client.messages.create(
    model="claude-opus-4-5", max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)
script = json.loads(re.search(r'\{.*\}', resp.content[0].text, re.DOTALL).group())
scenes = script["scenes"]
print(f"   title : {script['youtube_title']}")
print(f"   scenes: {len(scenes)}")

# ── TTS — single event loop ───────────────────────────────────────────────────
import edge_tts
print("🎙️  Synthesising audio…")
WORK      = Path("/tmp/finance_short")
AUDIO_DIR = WORK / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def ffprobe_dur(path):
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture_output=True, text=True)
    return float(r.stdout.strip())

async def synth_all():
    for i, scene in enumerate(scenes):
        ap = AUDIO_DIR / f"scene_{i:02d}.mp3"
        await edge_tts.Communicate(scene["narration"], cfg.VOICE).save(str(ap))
        scene["audio_path"] = str(ap)
        print(f"  [{i}] {scene['narration'][:50]}")

asyncio.run(synth_all())
for scene in scenes:
    scene["dur"] = ffprobe_dur(scene["audio_path"])
    print(f"  dur: {scene['dur']:.1f}s")

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
            # Pick HD (≤1920 wide) to avoid huge 4K downloads
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

print(f"  ✓ https://youtu.be/{response['id']}")
push_counter(idx + 1)
print(f"\n✅  Done. Counter → {idx + 1}")
