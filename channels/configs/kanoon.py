"""
Mahayukti Kanoon (@mahayuktikanoon) — Indian law, rights, court cases.
3 Long-form/week (Mon/Wed/Sat)
"""

CHANNEL_ID     = "kanoon"
CHANNEL_NAME   = "Mahayukti Kanoon"
CHANNEL_HANDLE = "@mahayuktikanoon"
TOKEN_ENV_VAR  = "YOUTUBE_KANOON_TOKEN_JSON"
TOKEN_FILE     = "kanoon_token.json"
SECRET_NAME    = "YOUTUBE_KANOON_TOKEN_JSON"

# ── AI Character ─────────────────────────────────────────────────────────
CHARACTER_NAME      = "Advocate Sharma"
CHARACTER_BIO       = "45-year-old senior advocate from Delhi High Court with 20 years experience in civil and consumer law. Known for making complex law simple for ordinary citizens."
CHARACTER_STYLE     = "Authoritative but approachable. Like a learned uncle who happens to be a top lawyer. Speaks clean English with occasional Hindi legal terms explained. Never condescending."
CHARACTER_IMAGE_URL = ""

ELEVENLABS_VOICE_ID = "yoZ06aMxZJJ28mfd3POQ"   # Sam — steady authoritative male

SHORT_VOICE = "en-IN-PrabhatNeural"
LONG_VOICE  = "en-IN-PrabhatNeural"

SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
LONG_WIDTH   = 1920
LONG_HEIGHT  = 1080
FPS          = 24
OUTPUT_DIR   = "output"

BG_COLOR      = (12, 8, 2)
BG_COLOR_2    = (25, 18, 4)
PRIMARY_COLOR = (184, 134, 11)
ACCENT_COLOR  = (255, 200, 50)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (180, 150, 80)

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
    "Tenant Rights":    ((8, 5, 2),   (16, 10, 4),  (180, 120, 0),  (255, 180, 0)),
    "Consumer Rights":  ((3, 10, 5),  (6, 20, 10),  (0, 180, 80),   (0, 255, 130)),
    "Criminal Law":     ((10, 3, 3),  (20, 6, 6),   (200, 50, 0),   (255, 100, 0)),
    "Family Law":       ((8, 3, 10),  (16, 6, 20),  (150, 50, 200), (200, 120, 255)),
    "Labour Law":       ((3, 8, 12),  (6, 16, 25),  (0, 150, 200),  (50, 200, 255)),
    "Property Law":     ((10, 8, 3),  (20, 16, 6),  (200, 160, 0),  (255, 220, 0)),
    "RTI":              ((3, 10, 8),  (6, 20, 16),  (0, 180, 150),  (0, 255, 200)),
    "Digital Rights":   ((5, 3, 15),  (10, 6, 30),  (120, 0, 255),  (180, 80, 255)),
    "Court Procedure":  ((8, 6, 2),   (16, 12, 4),  (180, 140, 0),  (255, 200, 50)),
    "General":          ((12, 8, 2),  (25, 18, 4),  (184, 134, 11), (255, 200, 50)),
}

CTA_LINE1  = "Subscribe to"
CTA_LINE2  = "know your rights"
CTA_SUBTEXT = "New legal guide every Mon, Wed & Sat"

LONG_INTRO_BADGE = "KNOW YOUR RIGHTS"
OUTRO_LINE1      = "Know your rights!"
OUTRO_LINE2      = "Subscribe for legal knowledge"
OUTRO_BELL_TEXT  = "Ring the bell — new guide every Mon, Wed & Sat"

LONG_ALSO_GENERATES_SHORT = False

AFFILIATE_PROGRAMS = [
    {"name": "LegalKart",    "commission": "₹500-1000 per consultation booking",   "link_placeholder": "https://www.legalkart.com/?ref=YOUR_CODE"},
    {"name": "VakilSearch",  "commission": "₹300-800 per service",                 "link_placeholder": "https://vakilsearch.com/?ref=YOUR_CODE"},
    {"name": "QuickCompany", "commission": "₹500 per company registration",        "link_placeholder": "https://www.quickcompany.in/?ref=YOUR_CODE"},
    {"name": "Notary/Document services", "commission": "₹200-500 per document",   "link_placeholder": "https://www.registrationwala.com/?ref=YOUR_CODE"},
    {"name": "Law Books (Amazon)", "commission": "8% on books",                    "link_placeholder": "https://www.amazon.in/s?k=indian+law+books&linkCode=ll2&tag=YOUR-TAG"},
]


def bg_prompt(category: str, topic_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Tenant Rights":    f"apartment building rental contract India golden dark justice {orientation} cinematic no text no people",
        "Consumer Rights":  f"consumer court india scales of justice golden teal dark {orientation} cinematic no text no people",
        "Criminal Law":     f"police handcuffs FIR station india dramatic dark red {orientation} cinematic no text no people",
        "Family Law":       f"family court marriage divorce documents india purple dark {orientation} cinematic no text no people",
        "Labour Law":       f"workers labour union india factory dark blue justice {orientation} cinematic no text no people",
        "Property Law":     f"property documents land India registration court golden {orientation} cinematic no text no people",
        "RTI":              f"government files papers RTI India transparency teal dark {orientation} cinematic no text no people",
        "Digital Rights":   f"digital privacy phone data India cyber court purple {orientation} cinematic no text no people",
        "Court Procedure":  f"indian court high court supreme court dark mahogany golden {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"indian court law justice scales dark gold classic {orientation} cinematic no text no people")


LONG_TOPICS = [
    {"name": "Tenant Rights in India — What Your Landlord Cannot Do", "category": "Tenant Rights", "law": "Rent Control Acts, Transfer of Property Act", "key_rights": "Notice period, deposit return, no arbitrary eviction"},
    {"name": "Consumer Rights — How to File a Consumer Court Case", "category": "Consumer Rights", "law": "Consumer Protection Act 2019", "key_rights": "Defective products, service deficiency, e-commerce complaints"},
    {"name": "Your Rights When Arrested by Police in India", "category": "Criminal Law", "law": "CrPC Sections 41, 50, 54, Article 22", "key_rights": "Right to know charges, right to lawyer, right to medical exam"},
    {"name": "How to File an RTI — Complete Step-by-Step Guide", "category": "RTI", "law": "Right to Information Act 2005", "key_rights": "Any Indian can ask any government — process, fees, timeline"},
    {"name": "Property Registration and Sale — Know Your Rights", "category": "Property Law", "law": "Registration Act 1908, RERA", "key_rights": "Sale agreement, stamp duty, fraud protection, RERA complaints"},
    {"name": "Divorce Laws in India — Mutual Consent and Contested", "category": "Family Law", "law": "Hindu Marriage Act, Special Marriage Act", "key_rights": "Grounds, timeline, alimony, child custody"},
    {"name": "Labour Rights Every Employee Must Know", "category": "Labour Law", "law": "Industrial Disputes Act, Shops & Establishments", "key_rights": "Minimum wage, PF, gratuity, wrongful termination"},
    {"name": "How to File an FIR — Police Cannot Refuse This Right", "category": "Criminal Law", "law": "CrPC Section 154, Lalita Kumari judgment", "key_rights": "Zero FIR, online FIR, when police must register FIR"},
    {"name": "RERA — Home Buyers' Rights Against Builders", "category": "Property Law", "law": "Real Estate Regulation Act 2016", "key_rights": "Delayed possession, refund rights, quality defects"},
    {"name": "Bail Rights in India — Bailable vs Non-Bailable Offences", "category": "Criminal Law", "law": "CrPC Sections 436-439", "key_rights": "Who can grant bail, conditions, anticipatory bail"},
    {"name": "Women's Rights Under Domestic Violence Act", "category": "Family Law", "law": "Protection of Women from Domestic Violence Act 2005", "key_rights": "Protection order, residence rights, maintenance, child custody"},
    {"name": "Section 498A IPC — Dowry Harassment Law Explained", "category": "Family Law", "law": "IPC Section 498A, Dowry Prohibition Act", "key_rights": "What constitutes cruelty, misuse concerns, recent SC judgments"},
    {"name": "Senior Citizens' Rights in India — Complete Guide", "category": "General", "law": "Maintenance and Welfare of Parents and Senior Citizens Act 2007", "key_rights": "Maintenance from children, property protection, old age homes"},
    {"name": "Medical Negligence — Your Rights Against Doctors and Hospitals", "category": "Consumer Rights", "law": "Consumer Protection Act, IPC 304A, MCI guidelines", "key_rights": "Informed consent, second opinion right, compensation claims"},
    {"name": "Cyber Crime Complaint — How to Report Online Fraud in India", "category": "Digital Rights", "law": "IT Act 2000, Cyber Crime Prevention Rules", "key_rights": "cybercrime.gov.in, helpline 1930, bank fraud reversal rights"},
    {"name": "Road Accident — MACT Claims and Insurance Rights", "category": "Consumer Rights", "law": "Motor Vehicles Act, MACT", "key_rights": "Third-party insurance, no-fault liability, claim timeline"},
    {"name": "Child Rights in India — POCSO and Juvenile Justice", "category": "Criminal Law", "law": "POCSO Act 2012, JJ Act 2015", "key_rights": "Child abuse reporting, anonymity rights, Childline 1098"},
    {"name": "Privacy Rights and Data Protection in India", "category": "Digital Rights", "law": "IT Act SPDI Rules, DPDP Act 2023", "key_rights": "Right to delete data, consent requirements, grievance officer"},
    {"name": "Cheque Bounce — Your Rights Under NI Act 138", "category": "Court Procedure", "law": "Negotiable Instruments Act Section 138", "key_rights": "Notice timeline, filing complaint, imprisonment provision"},
    {"name": "Hindu Succession Act — Property Inheritance Rights", "category": "Property Law", "law": "Hindu Succession Act 1956 (Amendment 2005)", "key_rights": "Daughters' equal right, ancestral vs self-acquired, will basics"},
    {"name": "Gratuity Rights — Every Employee Must Know This", "category": "Labour Law", "law": "Payment of Gratuity Act 1972", "key_rights": "5 year threshold, formula, nominee, denial recourse"},
    {"name": "Your Rights in a Bank — RBI Ombudsman Complaints", "category": "Consumer Rights", "law": "Banking Ombudsman Scheme, RBI guidelines", "key_rights": "Fraud reversal, ATM dispute, loan harassment, complaint process"},
    {"name": "Legal Heir Certificate — How to Get It and Why It Matters", "category": "Court Procedure", "law": "Various state acts, High Court procedure", "key_rights": "Death certificate → legal heir → succession certificate chain"},
    {"name": "Noise Pollution Rights — You Can Act Against Loud Neighbours", "category": "General", "law": "Noise Pollution Rules 2000, IPC 268", "key_rights": "Permissible limits, filing complaint, court injunction"},
    {"name": "Gig Worker Rights — Swiggy Zomato Ola Drivers' Legal Rights", "category": "Labour Law", "law": "Code on Social Security 2020, Rajasthan Gig Workers Act", "key_rights": "Deactivation policy, accident insurance, social security"},
    {"name": "NRI Property Rights in India — All You Need to Know", "category": "Property Law", "law": "FEMA, Succession Acts, RBI circular", "key_rights": "What NRI can own, power of attorney, inheritance"},
    {"name": "Will Writing in India — Complete Guide", "category": "Property Law", "law": "Indian Succession Act, Hindu Succession Act", "key_rights": "Registered vs unregistered will, witnesses, contesting a will"},
    {"name": "Right to Education Act — Parents' and Students' Rights", "category": "General", "law": "Right to Education Act 2009", "key_rights": "25% EWS reservation, no detention policy, corporal punishment ban"},
    {"name": "Employer Cannot Do This — Employment Law Rights", "category": "Labour Law", "law": "Industrial Employment Act, Equal Remuneration Act", "key_rights": "Illegal deductions, forced overtime, discriminatory termination"},
    {"name": "Defamation Law in India — When Can You Sue Someone?", "category": "Court Procedure", "law": "IPC 499-500, Civil defamation", "key_rights": "Criminal vs civil defamation, online defamation, WhatsApp forwards"},
]


LONG_PROMPT_TEMPLATE = """You are India's most trusted legal educator on YouTube — making complex law simple and actionable.
Create a "Know Your Rights" guide: "{name}"

Applicable laws: {law}
Key rights covered: {key_rights}

Rules:
- Total narration: 1600-2000 words (12-15 min at clear teaching pace)
- Language: Clear Hindi + English mix — like a lawyer friend explaining over chai
- Tone: Empowering, practical, non-intimidating — NOT like a legal textbook
- Structure: The right/law → Who it applies to → Exactly how to use it → Common mistakes → What to do if violated
- Use REAL case examples or scenarios Indians face daily
- Include: specific section numbers, official portal names, helpline numbers
- Make it ACTIONABLE — someone should finish this video knowing exactly what to do
- Disclaimer: "Yeh general legal education hai — specific advice ke liye lawyer se consult karein"

Return valid JSON:
{{
  "episode_title": "{name}",
  "intro_script": "150-word scenario hook — describe a situation where this right is being violated RIGHT NOW by thousands of Indians",
  "items": [
    {{
      "rank": 1,
      "name": "section title (e.g. 'What the Law Says', 'Who Can Use This Right', 'Step-by-Step Process', 'Common Violations', 'What To Do If Denied')",
      "narration": "350-400 word clear explanation with legal sections + real India examples",
      "key_points": ["Specific right or step 1", "Specific right or step 2", "Specific right or step 3"],
      "summary": "One-line empowering takeaway",
      "category": "{category}"
    }}
  ],
  "outro_script": "100-word empowering close — remind viewers of their rights + subscribe CTA",
  "full_script": "Complete narration: intro + all sections + outro concatenated",
  "title": "YouTube title — max 70 chars, rights-empowering hook, emoji",
  "description": "300-word description — what rights covered, section references, helplines, 12 hashtags #KnowYourRights #IndianLaw #LegalRights",
  "tags": ["know your rights india", "indian law explained", "legal rights india", "{name}", "mahayuktikanoon", "kanoon india", "legal help india", "indian court", "consumer rights india", "tenant rights india", "labour law india", "RTI india"]
}}"""
