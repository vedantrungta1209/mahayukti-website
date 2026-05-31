"""
Script generator — Claude Sonnet 4.6 primary (world-class writing quality).
Groq Llama 3.3 as rate-limit fallback only.
"""
import json
import os
import re
import time
import requests


_GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL    = "llama-3.3-70b-versatile"
_CLAUDE_URL    = "https://api.anthropic.com/v1/messages"
_CLAUDE_MODEL  = "claude-sonnet-4-6"   # world-class writing, not Haiku

_QUALITY_SYSTEM = """You are an elite Indian content creator and scriptwriter.
Your videos have crossed 10M+ views. Your writing philosophy:
- Every sentence either teaches something, creates emotion, or drives action. No filler.
- Language is natural spoken Hinglish (for Indian channels) or crisp English — never stiff, never AI-sounding.
- Specificity beats vagueness: "₹47,000 in 23 days" beats "earn good money".
- Numbers, examples, and names make abstract advice real.
- The hook must be so good that skipping feels like a mistake.
- Calls to action feel earned, not forced.
You ALWAYS return valid JSON and nothing else."""


def _call_claude(prompt: str, anthropic_key: str, max_tokens: int = 2000) -> dict:
    for attempt in range(2):
        r = requests.post(
            _CLAUDE_URL,
            headers={
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "system": _QUALITY_SYSTEM,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=180,
        )
        r.raise_for_status()
        stop_reason = r.json().get("stop_reason", "")
        text = r.json()["content"][0]["text"]
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise ValueError("No JSON object found in Claude response")
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            if attempt == 0 and stop_reason == "max_tokens":
                # Response was truncated — retry with more tokens
                print(f"  Claude response truncated (max_tokens={max_tokens}), retrying with +1000…")
                max_tokens = max_tokens + 1000
                continue
            raise
    return {}


def _call_groq(prompt: str, groq_key: str, max_tokens: int = 2000) -> dict:
    r = requests.post(
        _GROQ_URL,
        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
        json={
            "model": _GROQ_MODEL,
            "messages": [
                {"role": "system", "content": _QUALITY_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.82,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        },
        timeout=90,
    )
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])


def _llm(prompt: str, cfg, max_tokens: int = 2000) -> dict:
    """Claude Sonnet first (quality), Groq as fallback (rate-limit resilience)."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", getattr(cfg, "ANTHROPIC_API_KEY", ""))
    groq_key      = os.environ.get("GROQ_API_KEY", getattr(cfg, "GROQ_API_KEY", ""))

    if anthropic_key:
        try:
            return _call_claude(prompt, anthropic_key, max_tokens)
        except Exception as e:
            print(f"  Claude error ({e}) — falling back to Groq")

    if groq_key:
        # Groq has strict RPM limits; retry once on 429
        for attempt in range(2):
            try:
                return _call_groq(prompt, groq_key, max_tokens)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt == 0:
                    print("  Groq 429 — waiting 65s then retrying...")
                    time.sleep(65)
                else:
                    raise

    raise RuntimeError("No LLM API key available (set ANTHROPIC_API_KEY or GROQ_API_KEY).")


def _character_context(cfg) -> str:
    name  = getattr(cfg, "CHARACTER_NAME", "")
    bio   = getattr(cfg, "CHARACTER_BIO", "")
    style = getattr(cfg, "CHARACTER_STYLE", "")
    if not name:
        return ""
    return (
        f"\nCHARACTER PERSONA:\n"
        f"  Name: {name}\n"
        f"  Bio: {bio}\n"
        f"  Speech style: {style}\n"
        f"Write in {name}'s voice throughout. First-person where appropriate.\n"
    )


def _affiliate_context(cfg) -> str:
    programs = getattr(cfg, "AFFILIATE_PROGRAMS", [])
    if not programs:
        return ""
    lines = "\n".join(
        f"  - {p['name']}: {p['commission']} — {p['link_placeholder']}"
        for p in programs
    )
    return (
        f"\nAFFILIATE PROGRAMS (weave 2-3 most relevant into description + pinned_comment naturally):\n"
        f"{lines}\n"
    )


def _monetization_json_fields() -> str:
    return """
  "description": "YouTube description: what viewer will learn, 2-3 affiliate links as '🔗 Resource: URL', relevant timestamps for long-form, 10 hashtags",
  "pinned_comment": "First pinned comment ≤200 chars: 1 high-value tip + top affiliate link + 'More daily drops → subscribe!'","""


def generate_short_script(topic: dict, cfg) -> dict:
    character  = _character_context(cfg)
    affiliates = _affiliate_context(cfg)
    base_prompt = cfg.SHORT_PROMPT_TEMPLATE.format(**{k: str(v) for k, v in topic.items()})

    json_inject = _monetization_json_fields()
    if '"script"' in base_prompt:
        prompt = base_prompt.replace('"script"', f'{json_inject}\n  "script"', 1)
    else:
        prompt = base_prompt

    if character or affiliates:
        prompt = character + affiliates + prompt

    data = _llm(prompt, cfg, max_tokens=1800)
    data.setdefault("topic_name", topic.get("name", ""))
    return data


def generate_long_script(topic: dict, cfg) -> dict:
    character  = _character_context(cfg)
    affiliates = _affiliate_context(cfg)
    base_prompt = cfg.LONG_PROMPT_TEMPLATE.format(**{k: str(v) for k, v in topic.items()})

    json_inject = _monetization_json_fields()
    if '"title"' in base_prompt:
        prompt = base_prompt.replace('"title"', f'{json_inject}\n  "title"', 1)
    else:
        prompt = base_prompt

    if character or affiliates:
        prompt = character + affiliates + prompt

    return _llm(prompt, cfg, max_tokens=5500)
