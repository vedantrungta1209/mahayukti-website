#!/usr/bin/env python3
"""
MahaYukti Telegram broadcast module.
Sends posts to the Mahayukti Telegram channel.

Requires two GitHub secrets:
  TELEGRAM_BOT_TOKEN  — from @BotFather on Telegram
  TELEGRAM_CHANNEL_ID — the channel username (@MahayuktiOfficial) or numeric ID (-100xxxxxxxxx)

Setup (one-time, user action required):
  1. Message @BotFather on Telegram → /newbot → get the token
  2. Create a public Telegram channel (e.g. @MahayuktiOfficial)
  3. Add the bot as Admin to the channel with "Post Messages" permission
  4. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID to GitHub secrets
"""

import os, requests
from pathlib import Path

TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def is_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID)


def post_photo(caption: str, image_path: str) -> bool:
    """Post an image with caption to the channel."""
    if not is_configured():
        print("⚠️  Telegram not configured — skipping (add TELEGRAM_BOT_TOKEN + TELEGRAM_CHANNEL_ID secrets)")
        return False
    # Telegram caption limit is 1024 chars
    caption_trimmed = caption[:1020] + "…" if len(caption) > 1024 else caption
    with open(image_path, "rb") as f:
        r = requests.post(
            f"{_API}/sendPhoto",
            data={"chat_id": TELEGRAM_CHANNEL_ID, "caption": caption_trimmed, "parse_mode": "HTML"},
            files={"photo": f},
            timeout=60,
        )
    if r.ok:
        print(f"✅ Telegram photo posted (msg_id: {r.json().get('result', {}).get('message_id')})")
        return True
    print(f"⚠️  Telegram photo failed ({r.status_code}): {r.text[:300]}")
    return False


def post_text(text: str) -> bool:
    """Post a text-only message (for news pulse, long-form)."""
    if not is_configured():
        print("⚠️  Telegram not configured — skipping")
        return False
    # Telegram text limit: 4096 chars
    text_trimmed = text[:4090] + "…" if len(text) > 4096 else text
    r = requests.post(
        f"{_API}/sendMessage",
        json={"chat_id": TELEGRAM_CHANNEL_ID, "text": text_trimmed, "parse_mode": "HTML",
              "disable_web_page_preview": False},
        timeout=30,
    )
    if r.ok:
        print(f"✅ Telegram message posted (msg_id: {r.json().get('result', {}).get('message_id')})")
        return True
    print(f"⚠️  Telegram message failed ({r.status_code}): {r.text[:300]}")
    return False


def post_photo_url(caption: str, image_url: str) -> bool:
    """Post an image via URL (when local path not available)."""
    if not is_configured():
        print("⚠️  Telegram not configured — skipping")
        return False
    caption_trimmed = caption[:1020] + "…" if len(caption) > 1024 else caption
    r = requests.post(
        f"{_API}/sendPhoto",
        json={"chat_id": TELEGRAM_CHANNEL_ID, "photo": image_url,
              "caption": caption_trimmed, "parse_mode": "HTML"},
        timeout=30,
    )
    if r.ok:
        print(f"✅ Telegram photo (URL) posted")
        return True
    print(f"⚠️  Telegram photo URL failed ({r.status_code}): {r.text[:300]}")
    return False
