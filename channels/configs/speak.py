"""
Mahayukti Speak (@mahayuktispeak) — English learning for Indians.
1 Short/day + 2 Long-form/week (Tue/Thu)
"""

CHANNEL_ID     = "speak"
CHANNEL_NAME   = "Mahayukti Speak"
CHANNEL_HANDLE = "@mahayuktispeak"
TOKEN_ENV_VAR  = "YOUTUBE_SPEAK_TOKEN_JSON"
TOKEN_FILE     = "speak_token.json"
SECRET_NAME    = "YOUTUBE_SPEAK_TOKEN_JSON"

# ── AI Character ─────────────────────────────────────────────────────────
CHARACTER_NAME      = "Neha"
CHARACTER_BIO       = "28-year-old English teacher from Hyderabad who scored Band 8 in IELTS and now helps Indians speak confidently at work and abroad. Has trained 5,000+ students."
CHARACTER_STYLE     = "Encouraging, patient, clear. Like the teacher you actually enjoyed in school. Uses comparisons with Indian languages for pronunciation. Never makes you feel bad for mistakes."
CHARACTER_IMAGE_URL = ""

ELEVENLABS_VOICE_ID = "MF3mGyEYCl7XYWbV9V6O"   # Elli — clear friendly female

SHORT_VOICE = "en-IN-NeerjaNeural"
LONG_VOICE  = "en-IN-NeerjaNeural"

SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
LONG_WIDTH   = 1920
LONG_HEIGHT  = 1080
FPS          = 24
OUTPUT_DIR   = "output"

BG_COLOR      = (2, 12, 8)
BG_COLOR_2    = (4, 25, 16)
PRIMARY_COLOR = (16, 185, 129)
ACCENT_COLOR  = (56, 189, 248)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (100, 180, 150)

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
    "Vocabulary":      ((2, 10, 5),  (4, 20, 10),  (0, 180, 100),  (0, 255, 160)),
    "Grammar":         ((3, 8, 15),  (6, 16, 30),  (0, 150, 220),  (50, 210, 255)),
    "Pronunciation":   ((10, 5, 2),  (20, 10, 4),  (200, 120, 0),  (255, 180, 0)),
    "Business English":((3, 12, 5),  (6, 25, 10),  (0, 200, 100),  (50, 255, 160)),
    "Idioms":          ((8, 3, 12),  (16, 6, 25),  (150, 0, 220),  (200, 80, 255)),
    "Interview":       ((5, 10, 3),  (10, 20, 6),  (100, 200, 0),  (180, 255, 0)),
    "Daily English":   ((2, 12, 10), (4, 25, 20),  (0, 180, 160),  (0, 255, 220)),
    "Writing":         ((10, 8, 2),  (20, 16, 4),  (200, 160, 0),  (255, 220, 0)),
    "General":         ((2, 12, 8),  (4, 25, 16),  (16, 185, 129), (56, 189, 248)),
}

CTA_LINE1  = "Follow for"
CTA_LINE2  = "daily English lessons"
CTA_SUBTEXT = "One English lesson every single day"

LONG_INTRO_BADGE = "ENGLISH MADE SIMPLE"
OUTRO_LINE1      = "Speak with confidence!"
OUTRO_LINE2      = "Subscribe for English lessons"
OUTRO_BELL_TEXT  = "Ring the bell — new lesson every Tue & Thu"

LONG_ALSO_GENERATES_SHORT = False

AFFILIATE_PROGRAMS = [
    {"name": "Cambly",        "commission": "$8 per free trial user",               "link_placeholder": "https://www.cambly.com/invite/YOUR_CODE"},
    {"name": "Coursera Plus", "commission": "45% on course purchases",              "link_placeholder": "https://imp.i384100.net/YOUR_ID"},
    {"name": "British Council IELTS", "commission": "₹500 per course signup",      "link_placeholder": "https://www.britishcouncil.in/?ref=YOUR_CODE"},
    {"name": "Grammarly Premium", "commission": "$20 per annual subscriber",        "link_placeholder": "https://grammarly.go2cloud.org/aff_c?offer_id=3&aff_id=YOUR_ID"},
    {"name": "IELTS/TOEFL Books (Amazon)", "commission": "8% on books",            "link_placeholder": "https://www.amazon.in/s?k=ielts+books&linkCode=ll2&tag=YOUR-TAG"},
    {"name": "Udemy English Courses", "commission": "25% per sale",                "link_placeholder": "https://click.linksynergy.com/fs-bin/click?id=YOUR_ID&offerid=507388"},
]


def bg_prompt(category: str, topic_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Vocabulary":       f"dictionary words floating emerald green dark background language {orientation} cinematic no text no people",
        "Grammar":          f"book pages floating words grammar teal light dark clean {orientation} cinematic no text no people",
        "Pronunciation":    f"mouth waveform sound waves orange gold microphone {orientation} cinematic no text no people",
        "Business English": f"office meeting professional laptop india corporate green {orientation} cinematic no text no people",
        "Idioms":           f"creative speech bubbles colorful language floating dark {orientation} cinematic no text no people",
        "Interview":        f"job interview shaking hands india professional confident green {orientation} cinematic no text no people",
        "Daily English":    f"conversation cafe coffee chat clean modern india teal {orientation} cinematic no text no people",
        "Writing":          f"pen paper writing letter glowing teal warm light {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"english education learning books light green teal clean dark {orientation} cinematic no text no people")


SHORT_TOPICS = [
    {"name": "5 Words Indians Mispronounce Daily", "category": "Pronunciation", "focus": "Breakfast, Wednesday, February, pronunciation, comfortable"},
    {"name": "Instead of 'Do the Needful' Say This", "category": "Business English", "focus": "Needful, revert, prepone — Indian English vs global English"},
    {"name": "3 Ways to Say No Politely in English", "category": "Daily English", "focus": "I'm afraid, I'd rather not, I'll have to pass"},
    {"name": "The Word 'Albeit' — Meaning + Examples", "category": "Vocabulary", "focus": "Advanced conjunction for essays and formal writing"},
    {"name": "'Will' vs 'Would' — Indians Get This Wrong", "category": "Grammar", "focus": "Future real vs hypothetical — simple rule"},
    {"name": "How to Open an Email Professionally", "category": "Business English", "focus": "I hope this email finds you well — better alternatives"},
    {"name": "When to Use 'I' vs 'Me' in a Sentence", "category": "Grammar", "focus": "Subject vs object pronoun — the simple test"},
    {"name": "Job Interview Opening Line — First 30 Seconds", "category": "Interview", "focus": "Tell me about yourself — 30-second structured response"},
    {"name": "The Word 'Ubiquitous' — Use It in 3 Ways", "category": "Vocabulary", "focus": "Meaning, pronunciation, 3 natural sentences"},
    {"name": "5 Phrases to Sound More Confident in English", "category": "Daily English", "focus": "Based on my experience, I would argue, it seems to me"},
    {"name": "'Much' vs 'Many' — Simple Rule", "category": "Grammar", "focus": "Countable vs uncountable nouns — one rule covers all"},
    {"name": "How to Disagree Professionally in English", "category": "Business English", "focus": "I see it differently, I understand but, with respect"},
    {"name": "The Word 'Nuance' — What It Means + Examples", "category": "Vocabulary", "focus": "Used in conversation, reports, analysis writing"},
    {"name": "Saying 'Sorry' Professionally Without Overdoing It", "category": "Business English", "focus": "Sorry vs I apologize vs my mistake — when to use what"},
    {"name": "'Affect' vs 'Effect' — Once and For All", "category": "Grammar", "focus": "Verb vs noun — memory trick that never fails"},
    {"name": "Indian English Mistakes in WhatsApp", "category": "Daily English", "focus": "Revert back, do the needful, kindly — global perception"},
    {"name": "5 Business Idioms to Sound Fluent", "category": "Idioms", "focus": "On the same page, touch base, bandwidth, bandwidth, loop in"},
    {"name": "How to Give Feedback in English", "category": "Business English", "focus": "Sandwich method, I noticed, one thing that would help"},
    {"name": "The Word 'Juxtapose' — Impress Anyone", "category": "Vocabulary", "focus": "Meaning, usage in essays and discussion"},
    {"name": "'Since' vs 'For' with Present Perfect", "category": "Grammar", "focus": "Since = point in time, For = duration — never confuse again"},
    {"name": "How to Negotiate Salary in English", "category": "Interview", "focus": "Based on research, I was thinking, what flexibility is there"},
    {"name": "Small Talk Starters for Professionals", "category": "Daily English", "focus": "Beyond 'how are you' — office, networking events, calls"},
    {"name": "The Difference Between 'Comprise' and 'Consist'", "category": "Vocabulary", "focus": "Comprise of is wrong — how to use it correctly"},
    {"name": "5 Phrasal Verbs Every Working Indian Needs", "category": "Business English", "focus": "Follow up, bring up, go over, wrap up, check in"},
    {"name": "How to Introduce Yourself at Networking Events", "category": "Daily English", "focus": "20-second elevator pitch structure"},
    {"name": "'Who' vs 'Whom' — Actually Simple", "category": "Grammar", "focus": "He/she test — works every single time"},
    {"name": "Words That Show You're Educated in English", "category": "Vocabulary", "focus": "Albeit, hitherto, ergo, consequently, nonetheless"},
    {"name": "How to Write a Professional Email Subject Line", "category": "Writing", "focus": "Action required, Request, FYI — correct subject line format"},
    {"name": "Commonly Confused: Fewer vs Less", "category": "Grammar", "focus": "Countable vs uncountable — supermarket checkout example"},
    {"name": "The STAR Method for Interview Answers", "category": "Interview", "focus": "Situation, Task, Action, Result — all behavioral questions"},
    {"name": "5 Power Words for Your Resume", "category": "Writing", "focus": "Spearheaded, implemented, optimised, collaborated, delivered"},
    {"name": "How to Sound Natural on Phone Calls in English", "category": "Daily English", "focus": "Could you please, I'll just, bear with me, connect phrases"},
    {"name": "American English vs British English — Key Differences", "category": "Daily English", "focus": "Flat vs apartment, lift vs elevator, biscuit vs cookie"},
    {"name": "'However' vs 'But' in Formal Writing", "category": "Grammar", "focus": "Position in sentence, when each sounds more natural"},
    {"name": "5 Filler Words to Remove from Your English", "category": "Daily English", "focus": "Basically, actually, you know, like, sort of — replace with silence"},
    {"name": "The Word 'Pragmatic' — When and How to Use It", "category": "Vocabulary", "focus": "Meaning, example sentences, common contexts"},
    {"name": "How to Request Information Politely", "category": "Business English", "focus": "Could you please, I was wondering if, at your convenience"},
    {"name": "Prepositions Indians Always Get Wrong", "category": "Grammar", "focus": "Discuss about, explain about, cope up — the correct forms"},
    {"name": "LinkedIn Summary in English — Template", "category": "Writing", "focus": "Hook, what you do, who you help, CTA — 3 sentences max"},
    {"name": "How to Express Opinions in English Confidently", "category": "Daily English", "focus": "I believe, in my view, from my perspective, it seems to me"},
    {"name": "Academic English Connectors", "category": "Writing", "focus": "Furthermore, nevertheless, in addition, as a result, consequently"},
    {"name": "5 Mistakes Indians Make in English Emails", "category": "Writing", "focus": "Please do the needful, revert, attached herewith, dear sir/madam"},
    {"name": "Collective Nouns That Surprise Indians", "category": "Vocabulary", "focus": "A pride of lions, a murder of crows, a parliament of owls"},
    {"name": "How to Give a Compliment in English", "category": "Daily English", "focus": "That was insightful, well articulated, great point — office use"},
    {"name": "The Difference: Bring vs Take", "category": "Grammar", "focus": "Bring = toward speaker, Take = away from speaker — simple examples"},
    {"name": "5 Interview Questions and Perfect Answers", "category": "Interview", "focus": "Weakness, failure, challenge, five years, salary"},
    {"name": "How to Write a WhatsApp Message Professionally", "category": "Writing", "focus": "Greet, context, request, thank — no 'kindly do the needful'"},
    {"name": "Conditional Sentences — Types 1, 2, 3 Made Simple", "category": "Grammar", "focus": "Real, unreal, past regret — one sentence example each"},
    {"name": "10 Advanced Synonyms for 'Important'", "category": "Vocabulary", "focus": "Crucial, vital, paramount, indispensable, pivotal, essential"},
    {"name": "How to Give a Presentation in English", "category": "Business English", "focus": "Opening, transitions, signposting, closing — template structure"},
]

LONG_TOPICS = [
    {"name": "Complete Guide to English Job Interviews", "category": "Interview", "focus": "Preparation, tell me about yourself, behavioral questions, salary negotiation, thank you email"},
    {"name": "Business Email Writing Masterclass", "category": "Writing", "focus": "Subject lines, opening lines, tone matching, structure, closing, common mistakes"},
    {"name": "How to Improve English Pronunciation — Practical Methods", "category": "Pronunciation", "focus": "Sound mapping, shadowing technique, Indian accent vs clear English, daily practice plan"},
    {"name": "English Vocabulary for Working Professionals", "category": "Vocabulary", "focus": "200 words at 3 levels — workplace, presentations, written communication"},
    {"name": "Grammar Indians Get Wrong Most Often", "category": "Grammar", "focus": "Top 20 Indian English mistakes, why we make them, simple correction rules"},
    {"name": "Spoken English Fluency in 90 Days — A Plan", "category": "Daily English", "focus": "Daily routine, shadowing, output practice, thinking in English, measuring progress"},
    {"name": "Business English for Sales and Marketing", "category": "Business English", "focus": "Pitch phrases, objection handling, closing language, follow-up emails"},
    {"name": "IELTS Speaking Band 7+ Guide", "category": "Daily English", "focus": "Band descriptors, Part 1/2/3 structure, vocabulary range, fluency tips"},
    {"name": "How to Write Reports and Proposals in English", "category": "Writing", "focus": "Executive summary, findings, recommendations — corporate writing structure"},
    {"name": "Public Speaking in English — Overcoming Fear", "category": "Daily English", "focus": "Preparation strategies, filler word removal, confidence body language, Q&A handling"},
    {"name": "English for Campus Placement Drives", "category": "Interview", "focus": "GD skills, HR round English, technical interview communication, body language"},
    {"name": "Advanced Vocabulary Building System", "category": "Vocabulary", "focus": "Spaced repetition, word families, collocations, contextual learning — 30-day system"},
]


SHORT_PROMPT_TEMPLATE = """You are India's most popular English teacher on YouTube Shorts.
Your lessons are clear, practical, and directly useful for Indian professionals.

Create a 60-second "English Lesson of the Day" Short about: {name}
Focus: {focus}
Category: {category}

Rules:
- Script MUST be 110-125 words MAX (60 seconds of clear teaching pace)
- Language: Clear English with Hindi explanations where needed — warm teaching tone
- HOOK: First sentence must make the viewer feel this lesson is for them
- Teach ONE thing extremely clearly with an example sentence
- Include: how Indians typically say it wrong → how to say it correctly
- Make it memorable — a trick, a story, a comparison
- End CTA: "Follow @mahayuktispeak — daily English lessons"

Return valid JSON:
{{
  "topic_name": "{name}",
  "hook": "First 3-second teaching hook that makes them stay",
  "script": "Full 60-second teaching narration (110-125 words, clear and warm)",
  "slides": [
    {{"text": "{name}", "label": "TODAY'S LESSON"}},
    {{"text": "Wrong vs right example — max 10 words", "label": "COMMON MISTAKE"}},
    {{"text": "The correct way — max 10 words", "label": "CORRECT FORM"}},
    {{"text": "Memory tip — max 10 words", "label": "REMEMBER THIS"}},
    {{"text": "Follow @mahayuktispeak for daily English", "label": "FOLLOW US"}}
  ],
  "title": "YouTube title — max 60 chars, lesson topic, practical angle, emoji",
  "description": "YouTube description — 150 words, lesson summary, more examples, 8 hashtags #EnglishLearning #SpokenEnglish #EnglishIndia #Shorts",
  "tags": ["english learning india", "spoken english india", "english grammar india", "mahayuktispeak", "{name}", "english tips india", "fluent english", "english mistakes indians"]
}}"""

LONG_PROMPT_TEMPLATE = """You are India's most trusted English teacher — practical, patient, India-aware.
Create a complete English lesson: "{name}"

Focus areas: {focus}
Category: {category}

Rules:
- Total narration: 1600-2000 words (12-15 min at teaching pace)
- Language: Clear English throughout, Hindi translations for difficult concepts
- Tone: Patient teacher — no shame, just clear learning
- Structure: Why this matters → Core teaching → Multiple examples → Practice exercises → Common mistakes to avoid
- Use INDIAN context examples (offices, WhatsApp, job interviews, college)
- Include: drills, memory tricks, cheat sheets the viewer can screenshot
- End with: A clear homework assignment (1-2 short exercises)

Return valid JSON:
{{
  "episode_title": "{name}",
  "intro_script": "150-word opener — describe exactly when this lesson will help them in real life",
  "items": [
    {{
      "rank": 1,
      "name": "lesson section title",
      "narration": "350-400 word clear teaching section with examples",
      "key_points": ["Key rule or example 1", "Key rule or example 2", "Practice point"],
      "summary": "One memorable takeaway from this section",
      "category": "{category}"
    }}
  ],
  "outro_script": "100-word homework assignment + motivating close + subscribe CTA",
  "full_script": "Complete narration: intro + all sections + outro concatenated",
  "title": "YouTube title — max 70 chars, practical and search-friendly",
  "description": "250-word description — lesson overview, India context, practice tips, 12 hashtags #EnglishLearning #SpokenEnglish #EnglishIndia",
  "tags": ["english learning india", "spoken english india", "{name}", "mahayuktispeak", "english grammar hindi", "english speaking course india", "ielts india", "english for job india", "fluent english india", "business english india", "english tips india", "english mistakes indians"]
}}"""
