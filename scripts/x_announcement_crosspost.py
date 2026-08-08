#!/usr/bin/env python3
"""
Cross-post the Mahayukti X launch announcement to LinkedIn, Facebook, and Instagram.
Also post a tweet linking all Mahayukti social profiles.
One-shot — run once via GitHub Actions workflow_dispatch.
"""

import os, base64, io, requests
from PIL import Image, ImageDraw, ImageFont

ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
MAKE_LINKEDIN_WEBHOOK_URL = os.environ.get("MAKE_LINKEDIN_WEBHOOK_URL", "")
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN   = os.environ.get("LINKEDIN_AUTHOR_URN", "")
FB_PAGE_ACCESS_TOKEN  = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID            = os.environ.get("FB_PAGE_ID", "")
IG_USER_ID            = os.environ.get("IG_USER_ID", "")
IMGBB_API_KEY         = os.environ.get("IMGBB_API_KEY", "")
X_API_KEY             = os.environ.get("X_API_KEY", "")
X_API_SECRET          = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN        = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

NAVY  = (11, 27, 58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (6, 15, 35)

SOCIAL_LINKS = {
    "x":        "x.com/wearemahayukti",
    "linkedin": "linkedin.com/company/mahayukti",
    "instagram":"instagram.com/mahayukti.advisory",
    "facebook": "facebook.com/MahaYuktiAdvisory",
    "website":  "mahayukti.com",
}


def _font(size, bold=False):
    paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_image() -> str:
    W, H = 1080, 1080
    img  = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Gradient
    for y in range(H):
        t = y / H
        c = tuple(int(NAVY[i] + (DARK[i] - NAVY[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c)

    # Brand border
    draw.rectangle([(0, 0), (W, 6)],   fill=GOLD)
    draw.rectangle([(0, H-6), (W, H)], fill=GOLD)
    draw.rectangle([(0, 0), (5, H)],   fill=GOLD)

    # Header bar
    draw.rectangle([(0, 6), (W, int(H * 0.18))], fill=DARK)
    draw.rectangle([(0, int(H * 0.18) - 3), (W, int(H * 0.18))], fill=GOLD)
    draw.text((40, int(H * 0.025)), "MAHAYUKTI", fill=GOLD, font=_font(44, bold=True))
    draw.text((40, int(H * 0.080)), "India's Expert Advisory Network", fill=LIGHT, font=_font(28))

    # NOW ON X badge
    badge  = "NOW ON X"
    b_font = _font(26, bold=True)
    bb     = draw.textbbox((0, 0), badge, font=b_font)
    bw, bh = bb[2] - bb[0] + 28, bb[3] - bb[1] + 14
    bx     = W - 40 - bw
    by     = int(H * 0.22)
    draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=bh // 2, fill=GOLD)
    draw.text((bx + 14, by + 7), badge, fill=(0, 0, 0), font=b_font)

    # Main headline
    headline = "FIND US\nEVERYWHERE."
    h_font = _font(88, bold=True)
    y = int(H * 0.34)
    for line in headline.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=h_font)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=h_font)
        draw.text((x, y), line, fill=WHITE, font=h_font)
        y += int(H * 0.115)

    # Gold divider
    draw.rectangle([(W//2 - 80, y + 16), (W//2 + 80, y + 20)], fill=GOLD)
    y += 56

    # Platform list
    platforms = [
        ("X",         "@wearemahayukti"),
        ("LinkedIn",  "linkedin.com/company/mahayukti"),
        ("Instagram", "@mahayukti.advisory"),
        ("Facebook",  "facebook.com/MahaYuktiAdvisory"),
    ]
    p_font  = _font(28)
    lbl_fnt = _font(28, bold=True)
    row_gap = int(H * 0.068)
    for platform, handle in platforms:
        lbl_bb = draw.textbbox((0, 0), f"{platform}: ", font=lbl_fnt)
        draw.text((80, y), f"{platform}: ", fill=GOLD, font=lbl_fnt)
        draw.text((80 + lbl_bb[2] - lbl_bb[0], y), handle, fill=LIGHT, font=p_font)
        y += row_gap

    # Footer
    draw.text((40, H - int(H * 0.06)), "mahayukti.com", fill=GOLD, font=_font(28, bold=True))

    path = "/tmp/mahayukti_x_crosspost.jpg"
    img.save(path, "JPEG", quality=95)
    print(f"✅ Image saved: {path}")
    return path


def _upload_imgbb(image_path: str) -> str | None:
    if not IMGBB_API_KEY:
        return None
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = requests.post("https://api.imgbb.com/1/upload",
                      data={"key": IMGBB_API_KEY, "image": b64}, timeout=30)
    if r.ok:
        url = r.json()["data"]["url"]
        print(f"  imgbb URL: {url}")
        return url
    print(f"  imgbb failed: {r.status_code} {r.text[:200]}")
    return None


def generate_captions() -> dict:
    system = """You are the founding team of Mahayukti posting the announcement that we are now live on X (@wearemahayukti).
Write in a warm, direct, genuinely human voice — no corporate jargon, no AI phrases.
We are a movement: Make India Greatest. India's best experts, now connected and accessible."""

    prompts = {
        "linkedin": f"""Write a LinkedIn post announcing that Mahayukti is now on X (Twitter) at @wearemahayukti.

Tone: Professional but warm. Founders talking to their network.
Include:
- The announcement (we're on X)
- What Mahayukti does in one punchy line
- All our platforms: x.com/wearemahayukti | instagram.com/mahayukti.advisory | facebook.com/MahaYuktiAdvisory | mahayukti.com
- Max 3 hashtags: #Mahayukti #MakeIndiaGreatest #IndiaExperts
- No emojis unless one or two feel natural
- 150-200 words max

Respond with ONLY the post text.""",

        "facebook": f"""Write a Facebook post announcing Mahayukti is now on X at @wearemahayukti.

Tone: Warm, accessible, talking to a broad Indian audience.
Include:
- The launch announcement
- What Mahayukti is (India's expert advisory network — connecting people to verified specialists)
- Invite them to follow on X: x.com/wearemahayukti
- Mention LinkedIn too: linkedin.com/company/mahayukti
- Website: mahayukti.com
- 2-3 hashtags max
- 100-150 words

Respond with ONLY the post text.""",

        "instagram": f"""Write an Instagram caption announcing Mahayukti's launch on X (@wearemahayukti).

Tone: Sharp, energetic, India-first.
Include:
- We're on X now — follow @wearemahayukti
- One line on what Mahayukti does
- Cross-promote: LinkedIn at linkedin.com/company/mahayukti
- 4-6 hashtags: #Mahayukti #IndiaExperts #MakeIndiaGreatest and 2-3 more relevant ones
- Under 120 words

Respond with ONLY the caption text.""",

        "x_profiles": f"""Write a tweet (max 260 chars) listing all Mahayukti social profiles.

Profiles to include:
- LinkedIn: linkedin.com/company/mahayukti
- Instagram: @mahayukti.advisory
- Facebook: facebook.com/MahaYuktiAdvisory
- Website: mahayukti.com

Tone: Direct, not a press release. Like a real person sharing their links.
No fluff. #Mahayukti hashtag at the end.
Count characters carefully — must be under 280 total.

Respond with ONLY the tweet text.""",
    }

    captions = {}
    for key, prompt in prompts.items():
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 400,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"].strip().strip('"')
        captions[key] = text
        print(f"\n--- {key.upper()} ({len(text)} chars) ---\n{text}\n")
    return captions


def post_to_linkedin(text: str, image_path: str, image_url: str | None):
    if MAKE_LINKEDIN_WEBHOOK_URL:
        payload = {"linkedin_text": text, "title": "Mahayukti is now on X", "image_url": image_url or ""}
        r = requests.post(MAKE_LINKEDIN_WEBHOOK_URL, json=payload, timeout=30)
        if r.ok:
            print("✅ LinkedIn posted via Make.com")
            return
        print(f"⚠️  Make.com failed ({r.status_code}): {r.text[:200]}")

    if LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN:
        headers = {
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "LinkedIn-Version": "202310",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        init = requests.post(
            "https://api.linkedin.com/rest/images?action=initializeUpload",
            headers=headers,
            json={"initializeUploadRequest": {"owner": LINKEDIN_AUTHOR_URN}},
        )
        init.raise_for_status()
        val = init.json()["value"]
        with open(image_path, "rb") as f:
            requests.put(val["uploadUrl"], data=f,
                         headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                                  "Content-Type": "application/octet-stream"}).raise_for_status()
        requests.post(
            "https://api.linkedin.com/rest/posts",
            headers=headers,
            json={
                "author": LINKEDIN_AUTHOR_URN,
                "commentary": text,
                "visibility": "PUBLIC",
                "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                                 "thirdPartyDistributionChannels": []},
                "content": {"media": {"title": "Mahayukti is now on X", "id": val["image"]}},
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            },
        ).raise_for_status()
        print("✅ LinkedIn posted via direct API")
        return

    print("⚠️  LinkedIn skipped — credentials missing")


def post_to_facebook(text: str, image_path: str):
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️  Facebook credentials missing — skipping")
        return
    img_obj = Image.open(image_path).convert("RGB")
    img_obj.thumbnail((1080, 1080), Image.LANCZOS)
    buf = io.BytesIO()
    img_obj.save(buf, "JPEG", quality=82, optimize=True)
    buf.seek(0)
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos",
        files={"source": ("photo.jpg", buf, "image/jpeg")},
        data={"caption": text, "access_token": FB_PAGE_ACCESS_TOKEN},
    )
    if r.ok:
        print("✅ Facebook posted")
    else:
        err = r.json().get("error", {}) if "json" in r.headers.get("content-type", "") else {}
        print(f"⚠️  Facebook failed ({r.status_code}): {err.get('message', r.text[:200])}")


def _ig_publish_with_retry(cid: str, initial_wait=15, max_attempts=4, retry_wait=20):
    import time
    time.sleep(initial_wait)
    for attempt in range(max_attempts):
        pub = requests.post(
            f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media_publish",
            data={"creation_id": cid, "access_token": FB_PAGE_ACCESS_TOKEN},
        )
        if pub.ok:
            print("✅ Instagram posted")
            return
        data    = pub.json() if "json" in pub.headers.get("content-type", "") else {}
        subcode = data.get("error", {}).get("error_subcode")
        if subcode in (2207025, 2207006) and attempt < max_attempts - 1:
            print(f"   IG container processing (attempt {attempt+1}), retrying in {retry_wait}s…")
            time.sleep(retry_wait)
            continue
        print(f"⚠️  Instagram publish failed ({pub.status_code}): {pub.text[:200]}")
        return
    print("⚠️  Instagram container never ready")


def post_to_instagram(text: str, image_url: str | None):
    if not FB_PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("⚠️  Instagram credentials missing — skipping")
        return
    if not image_url:
        print("⚠️  No public image URL for Instagram — skipping (need imgbb)")
        return
    r = requests.post(
        f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media",
        data={"image_url": image_url, "caption": text, "access_token": FB_PAGE_ACCESS_TOKEN},
    )
    r.raise_for_status()
    cid = r.json()["id"]
    _ig_publish_with_retry(cid)


def post_profiles_tweet(text: str):
    if not X_API_KEY:
        print("⚠️  X credentials missing — skipping profile tweet")
        return
    from requests_oauthlib import OAuth1
    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    r = requests.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text[:280]},
        auth=auth,
        timeout=30,
    )
    if r.ok:
        tid = r.json().get("data", {}).get("id", "")
        print(f"✅ Profile links tweet: https://x.com/wearemahayukti/status/{tid}")
    else:
        print(f"⚠️  X tweet failed ({r.status_code}): {r.text[:300]}")


def main():
    print("Generating captions via Claude...")
    captions = generate_captions()

    print("\nGenerating cross-post image...")
    image_path = generate_image()

    print("\nUploading image to imgbb for public URL...")
    image_url = _upload_imgbb(image_path)

    print("\n--- Posting to LinkedIn ---")
    post_to_linkedin(captions["linkedin"], image_path, image_url)

    print("\n--- Posting to Facebook ---")
    post_to_facebook(captions["facebook"], image_path)

    print("\n--- Posting to Instagram ---")
    post_to_instagram(captions["instagram"], image_url)

    print("\n--- Tweeting social profile links ---")
    post_profiles_tweet(captions["x_profiles"])

    print("\n✅ Cross-post complete.")


if __name__ == "__main__":
    main()
