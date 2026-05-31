"""
Mahayukti Business — Indian startup & business case studies.
@mahayuktibusiness | 3 Long-form/week (Mon/Wed/Fri)
"""

CHANNEL_ID     = "business"
CHANNEL_NAME   = "Mahayukti Business"
CHANNEL_HANDLE = "@mahayuktibusiness"
TOKEN_ENV_VAR  = "YOUTUBE_BUSINESS_TOKEN_JSON"
TOKEN_FILE     = "business_token.json"
SECRET_NAME    = "YOUTUBE_BUSINESS_TOKEN_JSON"

# ── AI Character ─────────────────────────────────────────────────────────
CHARACTER_NAME      = "Arjun"
CHARACTER_BIO       = "35-year-old ex-IIM MBA turned startup analyst from Mumbai. Has evaluated 200+ Indian startups and brings razor-sharp financial analysis to every story."
CHARACTER_STYLE     = "Authoritative but accessible English, like a brilliant analyst friend. Uses data and specific numbers. Occasionally drops a sharp Hindi phrase for emphasis."
CHARACTER_IMAGE_URL = "https://raw.githubusercontent.com/vedantrungta1209/mahayukti-website/main/channels/characters/business.jpg"

ELEVENLABS_VOICE_ID = "ErXwobaYiN019PkySvjV"   # Antoni — deep authoritative male

SHORT_VOICE = "en-IN-NeerjaNeural"
LONG_VOICE  = "en-IN-PrabhatNeural"

SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
LONG_WIDTH   = 1920
LONG_HEIGHT  = 1080
FPS          = 24
OUTPUT_DIR   = "output"

BG_COLOR      = (4, 12, 28)
BG_COLOR_2    = (8, 22, 50)
PRIMARY_COLOR = (41, 98, 255)
ACCENT_COLOR  = (255, 200, 50)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (100, 130, 180)

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
    "Quick Commerce":  ((3, 10, 25),  (6, 20, 50),   (41, 98, 255),  (100, 180, 255)),
    "Fintech":         ((3, 15, 10),  (6, 30, 20),   (0, 200, 150),  (0, 255, 200)),
    "EdTech":          ((15, 5, 3),   (30, 10, 6),   (255, 100, 0),  (255, 180, 50)),
    "D2C Brand":       ((15, 3, 10),  (30, 6, 20),   (255, 50, 150), (255, 150, 200)),
    "SaaS":            ((3, 10, 20),  (6, 20, 40),   (80, 150, 255), (150, 200, 255)),
    "Logistics":       ((10, 10, 3),  (20, 20, 6),   (200, 180, 0),  (255, 230, 0)),
    "Healthcare":      ((3, 15, 8),   (6, 30, 16),   (0, 180, 120),  (0, 255, 180)),
    "Food & Beverage": ((20, 5, 3),   (40, 10, 6),   (255, 80, 0),   (255, 150, 50)),
    "Ride-hailing":    ((5, 3, 20),   (10, 6, 40),   (150, 50, 255), (200, 150, 255)),
    "General":         ((4, 12, 28),  (8, 22, 50),   (41, 98, 255),  (255, 200, 50)),
}

CTA_LINE1  = "Subscribe for"
CTA_LINE2  = "business deep dives"
CTA_SUBTEXT = "New Indian startup story every week"

LONG_INTRO_BADGE = "INDIA BUSINESS DEEP DIVE"
OUTRO_LINE1      = "Subscribe now!"
OUTRO_LINE2      = "New case study every week"
OUTRO_BELL_TEXT  = "Ring the bell — Mon, Wed & Fri uploads"

LONG_ALSO_GENERATES_SHORT = False

AFFILIATE_PROGRAMS = [
    {"name": "Zerodha",      "commission": "₹300 per account opening",             "link_placeholder": "https://zerodha.com/open-account/?c=YOUR_CODE"},
    {"name": "Groww",        "commission": "₹100-500 per account + investment",    "link_placeholder": "https://app.groww.in/v3cO/YOUR_REF"},
    {"name": "Zoho One",     "commission": "15% recurring on subscriptions",        "link_placeholder": "https://www.zoho.com/affiliates/"},
    {"name": "Razorpay",     "commission": "₹500 per business signup",             "link_placeholder": "https://razorpay.com/referral/YOUR_CODE"},
    {"name": "Notion",       "commission": "50% first payment",                    "link_placeholder": "https://affiliate.notion.so/YOUR_ID"},
    {"name": "Morning Brew", "commission": "$3-10 per newsletter subscriber",      "link_placeholder": "https://morningbrew.com/daily/r/YOUR_ID"},
]


def bg_prompt(category: str, topic_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Quick Commerce":  f"electric blue neon city lights fast delivery urban india night {orientation} cinematic no text no people",
        "Fintech":         f"digital payment UPI mobile phone glowing green teal dark background {orientation} cinematic no text no people",
        "EdTech":          f"student laptop books glowing orange digital learning india {orientation} cinematic no text no people",
        "D2C Brand":       f"product packaging premium beauty retail shelf neon pink dark {orientation} cinematic no text no people",
        "SaaS":            f"computer screen code dashboard dark mode blue glow software {orientation} cinematic no text no people",
        "Logistics":       f"warehouse trucks supply chain india dark blue industrial {orientation} cinematic no text no people",
        "Healthcare":      f"hospital medical tech digital health app green blue clean {orientation} cinematic no text no people",
        "Food & Beverage": f"restaurant kitchen food india saffron orange vibrant {orientation} cinematic no text no people",
        "Ride-hailing":    f"city traffic night india uber driver phone gps purple neon {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"corporate boardroom india skyscraper blue gold business success {orientation} cinematic no text no people")


LONG_TOPICS = [
    {"name": "How Zepto Built India's Fastest Growing Startup in 2 Years", "category": "Quick Commerce", "sector": "Quick Commerce", "angle": "10-minute delivery model, dark stores, massive funding"},
    {"name": "Why Byju's Collapsed — The Real Inside Story", "category": "EdTech", "sector": "EdTech", "angle": "Aggressive sales, overvaluation, COVID sugar rush, governance failure"},
    {"name": "How Zomato Beat Swiggy and Won India's Food Wars", "category": "Food & Beverage", "sector": "Food Delivery", "angle": "Blinkit acquisition, Hyperpure, international retreat, IPO"},
    {"name": "Zerodha: How Two Brothers Built India's Biggest Broker with Zero Marketing", "category": "Fintech", "sector": "Discount Brokerage", "angle": "No ads, tech-first, Nithin Kamath's philosophy"},
    {"name": "OYO's Rise and Fall — Lessons from India's Unicorn Disaster", "category": "General", "sector": "Hospitality Tech", "angle": "Rapid international expansion, SoftBank pressure, COVID collapse"},
    {"name": "PhonePe vs Paytm — India's Brutal UPI War", "category": "Fintech", "sector": "Payments", "angle": "Walmart money, Paytm's IPO disaster, NPCI regulations"},
    {"name": "How boAt Became India's #1 Audio Brand Without a Factory", "category": "D2C Brand", "sector": "Consumer Electronics", "angle": "Aman Gupta, asset-light model, Shark Tank effect"},
    {"name": "Flipkart's Story: From Books to ₹1.35 Lakh Crore Walmart Exit", "category": "General", "sector": "E-commerce", "angle": "Amazon threat, Big Billion Days, Walmart acquisition"},
    {"name": "CRED's Business Model — How They Make Money (Nobody Knows)", "category": "Fintech", "sector": "Fintech", "angle": "Negative revenue model, data play, brand aspirations"},
    {"name": "Mamaearth: How a Mother Built a ₹10,000 Crore Brand", "category": "D2C Brand", "sector": "D2C Beauty", "angle": "Ghazal Alagh, toxin-free positioning, Shark Tank, IPO"},
    {"name": "How Swiggy Built and Destroyed ₹1,000 Crore in Dark Stores", "category": "Food & Beverage", "sector": "Quick Commerce", "angle": "Instamart pivot, vs Zomato Blinkit, heavy losses"},
    {"name": "Paytm's IPO Disaster — What Went Wrong?", "category": "Fintech", "sector": "Fintech", "angle": "₹2,150 crore loss on listing day, RBI action, Vijay Shekhar Sharma"},
    {"name": "Meesho: How They Made 100 Million Indians Sell Online", "category": "General", "sector": "Social Commerce", "angle": "WhatsApp reselling, Tier 3 India, $4.9B valuation"},
    {"name": "Razorpay's Journey to India's #1 Payment Gateway", "category": "Fintech", "sector": "Payments", "angle": "Harshad and Shashank story, B2B only, Y Combinator"},
    {"name": "Jio: The Telecom Disruption That Changed India Forever", "category": "General", "sector": "Telecom", "angle": "Free internet, 4G disruption, Airtel/Vodafone collapse"},
    {"name": "Urban Company: Turning Home Services into a ₹5,000 Crore Business", "category": "General", "sector": "Home Services", "angle": "Hyperlocal gig model, quality control, international expansion"},
    {"name": "PolicyBazaar: Making Indians Buy Insurance Online", "category": "Fintech", "sector": "Insurtech", "angle": "Yashish Dahiya, aggregator model, PB Fintech IPO"},
    {"name": "How Nykaa Disrupted India's Beauty Industry", "category": "D2C Brand", "sector": "Beauty E-commerce", "angle": "Falguni Nayar at 50, omnichannel strategy, IPO premium"},
    {"name": "Ola vs Uber India — Who's Actually Winning?", "category": "Ride-hailing", "sector": "Ride-hailing", "angle": "Driver economics, Bhavish Aggarwal, EV pivot, Ola Electric"},
    {"name": "Dunzo's Death — Why ₹1,500 Crore Wasn't Enough", "category": "Quick Commerce", "sector": "Quick Commerce", "angle": "Unit economics failure, Reliance investment, operational chaos"},
    {"name": "How Delhivery Built India's Largest Logistics Network", "category": "Logistics", "sector": "Logistics", "angle": "B2B e-commerce infrastructure, IPO, SoftBank backing"},
    {"name": "Lenskart: Disrupting India's ₹20,000 Crore Eyewear Market", "category": "D2C Brand", "sector": "D2C Eyewear", "angle": "Peyush Bansal, own manufacturing, Shark Tank, SoftBank"},
    {"name": "PharmEasy vs Netmeds: India's Online Pharmacy War", "category": "Healthcare", "sector": "Online Pharmacy", "angle": "Funding cycles, Flipkart vs API Holdings, supply chain"},
    {"name": "Groww's Rise: How a Fintech Beat HDFC Securities in 5 Years", "category": "Fintech", "sector": "Wealth Management", "angle": "UX-first investing, SIP culture, Gen Z investors"},
    {"name": "Classplus: The EdTech That Survived When Byju's Didn't", "category": "EdTech", "sector": "EdTech", "angle": "Tutor enablement model, B2B not B2C, sustainable growth"},
    {"name": "India's Startup Funding Winter — What Really Happened", "category": "General", "sector": "Venture Capital", "angle": "2021 FOMO → 2022-23 crash, valuation resets, what survived"},
    {"name": "Amazon India vs Flipkart — 10 Years of E-commerce War", "category": "General", "sector": "E-commerce", "angle": "Investment amounts, market share, festive season battles"},
    {"name": "Wakefit: D2C Mattress Startup Taking on Sleepyhead and Springfit", "category": "D2C Brand", "sector": "D2C Furniture", "angle": "100-night trial, DTC model, Chaitanya Ramalingegowda"},
    {"name": "NPCI — The Silent Giant Powering India's Digital Payments", "category": "Fintech", "sector": "Payments Infrastructure", "angle": "UPI architecture, how it works, global expansion"},
    {"name": "How MakeMyTrip Survived Booking.com and Rebuilt India Travel", "category": "General", "sector": "OTA", "angle": "Deep Kalra, consolidation with Goibibo, post-COVID rebound"},
]


LONG_PROMPT_TEMPLATE = """You are India's most watched business analyst on YouTube — think FinancialWisdom + Backstage with Millionaires style.
Create a deep-dive case study: "{name}"

Sector: {sector}
Core angle: {angle}

Rules:
- Total narration: 2000-2500 words (15-20 min at normal pace)
- Language: Clear English with occasional Hindi phrases — like talking to a sharp friend
- Structure: Start with a dramatic hook → origin story → peak → crisis/turning point → lessons
- Use REAL numbers: valuations, funding rounds, revenue figures, employee counts
- Be analytically honest — what worked AND what failed
- Include 3-4 specific lessons any entrepreneur or investor can apply
- Make it BINGE-WORTHY — this is a mini documentary in audio form
- End with "what happens next" — current state and future outlook

Return valid JSON:
{{
  "episode_title": "{name}",
  "intro_script": "150-word dramatic hook — start in the middle of the most dramatic moment, then pull back",
  "items": [
    {{
      "rank": 1,
      "name": "section title (e.g. 'The Origin Story', 'The Explosive Growth', 'The Crisis')",
      "narration": "400-500 word narrative with real facts, numbers, and storytelling",
      "key_points": ["Key fact or stat 1", "Key fact or stat 2", "Key fact or stat 3"],
      "summary": "One sharp analytical takeaway from this section",
      "category": "{category}"
    }}
  ],
  "outro_script": "100-word wrap-up: lessons for founders + investors + strong subscribe CTA",
  "full_script": "Complete narration: intro + all sections + outro concatenated",
  "title": "YouTube title — max 70 chars, includes company name, provocative angle, emoji",
  "description": "300-word description — summary, timestamps, key lessons, 12 hashtags #IndianStartup #BusinessCaseStudy #StartupIndia",
  "tags": ["indian startup", "business case study", "startup india", "{name}", "entrepreneur india", "mahayuktibusiness", "business analysis india", "startup failure india", "unicorn india", "business documentary india", "how startup works india", "venture capital india"]
}}"""
