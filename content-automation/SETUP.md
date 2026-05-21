# Content Automation — Setup Guide

Fully free pipeline: generates a personal finance Hinglish video daily and uploads it to YouTube automatically.

---

## What You Need (all free)

| Thing | Where to get it | Time |
|---|---|---|
| Google Gemini API key | aistudio.google.com/app/apikey | 2 min |
| Google Cloud project | console.cloud.google.com | 5 min |
| YouTube OAuth credentials | Google Cloud Console | 5 min |
| GitHub repo (this one) | Already have it | — |

---

## Step 1 — Get Gemini API Key (free)

1. Go to **https://aistudio.google.com/app/apikey**
2. Sign in with any Google account
3. Click **Create API key**
4. Copy the key — you'll need it in Step 4

---

## Step 2 — Set Up YouTube API

1. Go to **https://console.cloud.google.com**
2. Create a new project (name it anything, e.g. "Paisa Gyaan")
3. In the left menu: **APIs & Services → Library**
4. Search for **"YouTube Data API v3"** → Enable it
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → OAuth client ID**
7. Application type: **Desktop app**
8. Download the JSON file and rename it to **`client_secret.json`**
9. Place `client_secret.json` in the `content-automation/` folder

> **OAuth consent screen:** If prompted, set it to "External" and add your own Gmail as a test user.

---

## Step 3 — Authorize Your YouTube Channel (one time)

```bash
cd content-automation
pip install -r requirements.txt
python setup_auth.py
```

A browser opens → sign in with the Google account that owns your YouTube channel → Allow.

This creates `youtube_token.json` and prints its contents.

---

## Step 4 — Add GitHub Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

Add these three secrets:

| Secret name | Value |
|---|---|
| `GEMINI_API_KEY` | The key from Step 1 |
| `YOUTUBE_TOKEN_JSON` | The entire JSON printed by setup_auth.py |
| `CHANNEL_NAME` | Your channel name e.g. `Paisa Gyaan` |

---

## Step 5 — Create Your YouTube Channel

1. Go to **youtube.com** → click your profile → **Create a channel**
2. Name it (suggestion: **Paisa Gyaan**, **Rupee Tips**, **Paisa Samjho**)
3. Add a description: "Daily personal finance tips in Hinglish. SIP, stocks, tax saving, insurance — sab kuch simple language mein."
4. Upload a channel banner (use Canva free — search "YouTube channel art finance")

---

## Step 6 — Test Locally

```bash
cd content-automation
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and CHANNEL_NAME
pip install -r requirements.txt
python main.py
```

This will:
- Generate a script via Gemini
- Create a voiceover (en-IN-NeerjaNeural voice)
- Render the video with slides
- Generate a thumbnail
- Upload to YouTube

---

## Step 7 — Enable Daily Auto-Upload

Push your code to GitHub. The GitHub Action runs automatically every day at 8:00 AM IST.

To trigger manually: **GitHub → Actions → Daily Video Generation → Run workflow**

---

## Monetization Roadmap

YouTube requires to join Partner Program:
- **1,000 subscribers** + **4,000 watch hours** in 12 months

How to get there faster:
1. **Consistency** — automation handles this, 1 video/day
2. **Good titles** — the script generator writes clickable Hinglish titles
3. **Cross-post Shorts** — take the best 60 seconds and repost as a Short
4. **Community posts** — once you hit 500 subs, post daily finance tips as text
5. **Descriptions + tags** — already optimized by the pipeline

Realistic timeline with daily uploads: **3-5 months** to monetization threshold.

After monetization, typical CPM for Indian finance = Rs. 80–200 per 1,000 views.

---

## Customizing Content

Edit `topics.py` to add your own topic angles.

Change the voice in `audio_generator.py`:
- `en-IN-NeerjaNeural` — female English India (default, best for Hinglish)
- `en-IN-PrabhatNeural` — male English India
- `hi-IN-SwaraNeural` — female Hindi (for pure Hindi content)

Change colors in `config.py` to match your channel branding.
