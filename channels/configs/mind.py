"""
Mahayukti Mind (@mahayuktimind) — psychology & mental health.
2 Shorts/day + 2 Long-form/week (Tue/Fri)
"""

CHANNEL_ID     = "mind"
CHANNEL_NAME   = "Mahayukti Mind"
CHANNEL_HANDLE = "@mahayuktimind"
TOKEN_ENV_VAR  = "YOUTUBE_MIND_TOKEN_JSON"
TOKEN_FILE     = "mind_token.json"
SECRET_NAME    = "YOUTUBE_MIND_TOKEN_JSON"

# ── AI Character ─────────────────────────────────────────────────────────
CHARACTER_NAME      = "Priya"
CHARACTER_BIO       = "32-year-old clinical psychologist from Bangalore with 8 years experience working with Indian families. Trained at NIMHANS. Passionate about making psychology accessible to ordinary Indians."
CHARACTER_STYLE     = "Warm, non-judgmental, intelligent. Like a therapist friend over coffee. Uses 'yeh bilkul normal hai' when normalising struggles. Never preachy. Science-backed but human."
CHARACTER_IMAGE_URL = "https://raw.githubusercontent.com/vedantrungta1209/mahayukti-website/main/channels/characters/mind.jpg"

ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"   # Rachel — warm empathetic female

SHORT_VOICE = "en-IN-NeerjaNeural"
LONG_VOICE  = "en-IN-NeerjaNeural"

SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
LONG_WIDTH   = 1920
LONG_HEIGHT  = 1080
FPS          = 24
OUTPUT_DIR   = "output"

BG_COLOR      = (8, 3, 18)
BG_COLOR_2    = (15, 6, 35)
PRIMARY_COLOR = (139, 92, 246)
ACCENT_COLOR  = (0, 220, 220)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (130, 100, 180)

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
    "Narcissism":       ((10, 3, 5),  (20, 6, 10),  (200, 0, 100),  (255, 80, 160)),
    "Attachment":       ((3, 8, 15),  (6, 16, 30),  (0, 150, 255),  (100, 200, 255)),
    "Trauma":           ((8, 5, 3),   (16, 10, 6),  (180, 80, 0),   (255, 160, 50)),
    "Cognitive Bias":   ((3, 10, 8),  (6, 20, 16),  (0, 180, 150),  (0, 255, 200)),
    "Self-Improvement": ((5, 3, 12),  (10, 6, 25),  (150, 0, 255),  (200, 100, 255)),
    "Relationships":    ((12, 3, 8),  (25, 6, 16),  (230, 60, 120), (255, 150, 180)),
    "Emotions":         ((3, 10, 15), (6, 20, 30),  (0, 150, 200),  (50, 220, 255)),
    "Dark Psychology":  ((8, 3, 3),   (16, 6, 6),   (180, 0, 0),    (255, 50, 50)),
    "Mindfulness":      ((3, 12, 8),  (6, 25, 16),  (0, 200, 120),  (0, 255, 160)),
    "General":          ((8, 3, 18),  (15, 6, 35),  (139, 92, 246), (0, 220, 220)),
}

CTA_LINE1  = "Follow for"
CTA_LINE2  = "daily psychology facts"
CTA_SUBTEXT = "New psychology drop every day"

LONG_INTRO_BADGE = "PSYCHOLOGY DEEP DIVE"
OUTRO_LINE1      = "Subscribe for more!"
OUTRO_LINE2      = "New deep dive every week"
OUTRO_BELL_TEXT  = "Ring the bell — new video every Tue & Fri"

LONG_ALSO_GENERATES_SHORT = False

AFFILIATE_PROGRAMS = [
    {"name": "iCall (Indian therapy)", "commission": "₹200 per first session booking", "link_placeholder": "https://icallhelpline.org/?ref=YOUR_CODE"},
    {"name": "Wysa App",        "commission": "₹150 per premium subscription",         "link_placeholder": "https://www.wysa.com/partner/YOUR_CODE"},
    {"name": "Headspace",       "commission": "15% on annual subscriptions",            "link_placeholder": "https://www.headspace.com/headspace-meditation-app?utm_source=YOUR_ID"},
    {"name": "Psychology Books (Amazon)", "commission": "8% on book purchases",         "link_placeholder": "https://www.amazon.in/s?k=psychology+books&linkCode=ll2&tag=YOUR-TAG"},
    {"name": "BetterHelp",      "commission": "$100+ per paying subscriber",            "link_placeholder": "https://www.betterhelp.com/partner-signup/?utm_campaign=YOUR_ID"},
    {"name": "Calm App",        "commission": "20% recurring on subscriptions",         "link_placeholder": "https://www.calm.com/affiliates"},
]


def bg_prompt(category: str, topic_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Narcissism":       f"mirror shattered fragments dark purple red psychological drama {orientation} cinematic no text no people",
        "Attachment":       f"two silhouettes connected by glowing threads blue teal dark {orientation} cinematic no text no people",
        "Trauma":           f"fractured glass light rays through cracks golden healing dark {orientation} cinematic no text no people",
        "Cognitive Bias":   f"brain neural pathways glowing teal neon dark background mind {orientation} cinematic no text no people",
        "Self-Improvement": f"person meditating glowing purple light transformation dark {orientation} cinematic no text no people",
        "Relationships":    f"two hands reaching glowing warm pink rose gold connection {orientation} cinematic no text no people",
        "Emotions":         f"colorful emotion spheres floating dark background feelings aura {orientation} cinematic no text no people",
        "Dark Psychology":  f"shadowy figure chess pieces manipulation dark chess board {orientation} cinematic no text no people",
        "Mindfulness":      f"meditation lotus green teal calm water reflection serenity {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"human brain psychology purple teal neon dark abstract mind {orientation} cinematic no text no people")


SHORT_TOPICS = [
    {"name": "Narcissistic Abuse Cycle", "category": "Narcissism", "hook": "Agar tumhara partner tumhe bad feel karata hai lekin tum chhod nahi sakte"},
    {"name": "Love Bombing Red Flags", "category": "Narcissism", "hook": "When someone is TOO perfect in the beginning — that's a warning sign"},
    {"name": "Anxious Attachment Style", "category": "Attachment", "hook": "Kya tum constantly check karte ho ki partner ne message kiya ya nahi"},
    {"name": "Avoidant Attachment Style", "category": "Attachment", "hook": "You push people away when they get close — here's why"},
    {"name": "Disorganized Attachment", "category": "Attachment", "hook": "Tum love chahte ho lekin isse dartey bhi ho — yeh pattern hai"},
    {"name": "Gaslighting Recognition", "category": "Narcissism", "hook": "Agar koi tumse kehta hai 'yeh tumhare imagination mein hai' — DANGER"},
    {"name": "Why You Self-Sabotage", "category": "Self-Improvement", "hook": "Success ke paas pohonchke tum khud sab kuch kharab karte ho — here's why"},
    {"name": "Impostor Syndrome", "category": "Self-Improvement", "hook": "Successful logon ko bhi lagta hai ki woh fraud hain — science ye kehta hai"},
    {"name": "Dunning-Kruger Effect", "category": "Cognitive Bias", "hook": "Jo log sabse zyada confident hote hain, woh often sabse zyada wrong hote hain"},
    {"name": "Sunk Cost Fallacy", "category": "Cognitive Bias", "hook": "Sirf isliye mat ruko kyunki tum bahut waqt de chuke ho — this is a trap"},
    {"name": "Confirmation Bias", "category": "Cognitive Bias", "hook": "Tumhara dimag sirf woh evidence dhundta hai jo tumhara belief confirm kare"},
    {"name": "Loss Aversion Psychology", "category": "Cognitive Bias", "hook": "₹100 khoye ka dard ₹100 paane ki khushi se DOUBLE hota hai — why?"},
    {"name": "Intermittent Reinforcement Trap", "category": "Relationships", "hook": "Toxic relationships mein rehne ki wajah — slot machine psychology"},
    {"name": "Trauma Bonding", "category": "Trauma", "hook": "Kya tum kisi abusive relationship mein isliye ho kyunki unhe chod nahi sakte?"},
    {"name": "Dark Triad Personalities", "category": "Dark Psychology", "hook": "3 traits jo make someone genuinely dangerous to be around"},
    {"name": "Emotional Manipulation Tactics", "category": "Dark Psychology", "hook": "10 manipulation techniques used on you daily — pata bhi nahi hoga"},
    {"name": "People-Pleasing Psychology", "category": "Self-Improvement", "hook": "'No' bolne mein kyun darr lagta hai — childhood trauma connection"},
    {"name": "Mirror Neurons and Empathy", "category": "Emotions", "hook": "Dusron ka dard tum kyon feel karte ho — brain mein special cells hote hain"},
    {"name": "FOMO Psychology", "category": "Emotions", "hook": "Social media ne ek aisa dard create kiya jo pehle existed nahi karta tha"},
    {"name": "Cognitive Dissonance", "category": "Cognitive Bias", "hook": "Jab do opposite beliefs ek sath hote hain dimag mein — yeh hota hai"},
    {"name": "Passive-Aggressive Behavior", "category": "Relationships", "hook": "The most frustrating personality type — and how to deal with them"},
    {"name": "Codependency Signs", "category": "Relationships", "hook": "Kya tum kisi ke liye khud ko mitata jaa rahe ho — stop, this is codependency"},
    {"name": "Inner Child Wounds", "category": "Trauma", "hook": "Bachpan mein jo chot lagi — woh aaj bhi tumhare decisions control karti hai"},
    {"name": "Shadow Self Psychology (Jung)", "category": "Self-Improvement", "hook": "Jo qualities tum dusron mein hate karte ho — woh tumhari shadow hai"},
    {"name": "Victim Mentality vs Accountability", "category": "Self-Improvement", "hook": "Victim mindset aur owner mindset mein yeh ek key difference hota hai"},
    {"name": "Dopamine Detox Reality", "category": "Mindfulness", "hook": "Dopamine detox kya actually hota hai — science ya just a trend?"},
    {"name": "Social Media Depression Link", "category": "Emotions", "hook": "Instagram dekhne ke baad sad feel karna — this is a documented disorder"},
    {"name": "Anger as a Secondary Emotion", "category": "Emotions", "hook": "Anger actually sabse bade emotion nahi hota — yeh cover karta hai kuch aur"},
    {"name": "Why Criticism Hurts So Much", "category": "Emotions", "hook": "Ek negative comment 100 compliments ko drown kar deta hai — brain ke kaaran"},
    {"name": "Anxiety vs Intuition", "category": "Emotions", "hook": "Kaise pata karo ki yeh gut feeling hai ya sirf anxiety?"},
    {"name": "Boundaries in Indian Families", "category": "Relationships", "hook": "India mein 'boundaries' ka concept kyun ajeeb lagta hai — but it's crucial"},
    {"name": "Scarcity Mindset Origins", "category": "Self-Improvement", "hook": "Paise ki anxiety generations se aati hai — generational trauma of poverty"},
    {"name": "Oversharing on Social Media Psychology", "category": "Emotions", "hook": "Kyon kuch log apni private life sab ko dikhate hain — attachment theory"},
    {"name": "The Bystander Effect", "category": "Cognitive Bias", "hook": "Public mein kuch bura hote dekh sab kyun wait karte hain — psychology"},
    {"name": "Projection as Defense Mechanism", "category": "Dark Psychology", "hook": "Jo qualities dusron mein point out karte ho — woh actually tumhare andar hain"},
    {"name": "Why Arguments Escalate", "category": "Relationships", "hook": "Har argument actually kuch aur ke baare mein hota hai — the real issue"},
    {"name": "Hyper-Independence as Trauma Response", "category": "Trauma", "hook": "'I don't need anyone' — yeh strength nahi hai, yeh trauma response hai"},
    {"name": "Hedonic Adaptation", "category": "Emotions", "hook": "Har cheez achieve karne ke baad khushi kyun temporary hoti hai — science"},
    {"name": "The 5 Stages of Grief", "category": "Emotions", "hook": "Grief sirf death pe nahi aata — breakup, job loss, kisi bhi loss pe aata hai"},
    {"name": "Perfectionism as Anxiety", "category": "Self-Improvement", "hook": "Perfect hone ki koshish actually failure ka darr hai — not ambition"},
    {"name": "Growth Mindset vs Fixed Mindset", "category": "Self-Improvement", "hook": "Carol Dweck ki research: yeh 2 words change karte hain life outcomes"},
    {"name": "Emotional Regulation Techniques", "category": "Mindfulness", "hook": "3 second technique to stop emotional hijacking — works in the moment"},
    {"name": "Toxic Positivity", "category": "Emotions", "hook": "'Sab theek ho jayega' sometimes the most harmful thing to say"},
    {"name": "Childhood Emotional Neglect", "category": "Trauma", "hook": "Ghar mein sab kuch tha lekin emotional connect nahi tha — yeh trauma hai"},
    {"name": "Attention Residue", "category": "Self-Improvement", "hook": "Multitasking kyun nahi karna chahiye — attention residue science"},
    {"name": "Learned Helplessness", "category": "Self-Improvement", "hook": "'Main kuch nahi kar sakta' — yeh belief kahan se aati hai?"},
    {"name": "Empathy Fatigue", "category": "Emotions", "hook": "Doosron ki problems sunne ke baad tum exhausted kyun feel karte ho"},
    {"name": "Locus of Control", "category": "Self-Improvement", "hook": "Jo log apni life control karte hain woh ek specific belief rakhte hain"},
    {"name": "Why People Stay in Toxic Relationships", "category": "Relationships", "hook": "7 psychological reasons — it's not weakness, it's brain chemistry"},
    {"name": "Attachment to Outcomes (Non-attachment)", "category": "Mindfulness", "hook": "Desire vs Attachment — Buddhist psychology jo actually works"},
    {"name": "Body Dysmorphia in Indian Teens", "category": "Emotions", "hook": "Instagram + fair skin obsession + thin ideal = body image crisis India"},
    {"name": "Morning Anxiety Psychology", "category": "Emotions", "hook": "Subah uthte hi anxiety kyun hoti hai — cortisol awakening response"},
    {"name": "Trust Issues Root Causes", "category": "Relationships", "hook": "Kisi pe trust nahi kar paate — yeh 3 childhood experiences hote hain usually"},
    {"name": "Overthinking Brain Science", "category": "Cognitive Bias", "hook": "Overthinking habit nahi hai — yeh brain ka default mode network hai"},
    {"name": "Self-Compassion vs Self-Pity", "category": "Self-Improvement", "hook": "Apne aap se pyaar karna selfish nahi hai — self-compassion ki science"},
    {"name": "Envy vs Jealousy Psychology", "category": "Emotions", "hook": "Envy aur jealousy alag hain — aur dono tumhara kuch reveal karte hain"},
    {"name": "Why Procrastination Is Not Laziness", "category": "Self-Improvement", "hook": "Procrastination = emotion regulation problem, not time management"},
    {"name": "The Spotlight Effect", "category": "Cognitive Bias", "hook": "Tum sochte ho sab tumhe dekh rahe hain — they're NOT, science says"},
    {"name": "Abandonment Fear in Adults", "category": "Attachment", "hook": "Agar koi nahi uthata phone toh heart race kyun hota hai — childhood link"},
    {"name": "Psychological Safety at Work", "category": "Relationships", "hook": "India ke offices mein yeh ek culture missing hai — and it's hurting business"},
    {"name": "Revenge Fantasies Psychology", "category": "Emotions", "hook": "Doosron ke baare mein revenge sochna — psychologically it's NOT harmful"},
    {"name": "Why Apologies Don't Work Without Change", "category": "Relationships", "hook": "'Sorry' sabse misused word hai — what a real apology looks like"},
    {"name": "Childhood Parentification Trauma", "category": "Trauma", "hook": "Bachpan mein parents ka support banana pad gaya — yeh childhood trauma hai"},
    {"name": "Midlife Crisis Psychology", "category": "Emotions", "hook": "40 ke baad existential dread kyun aata hai — the identity crisis explained"},
    {"name": "Comparison Trap on LinkedIn", "category": "Emotions", "hook": "LinkedIn dekh ke inferior feel karna — illusory superiority + social comparison"},
    {"name": "Emotional Intelligence Basics", "category": "Self-Improvement", "hook": "IQ se zyada important hai EQ — but what exactly is emotional intelligence?"},
    {"name": "The Empathy Map", "category": "Emotions", "hook": "Kisi ko samajhna chahte ho? Yeh 4-step framework use karo"},
    {"name": "Decision Fatigue", "category": "Cognitive Bias", "hook": "Raat ke waqt worst decisions kyun karte hain — decision fatigue science"},
    {"name": "Healthy vs Unhealthy Anger", "category": "Emotions", "hook": "Anger kabhi kabhi NECESSARY hota hai — the difference between healthy anger"},
    {"name": "Over-explaining as Anxiety Response", "category": "Emotions", "hook": "Har decision ke baad justify kyun karte ho — over-explanation anxiety link"},
    {"name": "Psychology of Money Anxiety in India", "category": "Self-Improvement", "hook": "Paise ka darr logon ko poor decisions karvata hai — why poor stays poor"},
    {"name": "Emotional Flashbacks", "category": "Trauma", "hook": "Yeh memories nahi hain — yeh emotional flashbacks hain, far more dangerous"},
    {"name": "Stonewalling in Relationships", "category": "Relationships", "hook": "Silent treatment deना — yeh communication failure nahi, yeh abuse hai"},
]

LONG_TOPICS = [
    {"name": "Narcissistic Personality Disorder — Complete Guide for Indians", "category": "Narcissism", "focus": "Types of narcissism, Indian family context, healing from narcissistic abuse, when to leave"},
    {"name": "Attachment Theory and Your Relationships", "category": "Attachment", "focus": "4 attachment styles, how childhood shapes adult relationships, earned secure attachment"},
    {"name": "Why You Self-Sabotage — The Deep Psychology", "category": "Self-Improvement", "focus": "Unconscious blocks, fear of success, imposter syndrome, childhood programming"},
    {"name": "Understanding Trauma — A Complete Guide", "category": "Trauma", "focus": "Big T vs small t trauma, somatic trauma, complex PTSD, India-specific family trauma"},
    {"name": "The Psychology of Toxic Relationships", "category": "Relationships", "focus": "Why we stay, trauma bonding, the leaving process, healing after"},
    {"name": "Cognitive Biases That Ruin Your Finances and Career", "category": "Cognitive Bias", "focus": "10 most damaging biases, real India examples, de-biasing strategies"},
    {"name": "How to Stop Overthinking — Science-Based Methods", "category": "Cognitive Bias", "focus": "Default mode network, rumination vs reflection, CBT techniques"},
    {"name": "Emotional Intelligence — How to Build It", "category": "Self-Improvement", "focus": "4 components, Indian cultural barriers to EQ, practical exercises"},
    {"name": "Depression in India — What No One Talks About", "category": "Emotions", "focus": "India's mental health crisis, stigma, symptoms, when to seek help"},
    {"name": "The Dark Triad and How to Spot Them", "category": "Dark Psychology", "focus": "Narcissism, Machiavellianism, Psychopathy — in workplace, relationships, family"},
    {"name": "Setting Boundaries in Indian Culture", "category": "Relationships", "focus": "Why boundaries feel taboo in India, family pressure, script templates"},
    {"name": "Healing Your Inner Child — A Practical Guide", "category": "Trauma", "focus": "Inner child work, re-parenting, childhood emotional neglect recovery"},
    {"name": "Social Anxiety — Understanding and Overcoming It", "category": "Emotions", "focus": "Indian cultural pressure, shame vs anxiety, exposure therapy, CBT"},
    {"name": "Psychology of Procrastination — Finally Fix It", "category": "Self-Improvement", "focus": "Root cause (emotion, not time), neuroscience, 5 evidence-based fixes"},
    {"name": "How Childhood Trauma Shows Up in Adult Relationships", "category": "Trauma", "focus": "Attachment wounds, repetition compulsion, intergenerational trauma, healing path"},
]


SHORT_PROMPT_TEMPLATE = """You are a viral Indian psychology content creator — calm, deep, intelligent.
Your Shorts stop the scroll with psychological insight Indians NEED to hear.

Create a 60-second "Psychology Fact of the Day" Short about: {name}
Hook: {hook}
Category: {category}

Rules:
- Script MUST be 110-125 words MAX (60 seconds, measured calm pace)
- Language: Mix of clear English + Hindi — warm, intelligent, like a knowledgeable friend
- HOOK: Use the given hook or make it even more compelling
- Deliver ONE key psychological insight clearly
- If applicable: mention the research/psychologist behind it
- Make people feel UNDERSTOOD, not judged
- End CTA: "Follow @mahayuktimind — daily psychology facts"

Return valid JSON:
{{
  "topic_name": "{name}",
  "hook": "First 3-second insight that stops the scroll",
  "script": "Full 60-second narration (110-125 words, warm and intelligent)",
  "slides": [
    {{"text": "{name}", "label": "PSYCHOLOGY FACT"}},
    {{"text": "The science in 10 words", "label": "THE SCIENCE"}},
    {{"text": "How this affects you — max 10 words", "label": "IN YOUR LIFE"}},
    {{"text": "One actionable tip — max 10 words", "label": "WHAT TO DO"}},
    {{"text": "Follow @mahayuktimind for daily psychology", "label": "FOLLOW US"}}
  ],
  "title": "YouTube title — max 60 chars, psychologically intriguing, emoji",
  "description": "YouTube description — 150 words, research context, India relevance, 8 hashtags #Psychology #MentalHealth #IndianPsychology #Shorts",
  "tags": ["psychology india", "mental health india", "psychology facts", "mahayuktimind", "{name}", "narcissism india", "attachment theory", "self improvement india"]
}}"""

LONG_PROMPT_TEMPLATE = """You are India's most insightful psychology educator on YouTube.
Create a deep-dive video: "{name}"

Focus areas: {focus}
Psychology category: {category}

Rules:
- Total narration: 1600-2000 words (10-14 min at calm pace)
- Language: Clear English with warm Hindi phrases — like a therapist friend
- Tone: Non-judgmental, validating, educational — NOT preachy
- Structure: What it is → Why it happens → How it shows up in Indian context → Healing/What to do
- Include: Research (cite researchers where possible), relatable Indian examples
- Avoid stigma language — frame everything with compassion
- End with SPECIFIC actionable steps — what can someone do this week?

Return valid JSON:
{{
  "episode_title": "{name}",
  "intro_script": "180-word intro — start with a scenario Indians will immediately recognize",
  "items": [
    {{
      "rank": 1,
      "name": "section title",
      "narration": "350-450 word deep exploration with research + Indian examples",
      "key_points": ["Key insight 1", "Key insight 2", "Key insight 3"],
      "summary": "One validating takeaway",
      "category": "{category}"
    }}
  ],
  "outro_script": "100-word warm wrap-up — normalize seeking help + subscribe CTA",
  "full_script": "Complete narration: intro + all sections + outro concatenated",
  "title": "YouTube title — max 70 chars, psychologically curious hook",
  "description": "250-word description — content overview, resource recommendations, 12 hashtags #Psychology #MentalHealth #IndianPsychology",
  "tags": ["psychology india", "mental health india", "{name}", "mahayuktimind", "therapy india", "self improvement india", "relationship psychology", "narcissism india", "attachment theory india", "trauma india", "psychology hindi", "mindset india"]
}}"""
