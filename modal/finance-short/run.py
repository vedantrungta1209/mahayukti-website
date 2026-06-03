"""
Mahayukti Finance — SHORT pipeline on Modal T4 GPU.
Triggered by GitHub Actions via: modal run modal/finance-short/run.py
"""
import modal
from pathlib import Path

app = modal.App("mahayukti-finance-short")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "git", "fonts-liberation")
    .pip_install(
        "anthropic",
        "edge-tts",
        "diffusers>=0.33.0",
        "transformers",
        "accelerate",
        "imageio[ffmpeg]",
        "google-api-python-client",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "torch",
        "torchvision",
    )
)

model_vol = modal.Volume.from_name("wan21-model-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="T4",
    timeout=5400,
    secrets=[modal.Secret.from_name("mahayukti-secrets")],
    volumes={"/root/models": model_vol},
)
def run_short():
    import asyncio, json, os, re, subprocess, sys
    from pathlib import Path

    os.environ["HF_HOME"] = "/root/models"

    import anthropic
    import edge_tts
    import torch
    from diffusers.utils import export_to_video
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"✅ GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

    ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
    YT_TOKEN_JSON = os.environ["YOUTUBE_FINANCE_TOKEN_JSON"]
    GH_TOKEN      = os.environ["GH_TOKEN"]

    # ── Clone repo ────────────────────────────────────────────────────────────
    GH_REPO  = "vedantrungta1209/mahayukti-website"
    REPO_DIR = Path("/tmp/repo")
    subprocess.run([
        "git", "clone", f"https://{GH_TOKEN}@github.com/{GH_REPO}.git",
        str(REPO_DIR), "--depth=5"
    ], check=True)

    sys.path.insert(0, str(REPO_DIR / "channels"))
    from configs import finance as cfg

    CHANNEL_ID = cfg.CHANNEL_ID
    VOICE      = cfg.VOICE
    MODE       = "short"

    # ── Counter ───────────────────────────────────────────────────────────────
    COUNTER_FILE = REPO_DIR / f"channels/counters/{CHANNEL_ID}_{MODE}.txt"

    def read_counter():
        try:
            return int(COUNTER_FILE.read_text().strip())
        except Exception:
            return 0

    def write_and_push_counter(idx):
        COUNTER_FILE.write_text(str(idx))
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.name", "modal-bot"], check=True)
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.email", "modal-bot@mahayukti"], check=True)
        subprocess.run(["git", "-C", str(REPO_DIR), "add", str(COUNTER_FILE)], check=True)
        subprocess.run(["git", "-C", str(REPO_DIR), "commit", "-m",
                        f"chore: {CHANNEL_ID} {MODE} counter [skip ci]"], check=True)
        subprocess.run(["git", "-C", str(REPO_DIR), "pull", "--rebase", "origin", "main"], check=True)
        subprocess.run(["git", "-C", str(REPO_DIR), "push"], check=True)

    idx   = read_counter()
    topic = cfg.SHORT_TOPICS[idx % len(cfg.SHORT_TOPICS)]
    print(f"\n📱 SHORT [{idx}]: {topic['name']}")

    # ── Generate script ───────────────────────────────────────────────────────
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
    raw    = resp.content[0].text
    script = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group())
    scenes = script["scenes"]
    print(f"   title: {script['youtube_title']}")
    print(f"   scenes: {len(scenes)}")

    # ── TTS ───────────────────────────────────────────────────────────────────
    print("🎙️  Synthesising audio…")
    WORK      = Path("/tmp/finance_short")
    AUDIO_DIR = WORK / "audio"
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    def ffprobe_duration(path):
        r = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ], capture_output=True, text=True)
        return float(r.stdout.strip())

    async def synth(text, voice, path):
        await edge_tts.Communicate(text, voice).save(str(path))

    for i, scene in enumerate(scenes):
        ap = AUDIO_DIR / f"scene_{i:02d}.mp3"
        asyncio.run(synth(scene["narration"], VOICE, ap))
        scene["audio_path"]     = str(ap)
        scene["actual_duration"] = ffprobe_duration(ap)
        print(f"  [{i}] {scene['actual_duration']:.1f}s — {scene['narration'][:40]}")

    # ── Wan 2.1 video generation ──────────────────────────────────────────────
    print("🎬  Loading ZeroScope v2 576w…")
    CLIPS_DIR = WORK / "clips"
    CLIPS_DIR.mkdir(exist_ok=True)

    from diffusers import TextToVideoSDPipeline
    pipe = TextToVideoSDPipeline.from_pretrained(
        "cerspense/zeroscope_v2_576w", torch_dtype=torch.float16
    )
    pipe.enable_model_cpu_offload()

    NEGATIVE = "text, subtitles, watermark, logo, blurry, low quality, distorted, faces"

    for i, scene in enumerate(scenes):
        clip_path  = CLIPS_DIR / f"clip_{i:02d}.mp4"
        dur        = scene["actual_duration"]
        num_frames = min(24, max(16, int(dur * 8)))
        print(f"  generating clip {i} ({dur:.1f}s → {num_frames} frames)…")
        output = pipe(
            prompt=scene["visual_prompt"], negative_prompt=NEGATIVE,
            height=320, width=576, num_frames=num_frames,
            num_inference_steps=25, guidance_scale=7.5,
        )
        export_to_video(output.frames[0], str(clip_path), fps=8)
        scene["clip_path"] = str(clip_path)
        print(f"    ✓ clip {i} saved")

    # ── FFmpeg compose ────────────────────────────────────────────────────────
    print("🎞️  Composing…")
    COMP_DIR = WORK / "composed"
    SEG_DIR  = COMP_DIR / "segments"
    SEG_DIR.mkdir(parents=True, exist_ok=True)

    def ffmpeg(*args):
        r = subprocess.run(["ffmpeg", "-y"] + list(args), capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"FFmpeg failed:\n{r.stderr[-1500:]}")

    seg_paths = []
    for i, scene in enumerate(scenes):
        seg = SEG_DIR / f"seg_{i:02d}.mp4"
        ffmpeg(
            "-stream_loop", "-1", "-i", scene["clip_path"],
            "-i", scene["audio_path"],
            "-map", "0:v", "-map", "1:a", "-shortest",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-vf", "scale=480:832:force_original_aspect_ratio=increase,crop=480:832",
            str(seg)
        )
        seg_paths.append(seg)

    concat_list = COMP_DIR / "list.txt"
    concat_list.write_text("\n".join(f"file '{p}'" for p in seg_paths))
    raw_video = COMP_DIR / "raw.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(raw_video))

    final_video = COMP_DIR / "final.mp4"
    font        = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    drawtext    = (
        f"fontfile={font}:text='{cfg.CHANNEL_NAME}':"
        f"fontsize=28:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=h-80:"
        f"box=1:boxcolor=0x00C864AA:boxborderw=12"
    )
    ffmpeg("-i", str(raw_video), "-vf", f"drawtext={drawtext}",
           "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "copy", str(final_video))
    print(f"  ✓ composed: {final_video}")

    # ── Upload to YouTube ─────────────────────────────────────────────────────
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
    title   = script["youtube_title"]
    if "#Shorts" not in title:
        title += " #Shorts"

    body = {
        "snippet": {
            "title":       title[:100],
            "description": script["youtube_description"][:5000],
            "tags":        script["tags"][:500],
            "categoryId":  "22",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(final_video), mimetype="video/mp4", resumable=True, chunksize=8*1024*1024)
    req   = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"  uploading… {int(status.progress()*100)}%")

    video_id = response["id"]
    print(f"  ✓ uploaded: https://youtu.be/{video_id}")

    write_and_push_counter(idx + 1)
    print(f"\n✅  Done. Counter → {idx + 1}")


@app.local_entrypoint()
def main():
    run_short.remote()
