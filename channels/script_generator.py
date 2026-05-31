"""
Generic script generator — channel config provides prompt templates.
Injects: character persona, affiliate programs, pinned comment CTA.
"""
import json
import os
import re
import requests


_GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.3-70b-versatile"


def _call_groq(prompt: str, groq_key: str, max_tokens: int = 2000) -> dict:
    r = requests.post(
        _GROQ_URL,
        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
        json={
            "model": _GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.85,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        },
        timeout=90,
    )
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])


def _call_anthropic(prompt: str, anthropic_key: str, max_tokens: int = 2000) -> dict:
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=90,
    )
    r.raise_for_status()
    text = r.json()["content"][0]["text"]
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group()) if m else {}


def _llm(prompt: str, cfg, max_tokens: int = 2000) -> dict:
    groq_key      = os.environ.get("GROQ_API_KEY", getattr(cfg, "GROQ_API_KEY", ""))
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", getattr(cfg, "ANTHROPIC_API_KEY", ""))
    if groq_key:
        return _call_groq(prompt, groq_key, max_tokens)
    return _call_anthropic(prompt, anthropic_key, max_tokens)


def _character_context(cfg) -> str:
    name  = getattr(cfg, "CHARACTER_NAME", "")
    bio   = getattr(cfg, "CHARACTER_BIO", "")
    style = getattr(cfg, "CHARACTER_STYLE", "")
    if not name:
        return ""
    return f"\nCHARACTER: You are writing for {name}. {bio} Speech style: {style}\n"


def _affiliate_context(cfg) -> str:
    programs = getattr(cfg, "AFFILIATE_PROGRAMS", [])
    if not programs:
        return ""
    lines = "\n".join(f"  - {p['name']}: {p['commission']} — {p['link_placeholder']}" for p in programs)
    return f"\nAFFILIATE PROGRAMS (include 2-3 most relevant in description + pinned_comment):\n{lines}\n"


def _monetization_json_fields() -> str:
    return """
  "character_intro": "15-20 second intro spoken by the AI host character — personal, warm, name themselves",
  "description": "YouTube description including: content summary, 2-3 affiliate links from the list above formatted as '🔗 [Resource Name]: [URL]', timestamps for long-form, 10-12 hashtags",
  "pinned_comment": "First pinned comment (200 chars max): friendly CTA with top 2 affiliate links + 'Subscribe for more!'","""


def generate_short_script(topic: dict, cfg) -> dict:
    character = _character_context(cfg)
    affiliates = _affiliate_context(cfg)
    base_prompt = cfg.SHORT_PROMPT_TEMPLATE.format(**{k: str(v) for k, v in topic.items()})

    # Inject character + affiliate context before the JSON schema
    json_inject = _monetization_json_fields()
    if '"script"' in base_prompt:
        prompt = base_prompt.replace(
            '"script"',
            f'{json_inject}\n  "script"',
            1
        )
    else:
        prompt = base_prompt

    if character or affiliates:
        prompt = character + affiliates + prompt

    data = _llm(prompt, cfg, max_tokens=1600)
    data.setdefault("topic_name", topic.get("name", ""))
    return data


def generate_long_script(topic: dict, cfg) -> dict:
    character = _character_context(cfg)
    affiliates = _affiliate_context(cfg)
    base_prompt = cfg.LONG_PROMPT_TEMPLATE.format(**{k: str(v) for k, v in topic.items()})

    json_inject = _monetization_json_fields()
    if '"title"' in base_prompt:
        prompt = base_prompt.replace(
            '"title"',
            f'{json_inject}\n  "title"',
            1
        )
    else:
        prompt = base_prompt

    if character or affiliates:
        prompt = character + affiliates + prompt

    return _llm(prompt, cfg, max_tokens=5000)
