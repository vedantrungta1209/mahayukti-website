"""
Pexels b-roll fetcher — downloads real footage for each channel/topic.
Caches clips locally to avoid re-downloading. Requires PEXELS_API_KEY.
Falls back to Pollinations static image if Pexels fails.
"""
import hashlib
import os
import subprocess
from pathlib import Path
from urllib.parse import quote

import requests

_CACHE_DIR = Path(__file__).parent / "broll_cache"
_PEXELS_BASE = "https://api.pexels.com/videos/search"
_PHOTOS_BASE = "https://api.pexels.com/v1/search"


def _pexels_key() -> str:
    return os.environ.get("PEXELS_API_KEY", "")


def _cache_key(query: str, portrait: bool, idx: int) -> str:
    tag = hashlib.md5(f"{query}:{portrait}:{idx}".encode()).hexdigest()[:12]
    return tag


def _download_video(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=60, stream=True)
        if r.status_code == 200:
            dest.write_bytes(r.content)
            return True
    except Exception as e:
        print(f"  Download error: {e}")
    return False


def _trim_to_duration(src: str, dst: str, duration: float) -> bool:
    """Trim or loop a video clip to exact duration."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-stream_loop", "-1",          # loop if source is shorter
        "-i", src,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-an",                          # no audio from b-roll
        dst,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0


def _resize_clip(src: str, dst: str, width: int, height: int) -> bool:
    """Resize and crop a clip to target dimensions."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", src,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,"
               f"crop={width}:{height}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-an", dst,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0


def fetch_broll_clip(
    query: str,
    duration: float,
    width: int,
    height: int,
    idx: int = 0,
) -> str | None:
    """
    Fetch a Pexels video clip matching the query, resized to target dimensions.
    Returns path to the ready-to-use clip, or None if unavailable.
    """
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        return None

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    orientation = "portrait" if height > width else "landscape"
    cache_id = _cache_key(query, height > width, idx)
    final_path = _CACHE_DIR / f"{cache_id}_{int(duration)}s.mp4"

    if final_path.exists():
        print(f"  B-roll cache hit: {query}")
        return str(final_path)

    try:
        r = requests.get(
            _PEXELS_BASE,
            headers={"Authorization": key},
            params={
                "query": query,
                "per_page": 10,
                "orientation": orientation,
                "size": "medium",
            },
            timeout=20,
        )
        if not r.ok:
            print(f"  Pexels API error {r.status_code}")
            return None

        videos = r.json().get("videos", [])
        if not videos:
            print(f"  No Pexels results for: {query}")
            return None

        # Pick video at idx (rotate through results for variety)
        video = videos[idx % len(videos)]

        # Find best quality file close to target resolution
        files = video.get("video_files", [])
        best = None
        for f in sorted(files, key=lambda x: x.get("width", 0), reverse=True):
            if f.get("width", 0) >= 720:
                best = f
                break
        if not best and files:
            best = files[0]
        if not best:
            return None

        raw_path = _CACHE_DIR / f"{cache_id}_raw.mp4"
        if not _download_video(best["link"], raw_path):
            return None

        resized_path = _CACHE_DIR / f"{cache_id}_resized.mp4"
        if not _resize_clip(str(raw_path), str(resized_path), width, height):
            return None

        if not _trim_to_duration(str(resized_path), str(final_path), duration):
            return None

        # Cleanup intermediates
        raw_path.unlink(missing_ok=True)
        resized_path.unlink(missing_ok=True)

        print(f"  B-roll downloaded: '{query}' ({duration:.1f}s)")
        return str(final_path)

    except Exception as e:
        print(f"  Pexels error: {e}")
        return None


# Per-channel/topic search query builder
_CHANNEL_BASE_QUERIES = {
    "hustle":   ["freelancer working laptop india", "entrepreneur hustle success", "money income earning india"],
    "business": ["startup office india", "corporate meeting business", "entrepreneur pitch investor india"],
    "crime":    ["dark city night india dramatic", "police investigation crime", "financial fraud documents"],
    "mind":     ["meditation india calm", "brain psychology therapy", "woman thinking emotions india"],
    "kanoon":   ["indian court law justice", "lawyer legal documents india", "scales justice india"],
    "speak":    ["english learning student india", "teacher classroom india", "confident presentation speaking"],
    "swasth":   ["yoga wellness india healthy", "doctor patient india", "healthy food nutrition india"],
}

_SLIDE_LABEL_QUERIES = {
    "STEP 1":            "getting started work laptop",
    "STEP 2":            "progress action doing",
    "STEP 3":            "success achievement result",
    "WHAT IS IT":        "explanation concept explain",
    "BEST USE":          "using laptop smartphone app",
    "INDIA PRICING":     "indian money rupee payment phone",
    "EARNING POTENTIAL": "money income success india",
    "WHERE TO START":    "smartphone app marketplace india",
    "TODAY'S LESSON":    "student learning classroom india",
    "COMMON MISTAKE":    "confused thinking mistake",
    "CORRECT FORM":      "correct right success thumbs up",
    "PSYCHOLOGY FACT":   "brain thinking mind psychology",
    "THE SCIENCE":       "science research brain neurons",
    "IN YOUR LIFE":      "person thinking everyday life india",
    "KEY INSIGHT":       "insight idea lightbulb thinking",
    "KNOW YOUR RIGHTS":  "indian court law rights",
    "TRUE CRIME INDIA":  "crime investigation dark india",
    "FOLLOW US":         "social media subscribe phone",
}


def get_broll_query(channel_id: str, label: str, topic: str) -> str:
    """Return best Pexels search query for a given slide label and topic."""
    if label in _SLIDE_LABEL_QUERIES:
        return _SLIDE_LABEL_QUERIES[label]
    base = _CHANNEL_BASE_QUERIES.get(channel_id, ["india people work"])
    import hashlib
    idx = int(hashlib.md5(topic.encode()).hexdigest()[:4], 16) % len(base)
    return base[idx] + f" {topic[:20]}"
