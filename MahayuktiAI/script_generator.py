"""
Script generator — viral hooks, Hinglish energy, affiliate CTAs.
"""
import json
import re
import requests
from config import GROQ_API_KEY, ANTHROPIC_API_KEY

_GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.3-70b-versatile"

# Hook templates that actually stop the scroll
_HOOK_STYLES = [
    "Start with a shocking stat: 'X% of Indian [profession] don't know this free AI tool exists...'",
    "Start with FOMO: 'This AI tool is replacing ₹[amount]/month jobs in Indian startups right now'",
    "Start with controversy: 'Forget ChatGPT. For Indians, THIS is actually better — and it's free'",
    "Start with a question: 'Agar aapko [problem] solve karna ho in 5 minutes — kya aap jaante ho kaise?'",
    "Start with a promise: 'I'll show you how to do [task] in under 2 minutes using AI — completely free'",
    "Start with comparison: '[Tool] just made [expensive tool] obsolete for Indian users'",
    "Start with transformation: 'A Mumbai CA used this AI tool to save 3 hours every day — for free'",
]

# Affiliate programs for tools (add more as needed)
_AFFILIATE_HINTS = {
    "Notion":       "notion.so (affiliate: 50% commission — link in bio)",
    "Jasper AI":    "jasper.ai (affiliate: 25% recurring — link in bio)",
    "Copy.ai":      "copy.ai (affiliate: 45% recurring — link in bio)",
    "Writesonic":   "writesonic.com (affiliate: 30% recurring — link in bio)",
    "Grammarly AI": "grammarly.com (affiliate: $20 per signup — link in bio)",
    "Cursor AI":    "cursor.com (affiliate: 20% — link in bio)",
    "Otter.ai":     "otter.ai (affiliate: 20% recurring — link in bio)",
    "Fireflies.ai": "fireflies.ai (affiliate: 20% recurring — link in bio)",
    "Murf AI":      "murf.ai (affiliate: 20% — link in bio)",
    "ElevenLabs":   "elevenlabs.io (affiliate: 22% recurring — link in bio)",
    "HeyGen":       "heygen.com (affiliate: 20% — link in bio)",
    "Descript":     "descript.com (affiliate: 15% — link in bio)",
    "Gamma":        "gamma.app (affiliate: 30% — link in bio)",
    "Make (Integromat)": "make.com (affiliate: 20% recurring — link in bio)",
    "Zapier AI":    "zapier.com (affiliate: 25% — link in bio)",
}


def _call_groq(prompt: str, max_tokens: int = 2000) -> dict:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": _GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85,
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
        try:
            return _call_groq(prompt, max_tokens)
        except Exception as e:
            print(f"  ⚠️  Groq failed ({e}) — falling back to Anthropic")
    return _call_anthropic(prompt, max_tokens)


def generate_short_script(tool: dict) -> dict:
    hook_style = _HOOK_STYLES[hash(tool["name"]) % len(_HOOK_STYLES)]
    affiliate = _AFFILIATE_HINTS.get(tool["name"], "")
    affiliate_note = f"Mention affiliate link opportunity: {affiliate}" if affiliate else ""

    prompt = f"""You are a viral Indian YouTube Shorts creator. Your videos regularly get 500K+ views.
Create a 60-second "AI Tool of the Day" Short about {tool['name']} by {tool['maker']}.

Tool details:
- Category: {tool['category']}
- Pricing: {tool['pricing']}
- India note: {tool['india_note']}

HOOK STYLE: {hook_style}

Rules:
- Script MUST be 115-130 words MAX (exactly 60 seconds of speech)
- Language: Mix of English + Hinglish — make it feel like a smart Indian friend
- HOOK: First 3 seconds must be so compelling the viewer can't scroll away
- Mention India-specific pricing or free availability prominently
- Build FOMO or genuine excitement — this tool should feel like a secret they're learning
- End CTA: "Follow @mahayuktiAI — new AI tool drop every single day"
- {affiliate_note}
- Do NOT mention competitors negatively
- Keep energy HIGH throughout — no boring sentences

Return valid JSON:
{{
  "tool_name": "{tool['name']}",
  "hook": "First 3-second punchy line — MUST stop the scroll",
  "script": "Full 60-second narration (115-130 words, energetic, Hinglish friendly)",
  "slides": [
    {{"text": "{tool['name']}", "label": "AI TOOL OF THE DAY"}},
    {{"text": "What it does — max 10 words", "label": "WHAT IS IT"}},
    {{"text": "Best use case — max 10 words", "label": "BEST USE"}},
    {{"text": "India pricing — max 10 words", "label": "INDIA PRICING"}},
    {{"text": "Follow @mahayuktiAI for daily AI tools", "label": "FOLLOW US"}}
  ],
  "title": "YouTube Shorts title — max 60 chars, include {tool['name']}, add emoji, make it click-worthy",
  "description": "YouTube description — 180 words, include India context, 3 key features, affiliate/pricing info, end with 8 hashtags including #AIIndia #IndianAI #AITool #Shorts",
  "tags": ["AI tools India", "Indian AI", "{tool['name']}", "{tool['category']}", "free AI tools", "AI for Indians", "AI productivity", "mahayuktiAI", "{tool['maker']}", "AI 2025"]
}}"""

    data = _call_llm(prompt, max_tokens=1400)
    data.setdefault("tool_name", tool["name"])
    return data


def generate_long_script(tools: list[dict]) -> dict:
    tools_str = "\n".join(
        f"{i+1}. {t['name']} by {t['maker']} — {t['category']} — {t['pricing']} — India: {t['india_note']}"
        for i, t in enumerate(tools)
    )
    affiliates_note = ", ".join(
        f"{t['name']} (has affiliate program)"
        for t in tools if t["name"] in _AFFILIATE_HINTS
    )

    prompt = f"""You are a top Indian YouTube creator with 500K subscribers in the AI tools space.
Create "Top 5 AI Tools for Indians This Week" — a 9-10 minute video script.

This week's tools:
{tools_str}

{f"Tools with affiliate programs (mention links in description): {affiliates_note}" if affiliates_note else ""}

Rules:
- Total narration: 1350-1500 words (9-10 min at normal pace)
- Language: Primarily English with natural Hinglish phrases — like a knowledgeable Indian tech expert
- Tone: Conversational, opinionated, practical — NOT corporate or robotic
- INTRO: Start with a hook about why these 5 tools matter RIGHT NOW for Indians
- Each tool: ~240 words — what it is, best 3 use cases, India pricing, who should use it TODAY
- Make it feel like insider knowledge — not just a feature list
- Include at least 1 "did you know" fact per tool
- OUTRO: Strong subscribe CTA + tease next week

Return valid JSON:
{{
  "episode_title": "Top 5 AI Tools for Indians This Week — [punchy 4-word theme]",
  "intro_script": "90-second intro — hook + why these tools matter now (200 words)",
  "tools": [
    {{
      "rank": 1,
      "name": "tool name",
      "narration": "240-word narration: what it is, 3 use cases for Indians, India pricing, verdict",
      "key_points": ["Point 1 (max 8 words)", "Point 2 (max 8 words)", "Point 3 (max 8 words)"],
      "india_verdict": "One opinionated sentence — should Indians use this? Why?"
    }}
  ],
  "outro_script": "Subscribe hard-sell + next week tease (120 words)",
  "full_script": "Complete narration: intro + all 5 tools + outro concatenated",
  "title": "YouTube title — max 70 chars, this week context, emoji, click-worthy",
  "description": "250-word YouTube description — timestamps (use 00:00 placeholders), India context, affiliate links note, end with 12 hashtags",
  "tags": ["AI tools India", "Indian AI tools", "top AI tools 2025", "AI for Indians", "free AI tools India", "mahayuktiAI", "AI productivity India", "best AI 2025", "Indian tech", "AI tutorial Hindi", "AI review India", "tech India"]
}}"""

    return _call_llm(prompt, max_tokens=4000)
