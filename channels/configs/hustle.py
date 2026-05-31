"""
Mahayukti Hustle — side hustle & income channel config.
@mahayuktihustle | 2 Shorts/day + 2 Long/week
"""
import os

CHANNEL_ID     = "hustle"
CHANNEL_NAME   = "Mahayukti Hustle"
CHANNEL_HANDLE = "@mahayuktihustle"
TOKEN_ENV_VAR  = "YOUTUBE_HUSTLE_TOKEN_JSON"
TOKEN_FILE     = "hustle_token.json"
SECRET_NAME    = "YOUTUBE_HUSTLE_TOKEN_JSON"

# ── AI Character ─────────────────────────────────────────────────────────
CHARACTER_NAME      = "Raj"
CHARACTER_BIO       = "27-year-old serial side-hustler from Pune who has personally tried 40+ income streams and now teaches others. Speaks from experience, not theory."
CHARACTER_STYLE     = "Energetic Hinglish, fast-paced, like your smartest friend who earns ₹5 lakh/month extra. Uses phrases like 'yaar', 'sach mein', 'try kar ke dekho'. Never preachy."
CHARACTER_IMAGE_URL = "https://raw.githubusercontent.com/vedantrungta1209/mahayukti-website/main/channels/characters/hustle.jpg"   # set to a stable URL of Raj's AI-generated photo (upload to GitHub releases)

# ElevenLabs voice — https://elevenlabs.io/voice-library
# Suggested: "Josh" (pNInz6obpgDQGcFmaJgB) for energetic male, or use a custom cloned voice
ELEVENLABS_VOICE_ID = "pNInz6obpgDQGcFmaJgB"   # Josh — energetic male (update with preferred voice)

SHORT_VOICE = "en-IN-NeerjaNeural"    # edge-tts fallback if no ElevenLabs key
LONG_VOICE  = "en-IN-PrabhatNeural"

SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
LONG_WIDTH   = 1920
LONG_HEIGHT  = 1080
FPS          = 24
OUTPUT_DIR   = "output"

BG_COLOR      = (10, 6, 2)
BG_COLOR_2    = (22, 12, 4)
PRIMARY_COLOR = (255, 140, 0)
ACCENT_COLOR  = (255, 215, 0)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (160, 130, 80)

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
    "Freelancing":     ((12, 5, 0),  (25, 10, 0),  (255, 140, 0),  (255, 215, 0)),
    "Reselling":       ((5, 12, 0),  (10, 25, 0),  (100, 200, 0),  (180, 255, 0)),
    "Content":         ((0, 5, 20),  (0, 10, 40),  (0, 150, 255),  (0, 200, 255)),
    "Teaching":        ((10, 0, 15), (20, 0, 30),  (180, 0, 255),  (220, 100, 255)),
    "Delivery":        ((15, 0, 0),  (30, 0, 0),   (255, 60, 0),   (255, 140, 0)),
    "Digital":         ((0, 10, 15), (0, 20, 30),  (0, 200, 200),  (0, 255, 200)),
    "Photography":     ((0, 5, 15),  (0, 10, 30),  (100, 149, 237),(150, 200, 255)),
    "Design":          ((15, 0, 10), (30, 0, 20),  (255, 0, 150),  (255, 100, 200)),
    "Finance":         ((0, 15, 5),  (0, 30, 10),  (0, 200, 100),  (0, 255, 150)),
    "General":         ((10, 8, 3),  (20, 15, 5),  (255, 140, 0),  (255, 215, 0)),
}

CTA_LINE1  = "Follow for"
CTA_LINE2  = "daily side hustles"
CTA_SUBTEXT = "New hustle drop every single day"

LONG_INTRO_BADGE = "COMPLETE INCOME GUIDE"
OUTRO_LINE1      = "Start earning today!"
OUTRO_LINE2      = "New guide every week"
OUTRO_BELL_TEXT  = "Ring the bell — new video every Mon & Thu"

LONG_ALSO_GENERATES_SHORT = False

# ── Monetization — affiliate programs (highest commission first) ──────────
AFFILIATE_PROGRAMS = [
    {"name": "Fiverr",        "commission": "$150 CPA per first-time buyer",       "link_placeholder": "https://go.fiverr.com/visit/?bta=YOUR_ID&brand=fiverrcpa"},
    {"name": "Upwork",        "commission": "$200 per approved freelancer signup",  "link_placeholder": "https://www.upwork.com/ab/signup/contractor/?utm_source=YOUR_REF"},
    {"name": "Teachable",     "commission": "30% recurring on course platform",    "link_placeholder": "https://teachable.com/?via=YOUR_ID"},
    {"name": "Bluehost India","commission": "₹3,000-5,000 per hosting signup",     "link_placeholder": "https://www.bluehost.in/track/YOUR_ID"},
    {"name": "Amazon Associates","commission": "4-8% on all purchases",            "link_placeholder": "https://www.amazon.in/b?&linkCode=ll2&tag=YOUR-TAG"},
    {"name": "Canva Pro",     "commission": "Up to $36 per annual subscriber",     "link_placeholder": "https://partner.canva.com/YOUR_ID"},
]


def bg_prompt(category: str, topic_name: str, portrait: bool) -> str:
    orientation = "vertical portrait" if portrait else "horizontal landscape"
    prompts = {
        "Freelancing":  f"laptop coffee coworking space golden morning light hustle productivity {orientation} cinematic no text no people",
        "Reselling":    f"products packages boxes ecommerce warehouse golden light success {orientation} cinematic no text no people",
        "Content":      f"camera microphone studio setup neon blue purple content creator {orientation} cinematic no text no people",
        "Teaching":     f"blackboard books students learning classroom bright education {orientation} cinematic no text no people",
        "Delivery":     f"motorcycle delivery city streets india evening golden hour {orientation} cinematic no text no people",
        "Digital":      f"computer code screen dark neon digital work from home {orientation} cinematic no text no people",
        "Photography":  f"camera lens bokeh golden hour photography studio professional {orientation} cinematic no text no people",
        "Design":       f"design tools ipad stylus colorful creative workspace inspiration {orientation} cinematic no text no people",
        "Finance":      f"stock market charts money growth investment success golden {orientation} cinematic no text no people",
    }
    return prompts.get(category, f"entrepreneur hustle success money growth dark golden abstract {orientation} cinematic no text no people")


SHORT_TOPICS = [
    {"name": "Freelance Writing on Upwork", "category": "Freelancing", "earning": "₹500-2,000/day", "detail": "No degree needed, just good English and a niche"},
    {"name": "Content Writing on Fiverr", "category": "Freelancing", "earning": "₹300-1,500/day", "detail": "Blog posts, product descriptions, SEO writing"},
    {"name": "Reselling on Meesho", "category": "Reselling", "earning": "₹500-3,000/day", "detail": "Zero investment needed, work from phone"},
    {"name": "YouTube Channel Monetisation", "category": "Content", "earning": "₹5,000-50,000/month", "detail": "AdSense kicks in at 1000 subscribers + 4000 watch hours"},
    {"name": "Online Tutoring on Chegg", "category": "Teaching", "earning": "₹400-800/hour", "detail": "Graduate-level knowledge, flexible hours"},
    {"name": "Instagram Paid Promotions", "category": "Content", "earning": "₹500-10,000/post", "detail": "10K followers is enough to start charging brands"},
    {"name": "Amazon Seller Account", "category": "Reselling", "earning": "₹10,000-1 lakh/month", "detail": "Private label or resell popular products"},
    {"name": "Graphic Design on Canva + Fiverr", "category": "Design", "earning": "₹400-2,000/order", "detail": "Logo, social media posts, pitch decks"},
    {"name": "Video Editing for YouTubers", "category": "Content", "earning": "₹2,000-10,000/video", "detail": "1000s of small YouTubers need editors"},
    {"name": "Swiggy/Zomato Delivery Partner", "category": "Delivery", "earning": "₹600-1,200/day", "detail": "Flexible hours, daily payments via app"},
    {"name": "Social Media Management", "category": "Digital", "earning": "₹8,000-25,000/month per client", "detail": "Small businesses need Instagram + Facebook managers"},
    {"name": "Data Entry on Freelancer.com", "category": "Digital", "earning": "₹200-600/day", "detail": "Simple work, no special skills required"},
    {"name": "Affiliate Marketing via Blog", "category": "Digital", "earning": "₹5,000-50,000/month", "detail": "Amazon Associates, ClickBank India"},
    {"name": "Photography on Shutterstock", "category": "Photography", "earning": "₹2-40 per download", "detail": "Upload once, earn forever — passive income"},
    {"name": "Transcription Work on Rev", "category": "Digital", "earning": "₹700-1,400/hour of audio", "detail": "Type what you hear — English or Hindi"},
    {"name": "Virtual Assistant on Upwork", "category": "Digital", "earning": "₹300-800/hour", "detail": "Calendar, email, research for foreign clients"},
    {"name": "Blogging with AdSense", "category": "Digital", "earning": "₹5,000-2 lakh/month", "detail": "High-traffic niche blogs earn big with Google Ads"},
    {"name": "Print on Demand via Merch", "category": "Design", "earning": "₹100-500 per sale", "detail": "Design once, Amazon prints + ships — zero inventory"},
    {"name": "Facebook Marketplace Flipping", "category": "Reselling", "earning": "₹2,000-15,000/week", "detail": "Buy cheap local items, clean and resell higher"},
    {"name": "Dropshipping from AliExpress", "category": "Reselling", "earning": "₹10,000-80,000/month", "detail": "Sell online without holding any inventory"},
    {"name": "Online Surveys on Toluna", "category": "Digital", "earning": "₹100-500/day", "detail": "Easy side income, best for students"},
    {"name": "Translation Work on Gengo", "category": "Digital", "earning": "₹500-2,000/day", "detail": "Know 2+ languages? This is pure income"},
    {"name": "Selling Digital Products on Gumroad", "category": "Digital", "earning": "₹5,000-1 lakh/month", "detail": "Templates, ebooks, courses — no manufacturing"},
    {"name": "Wedding Photography", "category": "Photography", "earning": "₹15,000-80,000/event", "detail": "One weekend booking = one month salary"},
    {"name": "Web Design for Small Businesses", "category": "Digital", "earning": "₹10,000-50,000/site", "detail": "Wix/WordPress — no coding needed anymore"},
    {"name": "Podcasting with Sponsorships", "category": "Content", "earning": "₹5,000-50,000/episode", "detail": "Niche podcasts with 1K listeners get sponsors"},
    {"name": "App Testing on UserTesting", "category": "Digital", "earning": "₹750-1,500/test", "detail": "Record your screen, give feedback — 15 minutes per test"},
    {"name": "Teaching English Online", "category": "Teaching", "earning": "₹800-2,000/hour", "detail": "Platforms like Preply, iTalki, VIPKid"},
    {"name": "Resume Writing Service", "category": "Digital", "earning": "₹1,000-5,000/resume", "detail": "Freshers + career switchers pay for expert resumes"},
    {"name": "Selling Handmade Crafts on Etsy", "category": "Design", "earning": "₹500-5,000/item", "detail": "Indian handmade items sell globally on Etsy"},
    {"name": "Car Wash at Home", "category": "Delivery", "earning": "₹300-800/car", "detail": "UrbanClap model, 5-10 cars/day in residential areas"},
    {"name": "Tiffin Service from Home", "category": "Delivery", "earning": "₹500-2,000/day", "detail": "20-30 tiffins/day at ₹80-100 each"},
    {"name": "Instagram Reels Viral Strategy", "category": "Content", "earning": "₹5,000-50,000/month", "detail": "Build audience fast with Reels, monetize multiple ways"},
    {"name": "Domain Flipping", "category": "Digital", "earning": "₹5,000-5 lakh/domain", "detail": "Buy cheap .com domains, sell to businesses at 10x"},
    {"name": "Voiceover Work on Voices.com", "category": "Content", "earning": "₹1,000-10,000/project", "detail": "Good Hindi or English voice? Record from home"},
    {"name": "Logo Design on 99designs", "category": "Design", "earning": "₹3,000-15,000/logo", "detail": "Compete for design briefs, win guaranteed payment"},
    {"name": "SEO Freelancing", "category": "Digital", "earning": "₹15,000-60,000/month per client", "detail": "Learn Google's algorithm, sell rankings to businesses"},
    {"name": "Email Marketing for Small Businesses", "category": "Digital", "earning": "₹10,000-40,000/month", "detail": "Build + manage email lists — highly underrated skill"},
    {"name": "Selling Photos on Adobe Stock", "category": "Photography", "earning": "₹80-800/photo", "detail": "India lifestyle photos sell fast on stock platforms"},
    {"name": "Creating Online Courses on Udemy", "category": "Teaching", "earning": "₹5,000-2 lakh/month", "detail": "Record once, earn forever from every new student"},
    {"name": "WhatsApp Reseller Groups", "category": "Reselling", "earning": "₹3,000-20,000/month", "detail": "Buy wholesale, sell to your WhatsApp contacts"},
    {"name": "ChatGPT Prompt Engineering", "category": "Digital", "earning": "₹500-3,000/prompt set", "detail": "Sell AI prompt packs on Gumroad + Etsy"},
    {"name": "Real Estate Photography", "category": "Photography", "earning": "₹3,000-8,000/property", "detail": "Every flat listed needs photos — realtors pay well"},
    {"name": "Selling Stationery on Amazon", "category": "Reselling", "earning": "₹10,000-50,000/month", "detail": "Custom stationery + planners sell consistently"},
    {"name": "Airbnb Property Management", "category": "Digital", "earning": "₹15,000-50,000/month", "detail": "Manage others' properties for 15-20% commission"},
    {"name": "Car Rental via Savaari", "category": "Delivery", "earning": "₹1,500-3,000/day", "detail": "Rent your car when you're not using it"},
    {"name": "Gift Hamper Business from Home", "category": "Design", "earning": "₹5,000-30,000/week", "detail": "Festival season hampers sell massively in India"},
    {"name": "Online Stock Trading", "category": "Finance", "earning": "Variable — ₹5,000+/month possible", "detail": "Zerodha + proper strategy = scalable income"},
    {"name": "Baking and Selling from Home", "category": "Delivery", "earning": "₹3,000-15,000/week", "detail": "Cakes, cookies — social media drives orders locally"},
    {"name": "Tarot/Astrology Consulting", "category": "Digital", "earning": "₹500-3,000/session", "detail": "India's spiritual market is massive — online consultations"},
    {"name": "Coding Bootcamp Tutoring", "category": "Teaching", "earning": "₹500-1,500/hour", "detail": "Help beginners learn Python, Java, web development"},
    {"name": "Pinterest Affiliate Marketing", "category": "Digital", "earning": "₹3,000-30,000/month", "detail": "Pin products, earn commission when people buy"},
    {"name": "Selling Old Books on OLX", "category": "Reselling", "earning": "₹200-2,000/week", "detail": "Textbooks near colleges sell fast every semester"},
    {"name": "3D Printing Small Products", "category": "Design", "earning": "₹300-1,500/item", "detail": "Keychains, custom gifts — sell on Instagram + Etsy"},
    {"name": "Travel Photography Stock", "category": "Photography", "earning": "₹500-5,000/month passive", "detail": "India travel photos are massively demanded globally"},
    {"name": "Podcast Editing Service", "category": "Content", "earning": "₹2,000-8,000/episode", "detail": "Podcast creators outsource editing as they grow"},
    {"name": "Canva Template Selling", "category": "Design", "earning": "₹3,000-25,000/month", "detail": "Instagram, presentation, resume templates sell on Etsy"},
    {"name": "Website Flipping", "category": "Digital", "earning": "₹20,000-5 lakh/flip", "detail": "Build or buy small websites, grow traffic, sell at 25x revenue"},
    {"name": "Cooking Class Online", "category": "Teaching", "earning": "₹2,000-10,000/month", "detail": "Zoom cooking classes — regional cuisine has global demand"},
    {"name": "Nutrition/Fitness Coaching Online", "category": "Teaching", "earning": "₹5,000-20,000/month per client", "detail": "Certification + social proof + WhatsApp coaching"},
    {"name": "Selling UPSC Notes", "category": "Teaching", "earning": "₹5,000-30,000/month", "detail": "Topper notes sell like crazy on Telegram and Gumroad"},
    {"name": "Event Photography", "category": "Photography", "earning": "₹5,000-20,000/event", "detail": "Corporate events, birthdays, product launches"},
    {"name": "Ghostwriting for Bloggers", "category": "Freelancing", "earning": "₹3,000-15,000/article", "detail": "Experienced bloggers outsource writing entirely"},
    {"name": "Meesho Reselling Guide", "category": "Reselling", "earning": "₹5,000-20,000/month", "detail": "Share in WhatsApp groups, zero investment model"},
    {"name": "Shopify Dropshipping India", "category": "Reselling", "earning": "₹15,000-2 lakh/month", "detail": "US market + India suppliers = high margin"},
    {"name": "Selling Flowers Daily", "category": "Delivery", "earning": "₹500-2,000/day", "detail": "Temples + events = constant demand in every city"},
    {"name": "Custom Phone Case Selling", "category": "Design", "earning": "₹3,000-15,000/month", "detail": "Instagram promotions + Meesho fulfillment"},
    {"name": "Teaching Yoga Online", "category": "Teaching", "earning": "₹10,000-40,000/month", "detail": "Morning batch of 20 students at ₹500/class each"},
    {"name": "Language Teaching (French/German)", "category": "Teaching", "earning": "₹600-2,000/hour", "detail": "European language demand surging for MBA/IELTS prep"},
    {"name": "Micro SaaS Tool", "category": "Digital", "earning": "₹5,000-1 lakh/month", "detail": "Simple tools solving one problem — charge ₹199/month"},
    {"name": "Renting Equipment (Camera/Projector)", "category": "Reselling", "earning": "₹1,000-5,000/day", "detail": "Events + students = constant rental demand"},
    {"name": "Interior Design Consulting Online", "category": "Design", "earning": "₹5,000-20,000/consultation", "detail": "WhatsApp video walkthrough + Canva mood board"},
    {"name": "Selling Plants from Home", "category": "Delivery", "earning": "₹3,000-15,000/month", "detail": "Instagram plant page + home delivery in your city"},
    {"name": "Proofreading for Students", "category": "Freelancing", "earning": "₹500-2,000/document", "detail": "Thesis, research papers, college assignments"},
    {"name": "Selling Homemade Pickles/Jams", "category": "Delivery", "earning": "₹5,000-20,000/month", "detail": "Instagram + Swiggy Genie home delivery model"},
    {"name": "Selling Sticker Packs on Etsy", "category": "Design", "earning": "₹2,000-10,000/month", "detail": "India-themed stickers and memes sell globally"},
    {"name": "Digital Marketing Agency", "category": "Digital", "earning": "₹30,000-2 lakh/month", "detail": "Start with 2-3 local business clients"},
    {"name": "YouTube Thumbnail Design", "category": "Design", "earning": "₹200-1,000/thumbnail", "detail": "Every YouTuber needs thumbnails — 1000s of creators"},
    {"name": "Subtitling Videos on Amara", "category": "Digital", "earning": "₹300-800/video", "detail": "Add captions to videos — consistent demand globally"},
    {"name": "Homeopathy Consultation Online", "category": "Teaching", "earning": "₹300-1,500/consultation", "detail": "India's ₹17,000 crore alternative medicine market"},
    {"name": "Selling Excel Templates", "category": "Digital", "earning": "₹2,000-15,000/month", "detail": "Budget planners, business trackers — huge demand"},
    {"name": "Photography Editing Services", "category": "Photography", "earning": "₹100-500/photo", "detail": "Lightroom editing for wedding + real estate photographers"},
    {"name": "Selling on Instagram Shopping", "category": "Reselling", "earning": "₹10,000-50,000/month", "detail": "Direct shopping without website — powerful for India"},
    {"name": "App Development Side Income", "category": "Digital", "earning": "₹20,000-2 lakh/app", "detail": "Simple Android apps for local businesses"},
    {"name": "Bicycle Repair at Home", "category": "Delivery", "earning": "₹300-800/bike", "detail": "Pandemic-era cycling boom is permanent in India"},
    {"name": "Building AI Automations for Businesses", "category": "Digital", "earning": "₹15,000-1 lakh/project", "detail": "ChatGPT + Zapier automations for SMBs"},
    {"name": "Selling Vintage Clothes on OLX/Vinted", "category": "Reselling", "earning": "₹3,000-15,000/month", "detail": "Thrift culture is rising fast in Indian metros"},
    {"name": "Creating WhatsApp Stickers", "category": "Design", "earning": "₹500-3,000/pack", "detail": "Festival + emotion sticker packs sell to local businesses"},
    {"name": "Selling Beauty Products as Reseller", "category": "Reselling", "earning": "₹5,000-25,000/month", "detail": "Modicare, Oriflame, Nykaa reseller programs"},
    {"name": "Running Facebook/Instagram Ads for Local Shops", "category": "Digital", "earning": "₹5,000-20,000/client/month", "detail": "Every kiranastore, salon, restaurant needs digital presence"},
    {"name": "Selling Homemade Candles Online", "category": "Design", "earning": "₹3,000-12,000/month", "detail": "Minimal investment, high perceived value gifting market"},
    {"name": "Ola/Uber Driver", "category": "Delivery", "earning": "₹700-1,500/day", "detail": "Surge hours + incentives can push daily earning high"},
    {"name": "Teaching Music Online", "category": "Teaching", "earning": "₹500-2,000/hour", "detail": "Guitar, tabla, vocals — post-pandemic demand spiked"},
    {"name": "Building Landing Pages for Clients", "category": "Digital", "earning": "₹5,000-25,000/page", "detail": "One-page sites for coaches, consultants, local businesses"},
    {"name": "Airbnb Hosting Your Room", "category": "Delivery", "earning": "₹800-3,000/night", "detail": "Even one spare room earns ₹15,000-50,000/month"},
    {"name": "Upwork Profile Review Service", "category": "Freelancing", "earning": "₹500-2,000/review", "detail": "Help other freelancers optimize their Upwork profile"},
    {"name": "Event Management Side Business", "category": "Digital", "earning": "₹10,000-50,000/event", "detail": "Small local events — birthdays, kitty parties, get-togethers"},
]

LONG_TOPICS = [
    {"name": "Complete Beginner's Guide to Freelancing on Upwork", "category": "Freelancing", "earning_potential": "₹30,000-1 lakh/month", "sections": "Getting Started,Creating a Winning Profile,Finding Your First Client,Pricing Strategy,Scaling to Full-Time"},
    {"name": "How to Start Reselling on Meesho in 2025", "category": "Reselling", "earning_potential": "₹15,000-50,000/month", "sections": "Account Setup,Finding Products,WhatsApp Group Strategy,Handling Orders,Scaling Up"},
    {"name": "YouTube Monetization Complete Guide", "category": "Content", "earning_potential": "₹5,000-5 lakh/month", "sections": "Channel Setup,Content Strategy,Reaching 1000 Subscribers,Enabling AdSense,Beyond AdSense"},
    {"name": "Side Hustle Income Tax Guide for Indians", "category": "Finance", "earning_potential": "Save ₹10,000-50,000/year", "sections": "What Income Is Taxable,Filing ITR as Freelancer,Deductions You Can Claim,Advance Tax,GST Threshold"},
    {"name": "Affiliate Marketing Complete Blueprint", "category": "Digital", "earning_potential": "₹10,000-2 lakh/month", "sections": "Choosing a Niche,Best Programs for India,Content Strategy,SEO Basics,Scaling Up"},
    {"name": "How to Start Dropshipping in India", "category": "Reselling", "earning_potential": "₹20,000-2 lakh/month", "sections": "What Is Dropshipping,Finding Suppliers,Setting Up Shopify,Marketing on Meta,Order Fulfilment"},
    {"name": "Selling Digital Products Online — Full Guide", "category": "Digital", "earning_potential": "₹10,000-1 lakh/month", "sections": "What to Sell,Creating Your Product,Gumroad vs Etsy vs Own Store,Marketing Strategy,Automating Sales"},
    {"name": "How to Build a Photography Side Business", "category": "Photography", "earning_potential": "₹20,000-80,000/month", "sections": "Equipment to Start With,First Clients,Stock Photography,Wedding Niche,Corporate Photography"},
    {"name": "Online Tutoring Complete Business Guide", "category": "Teaching", "earning_potential": "₹15,000-60,000/month", "sections": "Which Subjects to Teach,Choosing a Platform,Setting Your Rate,Getting Reviews,Offline to Online Transition"},
    {"name": "Building a ₹1 Lakh/Month Social Media Agency", "category": "Digital", "earning_potential": "₹50,000-2 lakh/month", "sections": "Picking a Niche,First Clients,Service Offerings,Pricing Packages,Team Building"},
    {"name": "Complete Guide to Amazon FBA in India", "category": "Reselling", "earning_potential": "₹30,000-3 lakh/month", "sections": "Understanding FBA,Product Research,Sourcing,Listing Optimisation,Reviews and Ads"},
    {"name": "How Indians Can Earn in USD Freelancing", "category": "Freelancing", "earning_potential": "$500-3,000/month", "sections": "Best Platforms for USD Income,Positioning for Global Clients,Payment Methods,Tax Implications,Scaling Strategy"},
    {"name": "Starting a Tiffin Service — Full Business Plan", "category": "Delivery", "earning_potential": "₹20,000-60,000/month", "sections": "Legal Requirements,Menu Planning,Finding Customers,Delivery Logistics,Scaling Beyond Kitchen"},
    {"name": "How to Make ₹50,000/Month from Blogging", "category": "Digital", "earning_potential": "₹20,000-2 lakh/month", "sections": "Choosing a Profitable Niche,Setting Up WordPress,SEO Strategy,Monetisation Methods,Timeline Reality Check"},
    {"name": "Building Passive Income Streams as an Indian", "category": "Finance", "earning_potential": "₹10,000-1 lakh/month passive", "sections": "Digital Products,Stock Dividends,Royalties,Affiliate Income,Real Estate Light"},
    {"name": "How to Become a Video Editor and Earn Well", "category": "Content", "earning_potential": "₹20,000-80,000/month", "sections": "Software to Learn,Building a Portfolio,Finding YouTube Clients,Pricing Your Services,Agency Model"},
    {"name": "Instagram Growth Strategy to Monetisation", "category": "Content", "earning_potential": "₹10,000-2 lakh/month", "sections": "Niche Selection,Content Pillars,Algorithm Secrets,Collaboration Strategy,Monetisation at 10K"},
    {"name": "From Zero to Fiverr Top Seller", "category": "Freelancing", "earning_potential": "₹15,000-1 lakh/month", "sections": "Profile Setup,First 5 Reviews,Gig Optimisation,Fiverr SEO,Pro Seller Path"},
    {"name": "How to Start an Online Coaching Business", "category": "Teaching", "earning_potential": "₹30,000-3 lakh/month", "sections": "Choosing Your Coaching Niche,Offer Design,Lead Generation,Sales Call Process,Delivering Results"},
    {"name": "Real Estate Side Hustles in India", "category": "Finance", "earning_potential": "₹20,000-1 lakh/month", "sections": "Referral Agent Model,Airbnb Sub-letting,Property Photography,Real Estate Content Creation,Fractional Investing"},
]


SHORT_PROMPT_TEMPLATE = """You are a viral Indian YouTube Shorts creator specializing in side hustle and income content.
Your shorts regularly get 1M+ views in India.

Create a 60-second "Side Hustle of the Day" Short about: {name}
Earning potential: {earning}
Detail: {detail}

Rules:
- Script MUST be 115-130 words MAX (exactly 60 seconds of speech)
- Language: Hinglish — energetic, aspirational, relatable to young Indians
- HOOK: Open with the earning figure — make it feel possible RIGHT NOW
- Show HOW to start (3 concrete steps anyone can follow today)
- India-specific platforms, apps, and resources only
- End CTA: "Follow @mahayuktihustle — daily side hustle drops"
- Pure value, zero fluff, maximum hustle energy

Return valid JSON:
{{
  "topic_name": "{name}",
  "hook": "First 3-second punchy line with earning figure",
  "script": "Full 60-second narration (115-130 words, Hinglish, high energy)",
  "slides": [
    {{"text": "{name}", "label": "SIDE HUSTLE OF THE DAY"}},
    {{"text": "Step 1 to start — max 10 words", "label": "STEP 1"}},
    {{"text": "Best platform to use — max 10 words", "label": "WHERE TO START"}},
    {{"text": "{earning}", "label": "EARNING POTENTIAL"}},
    {{"text": "Follow @mahayuktihustle for daily side hustles", "label": "FOLLOW US"}}
  ],
  "title": "YouTube title — max 60 chars, include earning figure, emoji",
  "description": "YouTube description — 150 words, step-by-step, India resources, 8 hashtags #SideHustle #MakeMoneyOnline #IndianHustle #Shorts",
  "tags": ["side hustle india", "make money online india", "earn money from home", "side income india", "mahayuktihustle", "{name}", "hustle india", "freelancing india"]
}}"""

LONG_PROMPT_TEMPLATE = """You are a top Indian YouTube educator who teaches practical income skills.
Create a complete guide: "{name}"

Earning potential: {earning_potential}
Sections to cover: {sections}

Rules:
- Total narration: 1800-2200 words (12-15 min at normal pace)
- Language: English with natural Hinglish phrases — like a successful elder brother sharing real advice
- Tone: Direct, practical, honest — no hype, no fluff
- Start with WHY this works in India RIGHT NOW in 2025
- Each section: 300-380 words with concrete, actionable steps
- Include: specific India-friendly apps, websites, payment methods
- Include: one realistic income story (not fake testimonial style)
- Realistic timelines — when will they see first money?
- End with EXACTLY what to do in the next 30 minutes

Return valid JSON:
{{
  "episode_title": "{name}",
  "intro_script": "200-word intro — hook on earning potential + why this works in India now",
  "items": [
    {{
      "rank": 1,
      "name": "section title",
      "narration": "300-380 word narration with step-by-step actions",
      "key_points": ["Actionable point 1", "Actionable point 2", "Actionable point 3"],
      "summary": "One-line key takeaway from this section",
      "category": "{category}"
    }}
  ],
  "outro_script": "100-word strong CTA — one thing to do right now + subscribe CTA",
  "full_script": "Complete narration: intro + all sections + outro concatenated",
  "title": "YouTube title — max 70 chars, include earning figure, click-worthy",
  "description": "250-word description — what viewer will learn, timestamps, India resources, 12 hashtags",
  "tags": ["side hustle india", "make money online 2025", "{name}", "income from home india", "mahayuktihustle", "how to earn money india", "freelancing india 2025", "side income india"]
}}"""
