import json
import re
import requests
from config import GROQ_API_KEY, ANTHROPIC_API_KEY

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.3-70b-versatile"


def _call_groq(prompt: str, max_tokens: int = 2000) -> dict:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": _GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.75,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(_GROQ_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    return json.loads(raw)


def _call_anthropic(prompt: str, max_tokens: int = 2000) -> dict:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    text = r.json()["content"][0]["text"]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group()) if match else {}


def _call_llm(prompt: str, max_tokens: int = 2000) -> dict:
    if GROQ_API_KEY:
        return _call_groq(prompt, max_tokens)
    return _call_anthropic(prompt, max_tokens)


def generate_short_script(tool: dict) -> dict:
    prompt = f"""You are a YouTube Shorts creator for Mahayukti AI — an Indian AI education channel.
Create a 60-second "AI Tool of the Day" script about {tool['name']} by {tool['maker']}.

Tool details:
- Category: {tool['category']}
- Pricing: {tool['pricing']}
- India note: {tool['india_note']}

Rules:
- Script MUST be 120-135 words MAX (60 seconds of speech)
- Language: Mostly English, Hinglish hook is fine
- Tone: Energetic, practical, no fluff — like a smart friend sharing a tip
- Always mention India-specific pricing or availability
- End with "Follow @mahayuktiAI for daily AI tools"

Return valid JSON:
{{
  "tool_name": "{tool['name']}",
  "hook": "First 5-second punchy line to stop the scroll",
  "script": "Full 60-second narration (120-135 words max)",
  "slides": [
    {{"text": "slide 1 text (8 words max)", "label": "TOOL OF THE DAY"}},
    {{"text": "slide 2 text — what it does (10 words max)", "label": "WHAT IS IT"}},
    {{"text": "slide 3 text — top use (10 words max)", "label": "BEST USE"}},
    {{"text": "slide 4 text — India pricing (10 words max)", "label": "INDIA PRICING"}},
    {{"text": "Follow @mahayuktiAI for daily AI tools", "label": "FOLLOW US"}}
  ],
  "title": "YouTube Shorts title (max 60 chars, include tool name and emoji)",
  "description": "YouTube description (150 words, include 5 hashtags at end)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"]
}}"""

    data = _call_llm(prompt, max_tokens=1200)
    data.setdefault("tool_name", tool["name"])
    return data


def generate_long_script(tools: list[dict]) -> dict:
    tools_str = "\n".join(
        f"{i+1}. {t['name']} by {t['maker']} — {t['category']} — {t['pricing']} — India: {t['india_note']}"
        for i, t in enumerate(tools)
    )

    prompt = f"""You are a YouTube creator for Mahayukti AI — an Indian AI education channel.
Create a script for "Top 5 AI Tools for Indians This Week" — a 9-10 minute video.

This week's tools:
{tools_str}

Rules:
- Total narration: 1400-1600 words (9-10 minutes at normal speaking pace)
- Language: Mostly English, some Hinglish is fine
- Tone: Knowledgeable, practical, conversational — like an Indian tech expert
- Each tool section: ~250 words
- Always mention India-specific pricing, availability, and use cases
- End with CTA to subscribe to @mahayuktiAI

Return valid JSON:
{{
  "episode_title": "Top 5 AI Tools for Indians This Week — [short theme]",
  "intro_script": "60-second intro narration (150 words)",
  "tools": [
    {{
      "rank": 1,
      "name": "tool name",
      "narration": "250-word narration covering what it is, top 3 uses, India pricing, who should use it",
      "key_points": ["Point 1 (max 8 words)", "Point 2 (max 8 words)", "Point 3 (max 8 words)"],
      "india_verdict": "One sentence India verdict"
    }}
  ],
  "outro_script": "60-second outro narration with subscribe CTA (150 words)",
  "full_script": "Complete concatenated narration intro + all tools + outro",
  "title": "YouTube title (max 70 chars, include week context and emoji)",
  "description": "YouTube description (250 words, timestamps placeholder, hashtags)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12"]
}}"""

    return _call_llm(prompt, max_tokens=3500)
