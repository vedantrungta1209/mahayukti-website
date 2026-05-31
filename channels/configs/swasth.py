"""
Mahayukti Swasth (@mahayuktiswasth) — health & wellness for Indians.
3 Long-form/week (Tue/Thu/Sat)
"""

CHANNEL_ID     = "swasth"
CHANNEL_NAME   = "Mahayukti Swasth"
CHANNEL_HANDLE = "@mahayuktiswasth"
TOKEN_ENV_VAR  = "YOUTUBE_SWASTH_TOKEN_JSON"
TOKEN_FILE     = "swasth_token.json"
SECRET_NAME    = "YOUTUBE_SWASTH_TOKEN_JSON"

# ── AI Character ─────────────────────────────────────────────────────────
CHARACTER_NAME      = "Dr. Anjali"
CHARACTER_BIO       = "38-year-old health educator and wellness researcher from Mumbai with a Masters in Public Health. Has spent 12 years translating complex medical research into actionable advice for Indian families."
CHARACTER_STYLE     = "Warm, caring, science-based. Like a doctor friend who gives you real answers, not textbook ones. Uses Indian food and lifestyle examples naturally. Always ends with something the viewer can do TODAY."
CHARACTER_IMAGE_URL = "https://raw.githubusercontent.com/vedantrungta1209/mahayukti-website/main/channels/characters/swasth.jpg"

ELEVENLABS_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"   # Bella — warm caring female

SHORT_VOICE = "en-IN-NeerjaNeural"
LONG_VOICE  = "en-IN-NeerjaNeural"

SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
LONG_WIDTH   = 1920
LONG_HEIGHT  = 1080
FPS          = 24
OUTPUT_DIR   = "output"

BG_COLOR      = (2, 12, 10)
BG_COLOR_2    = (4, 25, 20)
PRIMARY_COLOR = (20, 184, 166)
ACCENT_COLOR  = (110, 231, 183)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (100, 200, 180)

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
    "Diabetes":        ((2, 10, 8),  (4, 20, 16),  (0, 180, 150),  (0, 255, 200)),
    "Heart Health":    ((12, 3, 3),  (25, 6, 6),   (220, 60, 60),  (255, 120, 120)),
    "Sleep":           ((4, 4, 15),  (8, 8, 30),   (80, 80, 200),  (150, 150, 255)),
    "Nutrition":       ((4, 12, 3),  (8, 25, 6),   (100, 200, 0),  (160, 255, 0)),
    "Mental Health":   ((8, 4, 12),  (16, 8, 25),  (150, 80, 220), (200, 150, 255)),
    "Thyroid":         ((10, 8, 2),  (20, 16, 4),  (200, 160, 0),  (255, 220, 50)),
    "Gut Health":      ((3, 12, 5),  (6, 25, 10),  (0, 200, 80),   (50, 255, 130)),
    "Women's Health":  ((12, 4, 8),  (25, 8, 16),  (220, 60, 120), (255, 140, 180)),
    "Senior Health":   ((4, 10, 12), (8, 20, 25),  (0, 160, 200),  (50, 220, 255)),
    "General":         ((2, 12, 10), (4, 25, 20),  (20, 184, 166), (110, 231, 183)),
}

CTA_LINE1  = "Subscribe for"
CTA_LINE2  = "health knowledge"
CTA_SUBTEXT = "New health guide every week"

LONG_INTRO_BADGE = "DOCTOR EXPLAINS"
OUTRO_LINE1      = "Stay healthy!"
OUTRO_LINE2      = "New health guide every week"
OUTRO_BELL_TEXT  = "Ring the bell — new video every Tue, Thu & Sat"

LONG_ALSO_GENERATES_SHORT = False

AFFILIATE_PROGRAMS = [
    {"name": "Healthkart",    "commission": "5-8% on supplements",                  "link_placeholder": "https://www.healthkart.com/offers/referral?utm_source=YOUR_CODE"},
    {"name": "Cult.fit",      "commission": "₹300-500 per membership signup",       "link_placeholder": "https://cult.fit/partner/YOUR_CODE"},
    {"name": "1mg Health",    "commission": "₹200-400 per lab test booking",        "link_placeholder": "https://www.1mg.com/referral?code=YOUR_CODE"},
    {"name": "Apollo 247",    "commission": "₹150-300 per consultation",            "link_placeholder": "https://www.apollo247.com/?ref=YOUR_CODE"},
    {"name": "MuscleBlaze",   "commission": "8% on protein supplement sales",       "link_placeholder": "https://www.muscleblaze.com/referral/YOUR_CODE"},
    {"name": "Health Books (Amazon)", "commission": "8% on books",                  "link_placeholder": "https://www.amazon.in/s?k=health+wellness+india&linkCode=ll2&tag=YOUR-TAG"},
]


def bg_prompt(category: str, topic_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Diabetes":        f"blood sugar test glucose meter insulin teal blue dark health {orientation} cinematic no text no people",
        "Heart Health":    f"heart ECG monitor red glow healthy heart clean medical {orientation} cinematic no text no people",
        "Sleep":           f"sleeping bedroom dark blue calm peaceful moonlight {orientation} cinematic no text no people",
        "Nutrition":       f"fresh vegetables fruits indian food colourful healthy green {orientation} cinematic no text no people",
        "Mental Health":   f"meditation calm nature green peaceful indian person {orientation} cinematic no text no people",
        "Thyroid":         f"thyroid gland neck anatomy medical illustration teal dark {orientation} cinematic no text no people",
        "Gut Health":      f"gut microbiome bacteria digestive system green teal dark {orientation} cinematic no text no people",
        "Women's Health":  f"women health yoga calm nature india pink teal {orientation} cinematic no text no people",
        "Senior Health":   f"senior indian couple walking morning park healthy aging teal {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"health wellness doctor india teal green clean modern medical {orientation} cinematic no text no people")


LONG_TOPICS = [
    {"name": "Diabetes Management Without Medication — What Actually Works", "category": "Diabetes", "audience": "Type 2 diabetics, pre-diabetics, family members", "focus": "Diet changes, exercise, sleep — evidence-based non-drug interventions"},
    {"name": "Heart Attack Warning Signs Indians Miss", "category": "Heart Health", "audience": "Adults 35+, families of heart patients", "focus": "Unusual symptoms in Indians, jaw pain, indigestion, women's symptoms"},
    {"name": "Why Indians Sleep Wrong — and How to Fix It", "category": "Sleep", "audience": "Working professionals, parents, students", "focus": "Circadian rhythm, screen blue light, Indian lifestyle habits"},
    {"name": "Vitamin D Deficiency in India — Almost Everyone Has It", "category": "Nutrition", "audience": "All Indians", "focus": "Despite sunny India, why deficiency is epidemic — testing, supplements, foods"},
    {"name": "Thyroid Problems — Symptoms, Testing, Management", "category": "Thyroid", "audience": "Women 25-55, weight management seekers", "focus": "Hypothyroidism in Indian women, TSH levels, medication, diet"},
    {"name": "Gut Health and Why It Matters More Than You Think", "category": "Gut Health", "audience": "General health-conscious Indians", "focus": "Microbiome, IBS in India, probiotics, what to eat"},
    {"name": "High Blood Pressure in Young Indians — The Silent Epidemic", "category": "Heart Health", "audience": "Young Indians 25-45, parents", "focus": "Rising hypertension in India, stress link, DASH diet, monitoring"},
    {"name": "PCOD/PCOS — Complete Guide for Indian Women", "category": "Women's Health", "audience": "Indian women 18-40", "focus": "Symptoms, causes, diet, exercise, fertility, medication options"},
    {"name": "What to Eat for Strong Immunity — India-Specific", "category": "Nutrition", "audience": "All Indians, especially post-COVID", "focus": "Haldi, ginger, tulsi science, Vitamin C sources, protein for immunity"},
    {"name": "Cholesterol — What Your Blood Test Results Mean", "category": "Heart Health", "audience": "Adults 30+ with cholesterol concerns", "focus": "LDL vs HDL vs triglycerides, Indian ranges, diet vs medication"},
    {"name": "Fatty Liver Disease — India's Growing Problem", "category": "General", "audience": "Urban Indians, alcohol users, diabetics", "focus": "NAFLD vs AFLD, symptoms, reversal, lifestyle"},
    {"name": "Back Pain Relief — What Works for Indians", "category": "General", "audience": "Office workers, IT professionals, seniors", "focus": "Posture, exercises, yoga, when to see a doctor, mattress choice"},
    {"name": "Kidney Stone Prevention — Complete Indian Diet Guide", "category": "General", "audience": "Stone-prone individuals, northern Indians", "focus": "Types, hydration, oxalate foods, Indian diet adjustments"},
    {"name": "Stress and Cortisol — How Stress Is Killing Indians", "category": "Mental Health", "audience": "Working professionals, parents", "focus": "Cortisol effects on body, chronic stress signs, de-stress methods"},
    {"name": "Eye Care for Screen Users — Office Syndrome Guide", "category": "General", "audience": "IT professionals, students, children", "focus": "20-20-20 rule, blue light glasses debate, nutrition, exercises"},
    {"name": "Protein Needs for Indian Vegetarians", "category": "Nutrition", "audience": "Indian vegetarians, fitness beginners", "focus": "Complete proteins, daal+rice combo, paneer, soya, supplements"},
    {"name": "Menopause — What Indian Women Need to Know", "category": "Women's Health", "audience": "Women 40-60", "focus": "Symptoms timeline, HRT debate, diet, bone health, emotional wellbeing"},
    {"name": "Cancer Warning Signs Indians Should Not Ignore", "category": "General", "audience": "Adults 35+, smokers, high-risk individuals", "focus": "India's top 5 cancers, early signs, when to get checked"},
    {"name": "Intermittent Fasting for Indians — Does It Work?", "category": "Nutrition", "audience": "Weight management seekers, diabetics, general", "focus": "16:8 method, Indian meal timing, how to adapt to Indian eating culture"},
    {"name": "Senior Health at 60+ — Staying Active and Independent", "category": "Senior Health", "audience": "Seniors and their adult children", "focus": "Falls prevention, muscle loss, memory maintenance, vaccinations"},
    {"name": "Hair Fall in Indians — Real Causes and Solutions", "category": "General", "audience": "Young Indians 20-40, especially women", "focus": "Nutrition deficiencies, thyroid, stress, DHT — what actually helps"},
    {"name": "Anxiety Disorders in India — Symptoms and Management", "category": "Mental Health", "audience": "Young working professionals, students", "focus": "GAD vs panic attacks, India's stigma, therapy, medication, breathing"},
    {"name": "Childhood Nutrition Mistakes Indian Parents Make", "category": "Nutrition", "audience": "Parents of children 2-15", "focus": "Too much sugar, junk food, under-nutrition patterns, building healthy habits"},
    {"name": "Bone Health — Why Indians Suffer from Early Bone Loss", "category": "Senior Health", "audience": "Women 35+, seniors, fitness seekers", "focus": "Calcium absorption, Vitamin D, weight-bearing exercise, osteoporosis"},
    {"name": "Liver Health — Alcohol, Medication, and Indian Food Impact", "category": "General", "audience": "Adults concerned about liver health", "focus": "SGOT/SGPT levels, foods that hurt/help, jaundice warning signs"},
    {"name": "Healthy Ageing — What 80-Year-Old Healthy Indians Do Differently", "category": "Senior Health", "audience": "Adults 40-70 planning for old age", "focus": "Centenarian research, Indian lifestyle medicine, Blue Zone lessons"},
    {"name": "Managing Diabetes During Festivals and Weddings", "category": "Diabetes", "audience": "Diabetics and their families", "focus": "Smart choices at mithai, biryani situations, alcohol, blood sugar spikes"},
    {"name": "Hormonal Health for Indian Men — Testosterone and More", "category": "General", "audience": "Indian men 30-55", "focus": "Declining testosterone in India, symptoms, lifestyle optimization, when to test"},
    {"name": "Mental Health During Pregnancy — Postpartum Too", "category": "Women's Health", "audience": "Pregnant women, new mothers, husbands", "focus": "Anxiety in pregnancy, postpartum depression India, support system"},
    {"name": "UTI Prevention for Indian Women", "category": "Women's Health", "audience": "Indian women who get recurrent UTIs", "focus": "Causes, hygiene habits, hydration, D-mannose, antibiotics resistance"},
]


LONG_PROMPT_TEMPLATE = """You are a warm, trustworthy Indian health educator — like a doctor friend who explains things clearly.
Create a health guide: "{name}"

Target audience: {audience}
Focus areas: {focus}

Rules:
- Total narration: 1600-2000 words (12-15 min at calm, clear pace)
- Language: Clear English + Hindi medical terms explained — warm, reassuring tone
- Tone: Like a caring doctor friend — NOT scary, NOT preachy
- Structure: What is this condition/topic → How it shows up in Indians → What the science says → What to eat/do/avoid → When to see a doctor
- India-specific: Use Indian food names, common Indian lifestyle habits, Indian medical system
- Include: practical daily habits, meal examples, exercise suggestions
- Important disclaimer: "This is health education, not medical advice. Consult your doctor for treatment."
- Do NOT recommend specific drug brands

Return valid JSON:
{{
  "episode_title": "{name}",
  "intro_script": "150-word empathetic opener — describe the problem this video solves in Indian daily life",
  "items": [
    {{
      "rank": 1,
      "name": "section title (e.g. 'Understanding the Problem', 'What Science Says', 'Indian Diet Changes', 'Exercise Plan', 'When to See a Doctor')",
      "narration": "350-400 word warm, practical health education with India-specific examples",
      "key_points": ["Practical tip 1", "Practical tip 2", "Key fact to remember"],
      "summary": "One warm, empowering takeaway",
      "category": "{category}"
    }}
  ],
  "outro_script": "100-word empowering close — you have the power to change your health + subscribe CTA",
  "full_script": "Complete narration: intro + all sections + outro concatenated",
  "title": "YouTube title — max 70 chars, health problem + solution, emoji",
  "description": "300-word description — what viewer will learn, India context, disclaimer, 12 hashtags #HealthIndia #DiabetesIndia #HealthTips",
  "tags": ["health india", "health tips india", "{name}", "mahayuktiswasth", "indian health", "diabetes india", "heart health india", "nutrition india", "wellness india", "ayurveda india", "doctor explains india", "health advice india"]
}}"""
