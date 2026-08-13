#!/usr/bin/env python3
"""
Cross-post the Mahayukti manifesto thread to LinkedIn, Facebook, and Instagram.
One-shot — guard file prevents double-posting.
"""

import os, base64, io, time, requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ANTHROPIC_API_KEY         = os.environ["ANTHROPIC_API_KEY"]
LINKEDIN_ACCESS_TOKEN     = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN       = os.environ.get("LINKEDIN_AUTHOR_URN", "")
MAKE_LINKEDIN_WEBHOOK_URL = os.environ.get("MAKE_LINKEDIN_WEBHOOK_URL", "")
IMGBB_API_KEY             = os.environ.get("IMGBB_API_KEY", "")
FB_PAGE_ACCESS_TOKEN      = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID                = os.environ.get("FB_PAGE_ID", "")
IG_USER_ID                = os.environ.get("IG_USER_ID", "")

GUARD    = Path(__file__).parent / "_manifesto_crosspost_posted.txt"
IMG_PATH = "/tmp/mahayukti_manifesto.jpg"

# The X thread root tweet — shown in all captions
THREAD_URL = "https://x.com/wearemahayukti/status/2087856650279387253"

# Brand colours
NAVY  = (11, 27, 58)
GOLD  = (201, 148, 58)
WHITE = (255, 255, 255)
LIGHT = (220, 220, 230)
DARK  = (6, 15, 35)
RED   = (180, 30, 30)


# ── Image ─────────────────────────────────────────────────────────────────────

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


def _wrap(draw, text, font, max_w):
    words  = text.split()
    lines  = []
    line   = ""
    for word in words:
        test = (line + " " + word).strip()
        bb   = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def generate_image() -> str:
    W, H = 1080, 1080
    img  = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(H):
        t = y / H
        c = tuple(int(NAVY[i] + (DARK[i] - NAVY[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c)

    # Gold accent lines
    draw.rectangle([(0, 0),    (W, 6)],   fill=GOLD)
    draw.rectangle([(0, H-6),  (W, H)],   fill=GOLD)
    draw.rectangle([(0, 0),    (5, H)],   fill=GOLD)

    # Header bar
    draw.rectangle([(0, 6), (W, int(H * 0.16))], fill=DARK)
    draw.rectangle([(0, int(H * 0.16) - 3), (W, int(H * 0.16))], fill=GOLD)
    draw.text((40, int(H * 0.022)), "MAHAYUKTI", fill=GOLD, font=_font(44, bold=True))
    draw.text((40, int(H * 0.077)), "Make India Greatest", fill=LIGHT, font=_font(28))

    # Warning badge top-right
    badge  = "STAY ALERT"
    b_font = _font(24, bold=True)
    bb     = draw.textbbox((0, 0), badge, font=b_font)
    bw, bh = bb[2] - bb[0] + 28, bb[3] - bb[1] + 14
    bx     = W - 40 - bw
    by     = int(H * 0.19)
    draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=bh // 2, fill=RED)
    draw.text((bx + 14, by + 7), badge, fill=WHITE, font=b_font)

    # Main headline
    headline_lines = ["IF AN ENEMY", "WANTED", "REGIME CHANGE", "IN INDIA…"]
    h_font = _font(78, bold=True)
    y      = int(H * 0.22)
    for line in headline_lines:
        bb = draw.textbbox((0, 0), line, font=h_font)
        x  = (W - (bb[2] - bb[0])) // 2
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=h_font)
        draw.text((x, y),         line, fill=WHITE,     font=h_font)
        y += int(H * 0.099)

    # Gold divider
    y += 8
    draw.rectangle([(W//2 - 100, y), (W//2 + 100, y + 4)], fill=GOLD)
    y += 28

    # Sub-line
    sub      = "It wouldn't invade our borders first."
    sub_font = _font(30)
    sb       = draw.textbbox((0, 0), sub, font=sub_font)
    draw.text(((W - (sb[2] - sb[0])) // 2, y), sub, fill=LIGHT, font=sub_font)
    y += int(H * 0.065)

    sub2 = "It would enter your mind."
    sb2  = draw.textbbox((0, 0), sub2, font=_font(30, bold=True))
    draw.text(((W - (sb2[2] - sb2[0])) // 2, y), sub2, fill=GOLD, font=_font(30, bold=True))
    y += int(H * 0.10)

    # Footer
    draw.text((40, H - int(H * 0.06)), "@wearemahayukti  |  mahayukti.com", fill=GOLD, font=_font(26, bold=True))

    img.save(IMG_PATH, "JPEG", quality=95)
    print(f"✅ Image saved: {IMG_PATH}")
    return IMG_PATH


# ── imgbb upload ───────────────────────────────────────────────────────────────

def upload_imgbb(path: str) -> str | None:
    if not IMGBB_API_KEY:
        print("⚠️  No IMGBB_API_KEY — Instagram will be skipped")
        return None
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = requests.post("https://api.imgbb.com/1/upload",
                      data={"key": IMGBB_API_KEY, "image": b64}, timeout=30)
    if r.ok:
        url = r.json()["data"]["url"]
        print(f"  imgbb: {url}")
        return url
    print(f"  imgbb failed: {r.status_code} {r.text[:200]}")
    return None


# ── Caption generation ─────────────────────────────────────────────────────────

def generate_captions() -> dict:
    system = """\
You write for @wearemahayukti — India's Make India Greatest movement.
Voice: Sharp, India-first, non-partisan, constructive. No party names. No cynicism.
Today is August 13, 2026 — Parliament's Monsoon Session just adjourned sine die.
The thread being cross-posted is a 15-tweet manifesto about hybrid warfare, information
operations, and the 12-step regime-change playbook being studied and used against
democracies like India. The manifesto ends with Mahayukti's mission as the counter-narrative."""

    tasks = {
        "linkedin": f"""\
Write a LinkedIn post to accompany the Mahayukti manifesto on hybrid warfare.

CONTEXT:
- We just published a 15-tweet thread on X (@wearemahayukti) breaking down the 12-step
  hybrid warfare / regime change playbook used against democracies
- Parliament's Monsoon Session 2026 adjourned sine die today (Aug 13)
- The content is about cognitive security, information warfare, national resilience
- LinkedIn audience: policy professionals, India watchers, strategists, founders, senior executives

REQUIREMENTS:
- 250-320 words
- Open with a strong hook — not "Excited to share" or "We just posted"
- Summarise the core insight in 2-3 paras: why this matters, what the playbook is, why India specifically
- Quote 2-3 of the sharpest lines from the thread naturally
- End with Mahayukti's mission as the answer: "This is why Mahayukti exists..."
- Include the X thread link: {THREAD_URL}
- End with these hashtags exactly (on a new line after the body):
  #HybridWarfare #InformationWarfare #NationalSecurity #India #GeopoliticalAwareness #CognitiveSecurity #IndiaFirst #MakeIndiaGreatest #Mahayukti #ViksitBharat #India2047

Respond with ONLY the post text (including hashtags). No subject line. No preamble.""",

        "facebook": f"""\
Write a Facebook post to cross-promote the Mahayukti manifesto thread.

CONTEXT:
- 15-tweet X thread just posted: a sharp, accessible breakdown of the hybrid warfare / regime
  change playbook — how enemies enter your mind before your borders
- Parliament's Monsoon Session adjourned today
- Facebook audience: general Indian citizens, middle-class, educated but not necessarily policy professionals

REQUIREMENTS:
- 150-200 words
- Conversational, accessible — feel like a thoughtful Indian sharing something important
- Key message: "If you can recognise the pattern, you become the firewall"
- Include the X thread link: {THREAD_URL}
- End with hashtags (new line):
  #India #Bharat #NationalSecurity #HybridWarfare #MakeIndiaGreatest #Mahayukti #IndiaFirst #StayAlert

Respond with ONLY the post text (including hashtags). No preamble.""",

        "instagram": f"""\
Write an Instagram caption for the Mahayukti manifesto post.

CONTEXT:
- Visual post about hybrid warfare and regime change playbook
- The manifesto starts: "If an enemy wanted regime change in India, it wouldn't invade our borders first. It would enter your mind."
- Today: Parliament Monsoon Session 2026 adjourned sine die (Aug 13)

REQUIREMENTS:
- 80-120 words
- First line is the scroll-stopper — make it land hard
- Distil the 12-step playbook into 2-3 punchy lines
- End with: "Thread on X → link in bio" and "Follow @wearemahayukti for more"
- Hashtags (final line, all on one line):
  #India #Bharat #HybridWarfare #InformationWarfare #NationalSecurity #IndiaFirst #MakeIndiaGreatest #Mahayukti #CognitiveSecurity #IndiaGeopolitics #StayAlert #ViksitBharat #IndiaRising

Respond with ONLY the caption text (including hashtags). No preamble.""",
    }

    captions = {}
    for key, prompt in tasks.items():
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":         ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type":      "application/json",
                },
                json={
                    "model":      "claude-sonnet-4-6",
                    "max_tokens": 600,
                    "system":     system,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"].strip().strip('"')
            captions[key] = text
            print(f"\n--- {key.upper()} ({len(text)} chars) ---\n{text}\n")
        except Exception as e:
            print(f"❌ Caption generation failed for {key}: {e}")
            captions[key] = ""
    return captions


# ── LinkedIn ───────────────────────────────────────────────────────────────────

def post_linkedin(text: str, image_path: str, image_url: str | None):
    if not text:
        print("⚠️  LinkedIn skipped — no caption")
        return

    # Try Make.com webhook first
    if MAKE_LINKEDIN_WEBHOOK_URL:
        payload = {
            "linkedin_text": text,
            "title":         "The 12-Step Playbook Against India",
            "image_url":     image_url or "",
        }
        r = requests.post(MAKE_LINKEDIN_WEBHOOK_URL, json=payload, timeout=30)
        if r.ok:
            print("✅ LinkedIn posted via Make.com")
            return
        print(f"⚠️  Make.com failed ({r.status_code}): {r.text[:200]} — trying direct API")

    # Direct LinkedIn API
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_AUTHOR_URN:
        print("⚠️  LinkedIn skipped — credentials missing")
        return

    headers = {
        "Authorization":               f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "LinkedIn-Version":            "202310",
        "X-Restli-Protocol-Version":   "2.0.0",
        "Content-Type":                "application/json",
    }

    # Upload image
    try:
        init = requests.post(
            "https://api.linkedin.com/rest/images?action=initializeUpload",
            headers=headers,
            json={"initializeUploadRequest": {"owner": LINKEDIN_AUTHOR_URN}},
            timeout=30,
        )
        init.raise_for_status()
        val = init.json()["value"]
        with open(image_path, "rb") as f:
            requests.put(val["uploadUrl"], data=f, headers={
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type":  "application/octet-stream",
            }, timeout=60).raise_for_status()
        img_id = val["image"]

        requests.post(
            "https://api.linkedin.com/rest/posts",
            headers=headers,
            json={
                "author":        LINKEDIN_AUTHOR_URN,
                "commentary":    text,
                "visibility":    "PUBLIC",
                "distribution":  {
                    "feedDistribution":            "MAIN_FEED",
                    "targetEntities":              [],
                    "thirdPartyDistributionChannels": [],
                },
                "content": {"media": {"title": "The 12-Step Playbook Against India", "id": img_id}},
                "lifecycleState":            "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            },
            timeout=30,
        ).raise_for_status()
        print("✅ LinkedIn posted via direct API")
    except Exception as e:
        print(f"❌ LinkedIn direct API failed: {e}")


# ── Facebook ───────────────────────────────────────────────────────────────────

def post_facebook(text: str, image_path: str):
    if not text or not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️  Facebook skipped — missing credentials or caption")
        return
    try:
        img_obj = Image.open(image_path).convert("RGB")
        img_obj.thumbnail((1080, 1080), Image.LANCZOS)
        buf = io.BytesIO()
        img_obj.save(buf, "JPEG", quality=82, optimize=True)
        buf.seek(0)
        r = requests.post(
            f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos",
            files={"source": ("photo.jpg", buf, "image/jpeg")},
            data={"caption": text, "access_token": FB_PAGE_ACCESS_TOKEN},
            timeout=60,
        )
        if r.ok:
            print("✅ Facebook posted")
        else:
            err = r.json().get("error", {}) if "json" in r.headers.get("content-type", "") else {}
            print(f"⚠️  Facebook failed ({r.status_code}): {err.get('message', r.text[:200])}")
    except Exception as e:
        print(f"❌ Facebook error: {e}")


# ── Instagram ──────────────────────────────────────────────────────────────────

def _ig_publish_with_retry(cid: str):
    time.sleep(20)
    for attempt in range(4):
        pub = requests.post(
            f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media_publish",
            data={"creation_id": cid, "access_token": FB_PAGE_ACCESS_TOKEN},
            timeout=30,
        )
        if pub.ok:
            print("✅ Instagram posted")
            return
        subcode = pub.json().get("error", {}).get("error_subcode") if pub.headers.get("content-type", "").startswith("application/json") else None
        if subcode in (2207025, 2207006) and attempt < 3:
            print(f"   IG container processing (attempt {attempt+1}), retrying in 20s…")
            time.sleep(20)
            continue
        print(f"⚠️  Instagram publish failed ({pub.status_code}): {pub.text[:200]}")
        return
    print("⚠️  Instagram container never ready")


def post_instagram(text: str, image_url: str | None):
    if not text or not FB_PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("⚠️  Instagram skipped — missing credentials or caption")
        return
    if not image_url:
        print("⚠️  Instagram skipped — no public image URL (imgbb key missing?)")
        return
    try:
        r = requests.post(
            f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media",
            data={
                "image_url":    image_url,
                "caption":      text,
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
            timeout=30,
        )
        r.raise_for_status()
        cid = r.json()["id"]
        _ig_publish_with_retry(cid)
    except Exception as e:
        print(f"❌ Instagram error: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if GUARD.exists():
        print(f"⏸️  Already cross-posted — guard file exists.")
        return

    print("🇮🇳 MahaYukti Manifesto Cross-Post\n" + "─" * 50)

    print("\n[1/4] Generating branded image...")
    generate_image()

    print("\n[2/4] Uploading to imgbb for public URL...")
    image_url = upload_imgbb(IMG_PATH)

    print("\n[3/4] Generating platform captions via Claude...")
    captions = generate_captions()

    print("\n[4/4] Posting to platforms...")

    print("\n— LinkedIn —")
    post_linkedin(captions.get("linkedin", ""), IMG_PATH, image_url)
    time.sleep(5)

    print("\n— Facebook —")
    post_facebook(captions.get("facebook", ""), IMG_PATH)
    time.sleep(5)

    print("\n— Instagram —")
    post_instagram(captions.get("instagram", ""), image_url)

    GUARD.write_text("done")
    print("\n✅ Cross-post complete.")


if __name__ == "__main__":
    main()
