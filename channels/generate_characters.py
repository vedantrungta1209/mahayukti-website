#!/usr/bin/env python3
"""
Generate AI character avatars for all 7 Mahayukti channel hosts.
Uses Pollinations.ai (free, no key) with Flux model for photorealistic Indian faces.
Saves to channels/characters/ and pushes to GitHub.
D-ID can then use the raw GitHub URL as character source.

Usage:
  python3 generate_characters.py
  python3 generate_characters.py --channel hustle
"""
import argparse
import io
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image

CHARACTERS = {
    "hustle": {
        "name": "Raj",
        "prompt": (
            "hyperrealistic portrait photograph of a 27-year-old indian man, "
            "short neat hair, slight stubble, confident friendly smile, "
            "wearing a modern dark navy half-sleeve shirt, "
            "against a blurred warm bokeh background, "
            "soft studio lighting, DSLR quality, sharp focus on face, "
            "cinematic portrait photography"
        ),
    },
    "business": {
        "name": "Arjun",
        "prompt": (
            "hyperrealistic portrait photograph of a 35-year-old sharp indian man, "
            "clean shaven, intelligent analytical expression, "
            "crisp white formal shirt open collar, "
            "dark blurred modern office background, "
            "professional headshot lighting, DSLR quality, confident look"
        ),
    },
    "crime": {
        "name": "Vikram",
        "prompt": (
            "hyperrealistic portrait photograph of a 40-year-old indian man, "
            "serious intense expression, short dark hair with slight grey, "
            "dark formal shirt, dramatic moody dark background, "
            "cinematic low-key lighting, investigative journalist vibe, "
            "DSLR portrait, authoritative look"
        ),
    },
    "mind": {
        "name": "Priya",
        "prompt": (
            "hyperrealistic portrait photograph of a 32-year-old indian woman, "
            "warm empathetic smile, dark hair tied back, "
            "wearing a light teal professional top, "
            "soft warm blurred background, approachable therapist vibe, "
            "soft natural studio lighting, DSLR quality portrait"
        ),
    },
    "kanoon": {
        "name": "Advocate Sharma",
        "prompt": (
            "hyperrealistic portrait photograph of a 45-year-old distinguished indian man, "
            "formal dark suit and tie, authoritative dignified expression, "
            "slight grey at temples, blurred law library background, "
            "classic professional lighting, DSLR portrait, "
            "experienced lawyer appearance"
        ),
    },
    "speak": {
        "name": "Neha",
        "prompt": (
            "hyperrealistic portrait photograph of a 28-year-old indian woman, "
            "friendly encouraging smile, dark hair loose, "
            "wearing a bright white professional top, "
            "clean light classroom or studio background, "
            "soft natural daylight, approachable English teacher vibe, "
            "DSLR portrait quality"
        ),
    },
    "swasth": {
        "name": "Dr. Anjali",
        "prompt": (
            "hyperrealistic portrait photograph of a 38-year-old indian woman doctor, "
            "warm caring smile, neat hair tied back, "
            "wearing a white doctor coat over a teal scrub, "
            "clean light medical or wellness background, "
            "bright professional lighting, DSLR portrait, "
            "trustworthy health professional look"
        ),
    },
}

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
CHARACTERS_DIR    = Path(__file__).parent / "characters"
GH_REPO           = "vedantrungta1209/mahayukti-website"
GH_BRANCH         = "main"
RAW_BASE          = f"https://raw.githubusercontent.com/{GH_REPO}/{GH_BRANCH}/channels/characters"


def _generate_avatar(channel: str, char: dict, retries: int = 3) -> Image.Image | None:
    prompt = (
        char["prompt"]
        + " --no text no watermark no logo no writing no glasses no hat realistic skin texture"
    )
    encoded = quote(prompt)
    # Use different seeds to get variety; pick the best one
    import hashlib
    seed = int(hashlib.md5(channel.encode()).hexdigest()[:8], 16) % 999999

    url = (
        f"{POLLINATIONS_BASE}/{encoded}"
        f"?width=512&height=512&seed={seed}&nologo=true&model=flux&enhance=true"
    )
    print(f"  Generating {char['name']} ({channel})...")
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                print(f"  ✅ {char['name']} generated ({img.size})")
                return img
            print(f"  Attempt {attempt + 1} failed: HTTP {r.status_code}")
        except Exception as e:
            print(f"  Attempt {attempt + 1} error: {e}")
        if attempt < retries - 1:
            time.sleep(5)
    return None


def _save_and_push(channel: str, img: Image.Image) -> str:
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHARACTERS_DIR / f"{channel}.jpg"
    # Save at high quality, suitable for D-ID
    img.save(path, "JPEG", quality=95)
    print(f"  Saved → {path}")
    return str(path)


def _update_config_url(channel: str) -> None:
    config_path = Path(__file__).parent / "configs" / f"{channel}.py"
    if not config_path.exists():
        print(f"  ⚠️  Config not found: {config_path}")
        return
    content = config_path.read_text()
    raw_url  = f"{RAW_BASE}/{channel}.jpg"
    # Replace the empty CHARACTER_IMAGE_URL
    if 'CHARACTER_IMAGE_URL = ""' in content:
        content = content.replace(
            'CHARACTER_IMAGE_URL = ""',
            f'CHARACTER_IMAGE_URL = "{raw_url}"',
        )
        config_path.write_text(content)
        print(f"  ✅ CHARACTER_IMAGE_URL set → {raw_url}")
    elif raw_url in content:
        print(f"  Already set: {raw_url}")
    else:
        print(f"  ⚠️  Could not auto-update config — set manually: {raw_url}")


def _git_push(paths: list[str]) -> None:
    print("\n  Committing character images to GitHub...")
    repo_root = str(Path(__file__).parent.parent)
    def git(*args):
        return subprocess.run(["git", "-C", repo_root] + list(args),
                               check=True, capture_output=True)
    git("add", *paths)
    git("add", "channels/configs/")
    result = subprocess.run(["git", "-C", repo_root, "diff", "--staged", "--quiet"],
                             capture_output=True)
    if result.returncode == 0:
        print("  Nothing to commit (all images already up to date).")
        return
    git("commit", "-m", "feat(characters): add AI host avatars for all 7 channels [skip ci]")
    git("pull", "--rebase", "origin", "main")
    git("push", "origin", "main")
    print("  ✅ Pushed to GitHub — D-ID character URLs are now live.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", choices=list(CHARACTERS.keys()),
                        help="Generate for one channel only")
    args = parser.parse_args()

    targets = {args.channel: CHARACTERS[args.channel]} if args.channel else CHARACTERS

    saved_paths = []
    for channel, char in targets.items():
        print(f"\n{'='*50}")
        img = _generate_avatar(channel, char)
        if img:
            path = _save_and_push(channel, img)
            saved_paths.append(path)
            _update_config_url(channel)
        else:
            print(f"  ❌ Failed to generate avatar for {channel}")
        time.sleep(2)  # be polite to Pollinations

    if saved_paths:
        _git_push(saved_paths)

    print("\n" + "="*50)
    print("✅ Character generation complete!")
    print("\nRaw GitHub URLs (for D-ID):")
    for channel in targets:
        print(f"  {channel}: {RAW_BASE}/{channel}.jpg")
    print("\nD-ID will use these URLs automatically on the next video run.")


if __name__ == "__main__":
    main()
