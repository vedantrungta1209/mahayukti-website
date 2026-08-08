#!/usr/bin/env python3
"""One-off introductory X post for the @wearemahayukti account launch."""

import os, requests, base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

X_API_KEY             = os.environ["X_API_KEY"]
X_API_SECRET          = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN        = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]
ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]

NAVY  = (11, 27, 58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (6, 15, 35)


def generate_intro_tweet():
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "messages": [{
                "role": "user",
                "content": """Write an introductory X/Twitter post for @wearemahayukti — Mahayukti's official account just launched on X.

Mahayukti is India's vetted professional advisory network. When you have a complex problem needing deep expertise — legal, financial, tech, cybersecurity, medical, or intelligence — Mahayukti connects you to the exact verified specialist for that need.

Requirements:
- Max 260 characters (count carefully)
- Announce the account launch on X
- One punchy line on what Mahayukti does
- End with mahayukti.com
- Max 2 hashtags: #Mahayukti #IndiaExperts
- No fluff, no emojis
- Sound like a real founding team, not a brand account

Respond with ONLY the tweet text, nothing else."""
            }]
        },
        timeout=30,
    )
    r.raise_for_status()
    tweet = r.json()["content"][0]["text"].strip().strip('"')
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    print(f"Tweet ({len(tweet)} chars):\n{tweet}\n")
    return tweet


def generate_intro_image():
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), NAVY)
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(height):
        t = y / height
        r = int(NAVY[0] + (DARK[0] - NAVY[0]) * t)
        g = int(NAVY[1] + (DARK[1] - NAVY[1]) * t)
        b = int(NAVY[2] + (DARK[2] - NAVY[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Brand bars
    draw.rectangle([(0, 0), (width, 6)], fill=GOLD)
    draw.rectangle([(0, height - 6), (width, height)], fill=GOLD)
    draw.rectangle([(0, 0), (5, height)], fill=GOLD)

    # Load fonts
    def font(size, bold=False):
        paths = [
            f"/System/Library/Fonts/Helvetica.ttc",
            f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        ]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default()

    # Header
    draw.rectangle([(0, 6), (width, int(height * 0.18))], fill=(6, 15, 35))
    draw.rectangle([(0, int(height * 0.18) - 3), (width, int(height * 0.18))], fill=GOLD)
    draw.text((40, int(height * 0.025)), "MAHAYUKTI", fill=GOLD, font=font(44, bold=True))
    draw.text((40, int(height * 0.080)), "India's Expert Advisory Network", fill=LIGHT, font=font(28))

    # Now on X badge
    badge = "NOW ON X"
    b_font = font(26, bold=True)
    b_bbox = draw.textbbox((0, 0), badge, font=b_font)
    bw, bh = b_bbox[2] - b_bbox[0] + 28, b_bbox[3] - b_bbox[1] + 14
    bx = width - 40 - bw
    by = int(height * 0.22)
    draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=bh // 2, fill=GOLD)
    draw.text((bx + 14, by + 7), badge, fill=(0, 0, 0), font=b_font)

    # Main headline
    headline = "INDIA'S EXPERTS,\nNOW ON X."
    h_font = font(88, bold=True)
    y = int(height * 0.36)
    for line in headline.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=h_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=h_font)
        draw.text((x, y), line, fill=WHITE, font=h_font)
        y += int(height * 0.115)

    # Gold rule
    draw.rectangle([(width // 2 - 80, y + 16), (width // 2 + 80, y + 20)], fill=GOLD)
    y += 52

    # Subtext
    sub = "Follow @wearemahayukti"
    s_font = font(36)
    s_bbox = draw.textbbox((0, 0), sub, font=s_font)
    draw.text(((width - (s_bbox[2] - s_bbox[0])) // 2, y), sub, fill=LIGHT, font=s_font)
    y += int(height * 0.075)

    sub2 = "Describe your problem → Get the exact expert"
    s2_font = font(28)
    s2_bbox = draw.textbbox((0, 0), sub2, font=s2_font)
    draw.text(((width - (s2_bbox[2] - s2_bbox[0])) // 2, y), sub2, fill=GOLD, font=s2_font)

    # Footer
    footer_y = height - int(height * 0.06)
    draw.text((40, footer_y), "mahayukti.com", fill=GOLD, font=font(28, bold=True))

    path = "/tmp/mahayukti_x_intro.jpg"
    img.save(path, "JPEG", quality=95)
    print(f"✅ Image saved: {path}")
    return path


def post_tweet(tweet_text, image_path):
    from requests_oauthlib import OAuth1
    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)

    # Upload image
    print("Uploading image...")
    with open(image_path, "rb") as f:
        r = requests.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            files={"media": f},
            auth=auth,
            timeout=60,
        )
    r.raise_for_status()
    media_id = r.json()["media_id_string"]
    print(f"  Media ID: {media_id}")

    # Post tweet
    print("Posting tweet...")
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": tweet_text, "media": {"media_ids": [media_id]}},
        auth=auth,
        timeout=30,
    )
    if r.ok:
        tweet_id = r.json().get("data", {}).get("id", "")
        print(f"✅ Posted: https://x.com/wearemahayukti/status/{tweet_id}")
    else:
        print(f"❌ Failed ({r.status_code}): {r.text}")


if __name__ == "__main__":
    tweet = generate_intro_tweet()
    image = generate_intro_image()
    post_tweet(tweet, image)
