#!/usr/bin/env python3
"""
Mahayukti Finance — SHORT pipeline on Kaggle T4 GPU.
Runs Wan 2.1 locally (free). No fal.ai needed.
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── 1. Torch version — P100 (sm_60) needs torch 2.0.x ────────────────────────
_gpu = subprocess.run(
    ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
    capture_output=True, text=True
).stdout.strip()
_cuda_major = int(_gpu.split(".")[0]) if _gpu else 8
if _cuda_major < 7:
    print(f"P100 detected (sm_{_gpu.replace('.','')}) — installing torch 2.0.1+cu118")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "torch==2.0.1+cu118", "torchvision==0.15.2+cu118",
        "--index-url", "https://download.pytorch.org/whl/cu118",
        "--force-reinstall",
    ], check=True)
else:
    print(f"GPU sm_{_gpu.replace('.','')}: using default torch")

# ── 2. Install dependencies ───────────────────────────────────────────────────
subprocess.run([
    sys.executable, "-m", "pip", "install", "-q",
    "anthropic", "edge-tts", "diffusers>=0.33.0", "transformers",
    "accelerate", "imageio[ffmpeg]", "google-api-python-client",
    "google-auth", "google-auth-oauthlib", "google-auth-httplib2",
], check=True)

import anthropic
import edge_tts
import imageio
import numpy as np
import torch
from diffusers import WanPipeline
from diffusers.utils import export_to_video
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

if torch.cuda.is_available():
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
else:
    raise RuntimeError("No GPU available.")

# ── 3. Load secrets ───────────────────────────────────────────────────────────
_secrets_file = Path(__file__).parent / "secrets.json"
if _secrets_file.exists():
    _s = json.loads(_secrets_file.read_text())
    ANTHROPIC_KEY = _s["ANTHROPIC_API_KEY"]
    YT_TOKEN_JSON = _s["YOUTUBE_FINANCE_TOKEN_JSON"]
    GH_TOKEN      = _s["GH_TOKEN"]
else:
    from kaggle_secrets import UserSecretsClient
    _sc = UserSecretsClient()
    ANTHROPIC_KEY = _sc.get_secret("ANTHROPIC_API_KEY")
    YT_TOKEN_JSON = _sc.get_secret("YOUTUBE_FINANCE_TOKEN_JSON")
    GH_TOKEN      = _sc.get_secret("GH_TOKEN")

# ── 3. Clone repo for configs + counter ───────────────────────────────────────
GH_REPO = "vedantrungta1209/mahayukti-website"
REPO_DIR = Path("/kaggle/working/repo")
subprocess.run([
    "git", "clone", f"https://{GH_TOKEN}@github.com/{GH_REPO}.git",
    str(REPO_DIR), "--depth=5"
], check=True)

sys.path.insert(0, str(REPO_DIR / "channels"))
from configs import finance as cfg

CHANNEL_ID = cfg.CHANNEL_ID
VOICE      = cfg.VOICE        # en-IN-NeerjaNeural
MODE       = "short"

# ── 4. Counter ────────────────────────────────────────────────────────────────
COUNTER_FILE = REPO_DIR / f"channels/counters/{CHANNEL_ID}_{MODE}.txt"

def read_counter():
    try:
        return int(COUNTER_FILE.read_text().strip())
    except Exception:
        return 0

def write_and_push_counter(idx):
    COUNTER_FILE.write_text(str(idx))
    subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.name", "kaggle-bot"], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.email", "kaggle-bot@mahayukti"], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "add", str(COUNTER_FILE)], check=True)
    subprocess.run([
        "git", "-C", str(REPO_DIR), "commit", "-m",
        f"chore: {CHANNEL_ID} {MODE} counter [skip ci]"
    ], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "pull", "--rebase", "origin", "main"], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "push"], check=True)

idx   = read_counter()
topic = cfg.SHORT_TOPICS[idx % len(cfg.SHORT_TOPICS)]
print(f"\n📱 SHORT [{idx}]: {topic['name']}")

# ── 5. Generate script via Claude ────────────────────────────────────────────
print("✍️  Generating script…")
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

prompt = f"""You create viral YouTube Shorts scripts for {cfg.CHANNEL_NAME} ({cfg.CHANNEL_HANDLE}).
Channel niche: {cfg.NICHE}
Video style: {cfg.VIDEO_STYLE}
Topic: {topic['name']}
Category: {topic.get('category', 'General')}

Write a 55-60 second Short. Return ONLY valid JSON, no markdown:
{{
  "youtube_title": "Max 60 chars, punchy, emoji",
  "youtube_description": "80-word description + 6 hashtags",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "scenes": [
    {{
      "narration": "8-12 words spoken aloud",
      "visual_prompt": "Cinematic 9:16 vertical scene. Specific, vivid, NO text, NO faces. {cfg.VIDEO_STYLE}",
      "duration_hint": 6.0
    }}
  ]
}}
8-10 scenes totalling ~55 seconds. Scene 1: brutal hook. Final: micro-CTA."""

resp = client.messages.create(
    model="claude-opus-4-5", max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)
import re
raw = resp.content[0].text
script = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group())
scenes = script["scenes"]
print(f"   title: {script['youtube_title']}")
print(f"   scenes: {len(scenes)}")

# ── 6. TTS via edge-tts ───────────────────────────────────────────────────────
print("🎙️  Synthesising audio…")
WORK = Path("/kaggle/working/finance_short")
WORK.mkdir(exist_ok=True)
AUDIO_DIR = WORK / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

def ffprobe_duration(path):
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], capture_output=True, text=True)
    return float(r.stdout.strip())

async def synth(text, voice, path):
    comm = edge_tts.Communicate(text, voice)
    await comm.save(str(path))

for i, scene in enumerate(scenes):
    ap = AUDIO_DIR / f"scene_{i:02d}.mp3"
    asyncio.run(synth(scene["narration"], VOICE, ap))
    scene["audio_path"] = str(ap)
    scene["actual_duration"] = ffprobe_duration(ap)
    print(f"  [{i}] {scene['actual_duration']:.1f}s — {scene['narration'][:40]}")

# ── 7. Generate video clips via Wan 2.1 (local GPU) ──────────────────────────
print("🎬  Loading Wan 2.1 1.3B…")
CLIPS_DIR = WORK / "clips"
CLIPS_DIR.mkdir(exist_ok=True)

pipe = WanPipeline.from_pretrained(
    "Wan-AI/Wan2.1-T2V-1.3B",
    torch_dtype=torch.float16,
)
pipe.enable_model_cpu_offload()

NEGATIVE = "text, subtitles, watermark, logo, blurry, low quality, distorted, faces"

for i, scene in enumerate(scenes):
    clip_path = CLIPS_DIR / f"clip_{i:02d}.mp4"
    dur = scene["actual_duration"]
    num_frames = min(81, max(49, int(dur * 16)))   # 16fps, capped at 81

    print(f"  generating clip {i} ({dur:.1f}s → {num_frames} frames)…")
    output = pipe(
        prompt=scene["visual_prompt"],
        negative_prompt=NEGATIVE,
        height=832, width=480,       # 9:16 portrait for Shorts
        num_frames=num_frames,
        num_inference_steps=25,
        guidance_scale=5.0,
    )
    export_to_video(output.frames[0], str(clip_path), fps=16)
    scene["clip_path"] = str(clip_path)
    print(f"    ✓ clip {i} saved")

# ── 8. Compose with FFmpeg ────────────────────────────────────────────────────
print("🎞️  Composing…")
COMP_DIR = WORK / "composed"
COMP_DIR.mkdir(exist_ok=True)
SEG_DIR = COMP_DIR / "segments"
SEG_DIR.mkdir(exist_ok=True)

def ffmpeg(*args):
    result = subprocess.run(["ffmpeg", "-y"] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-1500:]}")

# Per scene: loop clip to match audio duration
seg_paths = []
for i, scene in enumerate(scenes):
    seg = SEG_DIR / f"seg_{i:02d}.mp4"
    ffmpeg(
        "-stream_loop", "-1", "-i", scene["clip_path"],
        "-i", scene["audio_path"],
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-vf", "scale=480:832",
        str(seg)
    )
    seg_paths.append(seg)

# Concatenate
concat_list = COMP_DIR / "list.txt"
concat_list.write_text("\n".join(f"file '{p}'" for p in seg_paths))

raw_video = COMP_DIR / "raw.mp4"
ffmpeg(
    "-f", "concat", "-safe", "0", "-i", str(concat_list),
    "-c", "copy", str(raw_video)
)

# Add channel watermark
final_video = COMP_DIR / "final.mp4"
font = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
drawtext = (
    f"fontfile={font}:text='{cfg.CHANNEL_NAME}':"
    f"fontsize=28:fontcolor=0xFFFFFF:"
    f"x=(w-text_w)/2:y=h-80:"
    f"box=1:boxcolor=0x00C864AA:boxborderw=12"
)
ffmpeg(
    "-i", str(raw_video),
    "-vf", f"drawtext={drawtext}",
    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
    "-c:a", "copy",
    str(final_video)
)
print(f"  ✓ composed: {final_video}")

# ── 9. Upload to YouTube ──────────────────────────────────────────────────────
print("🚀  Uploading to YouTube…")
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

youtube = build("youtube", "v3", credentials=creds)
title = script["youtube_title"]
if "#Shorts" not in title:
    title += " #Shorts"

body = {
    "snippet": {
        "title": title[:100],
        "description": script["youtube_description"][:5000],
        "tags": script["tags"][:500],
        "categoryId": "22",
    },
    "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
}
media = MediaFileUpload(str(final_video), mimetype="video/mp4", resumable=True, chunksize=8*1024*1024)
req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

response = None
while response is None:
    status, response = req.next_chunk()
    if status:
        print(f"  uploading… {int(status.progress()*100)}%")

video_id = response["id"]
print(f"  ✓ uploaded: https://youtu.be/{video_id}")

# ── 10. Update counter ────────────────────────────────────────────────────────
write_and_push_counter(idx + 1)
print(f"\n✅  Done. Counter → {idx + 1}")
