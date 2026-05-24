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

    prompt = f"""You are a senior financial analyst and head scriptwriter for "{CHANNEL_NAME}" ({CHANNEL_HANDLE}), a professional Indian personal finance YouTube channel that helps urban Indians make informed, data-driven financial decisions.

Topic: "{topic['angle']}"
Category: {topic['category']}

⚠️  ABSOLUTE RULE: This channel is MAHAYUKTI FINANCE. The old channel name "Paisa Gyaan" must NEVER appear anywhere — not in the script, description, tags, or any field. Every CTA must say "Mahayukti Finance ko subscribe karein." Violation of this rule is not acceptable.

Write a complete, professional video package in HINGLISH (sophisticated Hindi-English mix in Roman script).
Target audience: Urban Indians aged 22-40 who are serious about building long-term wealth.
Script length: ~850-950 words (6-7 minutes at a measured, authoritative pace).

Return ONLY valid JSON — no markdown, no backticks, no explanation:

{{
  "title": "Professional YouTube title in Hinglish, max 70 chars. Lead with a specific number or insight. Compelling but never sensationalist.",
  "hook": "One authoritative opening statement with a real data point, max 20 words. No hyperbole.",
  "script": "Full voiceover script. Authoritative Hinglish tone — like a SEBI-registered financial advisor who speaks plainly. Open with a concrete real-world statistic. Structure: strong data-led opening → clear problem or concept → 5-7 well-explained actionable points with specific Indian rupee examples → honest trade-off or risk disclaimer → professional CTA: 'Mahayukti Finance ko subscribe karein aur notification bell on karein — financial clarity ke liye.'",
  "key_points": ["Concise insight max 12 words", "Concise insight max 12 words", "Concise insight max 12 words", "Concise insight max 12 words", "Concise insight max 12 words", "Concise insight max 12 words"],
  "description": "YouTube description, 200 words. Professional tone. Summarise the video, list key takeaways, add timestamps for each section, include relevant hashtags: #MahayuktiFinance #PaisaSamjho #PersonalFinance #MoneyTips #FinancialPlanning. End with: 'Subscribe to Mahayukti Finance for expert personal finance guidance.'",
  "tags": ["MahayuktiFinance", "mahayukti", "PaisaSamjho", "PersonalFinance", "FinancialPlanning", "MoneyTips", "IndianFinance", "WealthBuilding", "tag9", "tag10", "tag11", "tag12", "tag13", "tag14", "tag15"],
  "thumbnail_text": "Short punchy ALL CAPS text for thumbnail, max 5 words, no channel names"
}}

Script quality standards:
- Authoritative, not sensationalist — no "crorepati ban jao", "secret trick", "guaranteed returns"
- Real data: cite actual figures — "Nifty 50 ka 20-year CAGR 14.5% raha hai", "RBI ne repo rate 6.5% rakha hai"
- Nuanced: acknowledge risks and trade-offs honestly — viewers should trust you, not just like you
- Structured: clear transitions between each point, professional signposting
- Practical: every video should leave viewers with 2-3 things they can do this week
- Culturally authentic: real Indian examples — LIC, PPF, Zerodha, NSE, Indian tax slabs
- Mix Hindi and English naturally for educated Indian professionals"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.65,
        max_tokens=2500,
    )

    text = response.choices[0].message.content.strip()
    text = re.sub(r"^```json?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    data = json.loads(text)
    return _sanitize(data)
