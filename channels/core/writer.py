"""
Script generation via Claude API.
Produces structured scene-by-scene scripts for Shorts and Long-form videos.
"""
import json
import os
import re

import anthropic

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _parse_json(text: str) -> dict:
    """Extract the first JSON object from a Claude response."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response:\n{text[:500]}")
    return json.loads(match.group())


def generate_short(config, topic: dict) -> dict:
    """
    Generate a YouTube Shorts script for the given channel config and topic.

    Returns a dict:
    {
      "youtube_title": str,
      "youtube_description": str,
      "tags": [str],
      "scenes": [{"narration": str, "visual_prompt": str, "duration_hint": float}]
    }
    Total scenes should sum to ~55-60 seconds.
    """
    aspect = "vertical 9:16"

    prompt = f"""You create viral YouTube Shorts scripts for {config.CHANNEL_NAME} ({config.CHANNEL_HANDLE}).

Channel niche: {config.NICHE}
Video style: {config.VIDEO_STYLE}
Topic: {topic['name']}
Category: {topic.get('category', 'General')}

Write a 55-60 second Short. Return ONLY valid JSON, no markdown:

{{
  "youtube_title": "Max 60 chars, punchy, emoji, stops the scroll",
  "youtube_description": "80-word description + 6 relevant hashtags",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "scenes": [
    {{
      "narration": "Exact words spoken aloud. 8-12 words max per scene.",
      "visual_prompt": "Cinematic {aspect} video scene. Specific, vivid, NO text, NO faces. India-relevant where fitting. {config.VIDEO_STYLE}",
      "duration_hint": 6.0
    }}
  ]
}}

Rules:
- 8-10 scenes, each 5-8 seconds. Total ≈ 55 seconds.
- Scene 1: brutal hook — surprising fact or bold statement
- Scenes 2-7: rapid insight delivery, one idea per scene
- Final scene: micro-CTA ("Follow for more" / "Share this")
- Visual prompts must be concrete cinematic descriptions — director-level detail
- No filler words, no "um", no padding
"""

    resp = _get_client().messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json(resp.content[0].text)


def generate_long(config, topic: dict) -> dict:
    """
    Generate a long-form YouTube video script.

    Returns:
    {
      "youtube_title": str,
      "youtube_description": str,
      "tags": [str],
      "sections": [
        {
          "heading": str,
          "narration": str,            # full spoken narration for this section
          "visual_prompts": [str]      # 2-4 cinematic scene prompts for this section
        }
      ]
    }
    """
    prompt = f"""You create deeply engaging YouTube documentary scripts for {config.CHANNEL_NAME} ({config.CHANNEL_HANDLE}).

Channel niche: {config.NICHE}
Video style: {config.VIDEO_STYLE}
Topic: {topic['name']}
Angle: {topic.get('angle', '')}
Category: {topic.get('category', 'General')}

Write a 12-15 minute video script (1800-2200 words of narration). Return ONLY valid JSON, no markdown:

{{
  "youtube_title": "Max 70 chars, keyword-rich, emoji, India-specific hook",
  "youtube_description": "400-word description with timestamps, key takeaways, 12 hashtags",
  "tags": ["tag1", "tag2"],
  "sections": [
    {{
      "heading": "Section title shown on screen (e.g. 'The Beginning', 'The Turning Point')",
      "narration": "280-340 words of narration. Flows naturally when read aloud. Real facts, specific numbers, storytelling pace.",
      "visual_prompts": [
        "Cinematic 16:9 scene — highly specific, vivid, director-level detail. {config.VIDEO_STYLE}. NO text. NO faces.",
        "Another distinct visual moment for this section"
      ]
    }}
  ]
}}

Rules:
- 6-7 sections minimum
- Section 1: dramatic hook — start IN the most compelling moment
- Middle sections: build the story with real data and human stakes
- Final section: lessons + forward-looking conclusion
- Visual prompts: 2-3 per section, each a completely different cinematic shot
- Narration must sound like an engaging documentary voiceover, not an article
- Include real names, numbers, dates, and specific details
"""

    resp = _get_client().messages.create(
        model="claude-opus-4-5",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json(resp.content[0].text)
