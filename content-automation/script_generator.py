import json
import re
from groq import Groq
from config import GROQ_API_KEY, CHANNEL_NAME, CHANNEL_HANDLE

_PAISA_GYAAN_PATTERNS = [
    (re.compile(r"[Pp]aisa\s+[Gg]yaan", re.IGNORECASE), "Mahayukti Finance"),
    (re.compile(r"#PaisaGyaan", re.IGNORECASE), "#MahayuktiFinance"),
    (re.compile(r"paisa_gyaan", re.IGNORECASE), "mahayukti_finance"),
    (re.compile(r"@paisagyaan", re.IGNORECASE), "@mahayuktifinance"),
]


def _scrub(text: str) -> str:
    for pattern, replacement in _PAISA_GYAAN_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _sanitize(data: dict) -> dict:
    """Hard-remove any stray Paisa Gyaan references from all generated fields."""
    for key in ("title", "hook", "script", "description", "thumbnail_text"):
        if isinstance(data.get(key), str):
            data[key] = _scrub(data[key])
    if isinstance(data.get("tags"), list):
        data["tags"] = [_scrub(t) if isinstance(t, str) else t for t in data["tags"]]
    if isinstance(data.get("key_points"), list):
        data["key_points"] = [_scrub(p) if isinstance(p, str) else p for p in data["key_points"]]
    return data


def generate_script(topic: dict) -> dict:
    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""You are the scriptwriter for "{CHANNEL_NAME}" ({CHANNEL_HANDLE}), a YouTube Shorts channel for urban Indians aged 22-40 who want practical, data-driven personal finance advice.

Topic: "{topic['angle']}"
Category: {topic['category']}

⚠️  ABSOLUTE RULE: This channel is MAHAYUKTI FINANCE. The old channel name "Paisa Gyaan" must NEVER appear anywhere. Every CTA must say "Mahayukti Finance ko follow karein." Violation is not acceptable.

Format: YouTube SHORT — strict 60 seconds. Script must be exactly 110-130 words.

Return ONLY valid JSON — no markdown, no backticks, no explanation:

{{
  "title": "Hinglish title max 60 chars. Lead with a number or surprising fact. No fluff.",
  "hook": "Opening line max 15 words — one real data point that stops the scroll instantly.",
  "script": "Voiceover script EXACTLY 110-130 words. Structure: hook (15 words) → 1 key insight with real Indian rupee/% example (60 words) → 1 actionable tip viewer can do today (25 words) → CTA: 'Mahayukti Finance ko follow karein — roz ek finance tip.' Tone: smart Indian friend, not a lecturer. Real data only — LIC, PPF, Zerodha, NSE figures.",
  "key_points": ["Insight max 8 words", "Insight max 8 words", "Insight max 8 words"],
  "description": "100-word YouTube description. Crisp summary, 2-3 takeaways, hashtags: #MahayuktiFinance #Shorts #PersonalFinance #MoneyTips #IndianFinance #PaisaSamjho. End: 'Follow Mahayukti Finance for daily finance tips.'",
  "tags": ["MahayuktiFinance", "Shorts", "PersonalFinance", "MoneyTips", "IndianFinance", "PaisaSamjho", "FinanceTips", "WealthBuilding", "IndianInvestor", "StockMarket", "MutualFunds", "TaxSaving"],
  "thumbnail_text": "ALL CAPS max 4 words for thumbnail"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.65,
        max_tokens=900,
    )

    text = response.choices[0].message.content.strip()
    text = re.sub(r"^```json?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    data = json.loads(text)
    return _sanitize(data)
