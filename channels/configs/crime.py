"""
Mahayukti Crime (@mahayuktikrime) — true crime India, long-form + trailer Shorts.
2 Long-form/week + 1 Short trailer per long video.
"""
import json
import os
import re
import requests

CHANNEL_ID     = "crime"
CHANNEL_NAME   = "Mahayukti Crime"
CHANNEL_HANDLE = "@mahayuktikrime"
TOKEN_ENV_VAR  = "YOUTUBE_CRIME_TOKEN_JSON"
TOKEN_FILE     = "crime_token.json"
SECRET_NAME    = "YOUTUBE_CRIME_TOKEN_JSON"

# ── AI Character ─────────────────────────────────────────────────────────
CHARACTER_NAME      = "Vikram"
CHARACTER_BIO       = "40-year-old investigative journalist from Delhi who has covered financial frauds, murders and political scams for 15 years. Has personal contacts inside CBI and ED."
CHARACTER_STYLE     = "Measured, dramatic, authoritative. Like a documentary narrator with insider knowledge. Builds tension slowly. Uses short punchy sentences for impact."
CHARACTER_IMAGE_URL = "https://raw.githubusercontent.com/vedantrungta1209/mahayukti-website/main/channels/characters/crime.jpg"

ELEVENLABS_VOICE_ID = "VR6AewLTigWG4xSOukaG"   # Arnold — deep dramatic male

SHORT_VOICE = "en-IN-PrabhatNeural"
LONG_VOICE  = "en-IN-PrabhatNeural"

SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
LONG_WIDTH   = 1280
LONG_HEIGHT  = 720
FPS          = 24
OUTPUT_DIR   = "output"

BG_COLOR      = (8, 2, 2)
BG_COLOR_2    = (20, 4, 4)
PRIMARY_COLOR = (180, 20, 20)
ACCENT_COLOR  = (255, 60, 60)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (160, 100, 100)

BOLD_FONT_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
REGULAR_FONT_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

CATEGORY_PALETTES = {
    "Financial Fraud": ((8, 5, 2),   (20, 10, 4),  (200, 100, 0),  (255, 180, 0)),
    "Cyber Crime":     ((2, 5, 12),  (4, 10, 25),  (0, 100, 255),  (50, 180, 255)),
    "Murder":          ((10, 2, 2),  (25, 4, 4),   (180, 20, 20),  (255, 60, 60)),
    "Corporate Crime": ((5, 5, 2),   (10, 10, 4),  (150, 150, 0),  (220, 220, 0)),
    "Terrorism":       ((5, 2, 8),   (10, 4, 20),  (120, 0, 180),  (180, 60, 255)),
    "Political Scam":  ((2, 8, 5),   (4, 20, 10),  (0, 150, 80),   (0, 220, 130)),
    "General":         ((8, 2, 2),   (20, 4, 4),   (180, 20, 20),  (255, 60, 60)),
}

CTA_LINE1  = "Follow for"
CTA_LINE2  = "true crime stories"
CTA_SUBTEXT = "New crime story every week"

LONG_INTRO_BADGE = "TRUE CRIME INDIA"
OUTRO_LINE1      = "Subscribe for more!"
OUTRO_LINE2      = "New crime story every week"
OUTRO_BELL_TEXT  = "Ring the bell — new story every Tue & Sat"

LONG_ALSO_GENERATES_SHORT = True

AFFILIATE_PROGRAMS = [
    {"name": "True Crime Obsessed (Patreon model)", "commission": "₹99-499/month membership", "link_placeholder": "https://www.patreon.com/mahayuktikrime"},
    {"name": "Audible India",  "commission": "₹200 per free trial signup",         "link_placeholder": "https://www.amazon.in/b?ie=UTF8&node=12279858031&tag=YOUR-TAG"},
    {"name": "Zee5 Premium",   "commission": "₹100-300 per subscription",          "link_placeholder": "https://www.zee5.com/affiliate"},
    {"name": "VPN (ExpressVPN)","commission": "$13 USD per signup",                 "link_placeholder": "https://www.expressrefer.com/refer-a-friend/30-days-free?referrer_id=YOUR_ID"},
    {"name": "True Crime Books (Amazon Associates)", "commission": "8% on books",  "link_placeholder": "https://www.amazon.in/s?k=true+crime+india&linkCode=ll2&tag=YOUR-TAG"},
]


def bg_prompt(category: str, topic_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Financial Fraud": f"broken bank vault money scattered dark moody red gold {orientation} cinematic no text no people",
        "Cyber Crime":     f"dark web computer screen glowing blue hacker digital crime {orientation} cinematic no text no people",
        "Murder":          f"crime scene police tape dark shadowy corridor red black {orientation} cinematic no text no people",
        "Corporate Crime": f"empty boardroom shredded documents dark corporate shadows {orientation} cinematic no text no people",
        "Terrorism":       f"dark city night rain dramatic shadows tension suspense {orientation} cinematic no text no people",
        "Political Scam":  f"parliament steps dark night dramatic lighting shadows political {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"crime thriller dark india shadows red moody dramatic {orientation} cinematic no text no people")


LONG_TOPICS = [
    {"name": "The Harshad Mehta Scam — India's ₹5,000 Crore Stock Market Fraud", "category": "Financial Fraud", "era": "1992", "key_figures": "Harshad Mehta, Sucheta Dalal, ready forward deals"},
    {"name": "Nirav Modi Diamond Heist — How He Stole ₹13,578 Crore from PNB", "category": "Financial Fraud", "era": "2018", "key_figures": "Nirav Modi, Mehul Choksi, LoU fraud"},
    {"name": "2G Spectrum Scam — India's ₹1.76 Lakh Crore Telecom Robbery", "category": "Political Scam", "era": "2008", "key_figures": "A Raja, Kanimozhi, Raja's ministry"},
    {"name": "Satyam Scandal — India's Enron Moment", "category": "Corporate Crime", "era": "2009", "key_figures": "Ramalinga Raju, inflated accounts, ₹7,136 crore fraud"},
    {"name": "Sheena Bora Murder Case — The Family That Shocked India", "category": "Murder", "era": "2015", "key_figures": "Indrani Mukerjea, Peter Mukerjea, Peter Indrani Peter's media empire"},
    {"name": "PMC Bank Fraud — How ₹6,500 Crore Disappeared", "category": "Financial Fraud", "era": "2019", "key_figures": "HDIL loans, Joy Thomas, fake accounts"},
    {"name": "Vijay Mallya — The Kingfisher King Who Fled India with ₹9,000 Crore", "category": "Financial Fraud", "era": "2016", "key_figures": "Kingfisher Airlines, 17 banks, ED CBI fugitive"},
    {"name": "IL&FS Crisis — India's Shadow Banking Collapse", "category": "Financial Fraud", "era": "2018", "key_figures": "₹91,000 crore debt default, Ravi Parthasarathy"},
    {"name": "Jamtara — India's Cyber Crime Capital That Defrauded Millions", "category": "Cyber Crime", "era": "2010-present", "key_figures": "OTP fraud, SIM card scam, phishing networks"},
    {"name": "NSEL Commodity Exchange Fraud — ₹5,600 Crore Vanished", "category": "Financial Fraud", "era": "2013", "key_figures": "Jignesh Shah, FTIL, warehouse fraud"},
    {"name": "Commonwealth Games Scam — How India's Biggest Sporting Event Was Looted", "category": "Political Scam", "era": "2010", "key_figures": "Suresh Kalmadi, ₹70,000 crore event, overpriced contracts"},
    {"name": "Mewat Cyber Crime Network — The WhatsApp Honeytrap Gang", "category": "Cyber Crime", "era": "2020-present", "key_figures": "WhatsApp video call traps, extortion, 1000+ villages"},
    {"name": "The Dark Truth Behind Indian Fake News Factories", "category": "Cyber Crime", "era": "2019-present", "key_figures": "Alt News expose, political propaganda factories"},
    {"name": "Punjab National Bank Fraud — Diamond Merchants vs Bankers", "category": "Financial Fraud", "era": "2018", "key_figures": "Letters of Undertaking, SWIFT bypass, overseas banks"},
    {"name": "Aadarsh Society Scam — How Army Heroes Looted War Widows", "category": "Political Scam", "era": "2010", "key_figures": "Mumbai 36-floor building, Kargil martyr widows, politicians"},
    {"name": "Bhopal Gas Tragedy — The Corporate Crime India Never Got Justice For", "category": "Corporate Crime", "era": "1984", "key_figures": "Union Carbide, Warren Anderson, 3,787+ dead, compensation failure"},
    {"name": "Ketan Parekh Stock Scam — The Man Who Crashed the BSE", "category": "Financial Fraud", "era": "2001", "key_figures": "K-10 stocks, bank loans, ₹1,250 crore manipulation"},
    {"name": "India's ₹500 Crore Crypto Scam — The WazirX Hack Story", "category": "Cyber Crime", "era": "2024", "key_figures": "WazirX, ₹2,000 crore stolen, North Korea connection"},
    {"name": "Yes Bank Crisis — How India's Fastest Growing Bank Almost Died", "category": "Financial Fraud", "era": "2020", "key_figures": "Rana Kapoor, ₹50,000 crore NPA, RBI takeover"},
    {"name": "Agusta Westland Helicopter Scam — ₹3,600 Crore Defence Bribe", "category": "Political Scam", "era": "2010", "key_figures": "AgustaWestland, Michel Haschke, Air Chief Marshal"},
    {"name": "Operation Cobra — India's Largest Drug Bust Network", "category": "General", "era": "2020-present", "key_figures": "₹12,000 crore drugs, narco-terror network, ports"},
    {"name": "The Delhi Gang Rape That Changed India's Rape Laws", "category": "Murder", "era": "2012", "key_figures": "Nirbhaya, Justice Verma Committee, death sentence"},
    {"name": "Neeraj Grover Murder Case — The Actor Who Was Never Found Whole", "category": "Murder", "era": "2008", "key_figures": "Maria Susairaj, Emile Jerome, 300+ pieces"},
    {"name": "Stock Market IPO Scam — How Retail Investors Are Still Getting Looted", "category": "Financial Fraud", "era": "2023-2024", "key_figures": "Grey market premium, ring leaders, SEBI action"},
    {"name": "Sahara Group Fraud — The Biggest Ever SEBI Case", "category": "Corporate Crime", "era": "2012", "key_figures": "Subrata Roy, ₹24,000 crore investor deposits, Supreme Court"},
]


LONG_PROMPT_TEMPLATE = """You are India's most gripping true crime narrator — think Scam 1992 documentary style.
Create a complete true crime episode: "{name}"

Era: {era}
Key figures/facts: {key_figures}

Rules:
- Total narration: 1200-1500 words (12-15 min at measured, dramatic pace)
- Language: English with occasional Hindi phrases for drama
- Structure: Cold open → Background → The Crime → Unraveling → Investigation → Verdict/Status → Impact
- Use REAL names, dates, amounts, court judgements where available
- Build dramatic tension — this should feel like a Netflix documentary
- Include human impact — how many people were affected, how their lives changed
- Be factual and fair — state what is proved vs. alleged
- End with: current status of case + broader lesson for Indians

Return valid JSON:
{{
  "episode_title": "{name}",
  "intro_script": "200-word cold open — start at the most dramatic moment, create instant intrigue",
  "items": [
    {{
      "rank": 1,
      "name": "chapter title (e.g. 'The Setup', 'The Crime', 'The Unraveling', 'The Verdict')",
      "narration": "250-300 word dramatic narrative with real facts and timeline",
      "key_points": ["Key fact 1", "Key fact 2", "Key fact 3"],
      "summary": "One-line chapter summary",
      "category": "{category}"
    }}
  ],
  "outro_script": "100-word reflection on the case + subscribe CTA",
  "full_script": "Complete narration: cold open + all chapters + outro concatenated",
  "title": "YouTube title — max 70 chars, true crime hook, emoji",
  "description": "300-word description — case summary, timeline, 12 hashtags #TrueCrimeIndia #IndianCrime #CrimeStory",
  "tags": ["true crime india", "indian crime stories", "crime documentary india", "{name}", "mahayuktikrime", "scam india", "fraud india", "crime india 2025", "investigation india", "court case india", "news india crime", "hindi crime story"]
}}"""


def generate_trailer_script(long_script: dict) -> dict:
    """Generate a cliffhanger short trailer from the long crime video script."""
    groq_key      = os.environ.get("GROQ_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    full_script = long_script.get("full_script", "")[:2000]
    episode_title = long_script.get("episode_title", "")
    tags = long_script.get("tags", [])

    prompt = f"""You are creating a 30-second cliffhanger trailer for a true crime YouTube Short.
Long video: "{episode_title}"
Opening of the full story: {full_script[:800]}

Create a 30-second hook that:
- Opens with the most shocking fact from the story
- Builds to a cliffhanger: "Agle 2 minute mein suno kya hua..."
- Language: Hinglish — dramatic, suspenseful
- End: "Full story on @mahayuktikrime — link in bio"
- Script MUST be 60-70 words MAX

Return valid JSON:
{{
  "topic_name": "{episode_title} — Trailer",
  "script": "60-70 word dramatic cliffhanger narration",
  "slides": [
    {{"text": "BREAKING CRIME STORY", "label": "TRUE CRIME INDIA"}},
    {{"text": "{episode_title[:30]}...", "label": "STORY"}},
    {{"text": "Agle 2 minute mein suno...", "label": "CLIFFHANGER"}},
    {{"text": "Full story on @mahayuktikrime", "label": "WATCH NOW"}}
  ],
  "title": "Short trailer title — 50 chars max, shocking hook",
  "description": "Watch the full story on @mahayuktikrime — Link in bio #TrueCrimeIndia #Shorts",
  "tags": {json.dumps(tags[:8] + ["Shorts", "TrueCrimeIndia"])}
}}"""

    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.9,
            "max_tokens": 800,
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    if r.ok:
        data = json.loads(r.json()["choices"][0]["message"]["content"])
        data["category"] = "General"
        return data

    return {
        "topic_name": f"Trailer: {episode_title}",
        "script": f"Suno yeh crime story — {episode_title}. Full kahani @mahayuktikrime pe. Subscribe karo.",
        "slides": [{"text": episode_title[:30], "label": "TRUE CRIME"}],
        "title": f"Trailer: {episode_title[:40]} #Shorts",
        "description": "Watch the full story on @mahayuktikrime",
        "tags": ["true crime india", "Shorts"],
        "category": "General",
    }
