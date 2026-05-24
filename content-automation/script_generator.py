import json
import re
from groq import Groq
from config import GROQ_API_KEY, CHANNEL_NAME, CHANNEL_HANDLE


def generate_script(topic: dict) -> dict:
    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""You are the scriptwriter for "{CHANNEL_NAME}" ({CHANNEL_HANDLE}), a popular Indian personal finance YouTube channel.

Topic: "{topic['angle']}"
Category: {topic['category']}

Write a complete video package in HINGLISH (natural Hindi-English mix in Roman script).
Target audience: Indians aged 18-35 who want to grow their wealth.
Script length: ~750-850 words (5-6 minutes when spoken at normal pace).

Return ONLY valid JSON — no markdown, no backticks, no explanation. Exact format:

{{
  "title": "Catchy YouTube title in Hinglish, max 70 chars. Use numbers or questions. Must make people click.",
  "hook": "One shocking fact or question to open the video, max 20 words.",
  "script": "Full voiceover script. Conversational Hinglish tone. Start with a strong hook (question or shocking fact). Use real Indian examples with rupee amounts. Cover the topic in 5-7 clear points. End with a CTA to subscribe to Mahayukti Finance.",
  "key_points": ["Point 1 max 12 words", "Point 2 max 12 words", "Point 3 max 12 words", "Point 4 max 12 words", "Point 5 max 12 words", "Point 6 max 12 words"],
  "description": "YouTube video description. 200 words. Include what the video covers, timestamps for key points, relevant hashtags like #PersonalFinance #MahayuktiFinance #PaisaSamjho #MoneyTips. End with subscribe CTA mentioning Mahayukti Finance.",
  "tags": ["MahayuktiFinance", "mahayukti", "PaisaSamjho", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13", "tag14", "tag15"],
  "thumbnail_text": "Short punchy ALL CAPS text for thumbnail image, max 5 words"
}}

Script tone rules:
- Sound like a knowledgeable friend, not a formal textbook
- Mix Hindi and English naturally: "10,000 rupay ki SIP se 30 saal mein 3.5 crore ban sakte hain"
- Use real numbers, real examples, real Indian context
- Include at least one surprising fact or shocking statistic
- Keep it practical: viewers should be able to act on the advice today
- Never reference Paisa Gyaan in scripts, tags, or descriptions"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2048,
    )

    text = response.choices[0].message.content.strip()

    # Strip markdown code fences if the model adds them
    text = re.sub(r"^```json?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return json.loads(text)
