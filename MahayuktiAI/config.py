import os
from dotenv import load_dotenv

load_dotenv()

CHANNEL_NAME   = "Mahayukti AI"
CHANNEL_HANDLE = "@mahayuktiAI"
CHANNEL_TAGLINE = "AI Jo Kaam Aaye."

# Short (portrait) — YouTube Shorts / Instagram Reels / Facebook Reels
SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920

# Long-form (landscape) — YouTube regular
LONG_WIDTH  = 1920
LONG_HEIGHT = 1080

FPS = 24

# Default fallback palette (overridden per category in frame_generator)
BG_COLOR      = (8, 8, 20)
BG_COLOR_2    = (18, 10, 46)
PRIMARY_COLOR = (139, 92, 246)
ACCENT_COLOR  = (0, 212, 255)
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (100, 116, 139)
CARD_COLOR    = (15, 15, 35)

# Category-specific palettes: (bg_dark, bg_mid, primary, accent)
CATEGORY_PALETTES = {
    "Productivity":     ((5, 10, 30),    (10, 20, 50),   (99, 102, 241),  (167, 139, 250)),
    "Writing":          ((10, 5, 25),    (25, 10, 45),   (168, 85, 247),  (236, 72, 153)),
    "Image AI":         ((25, 5, 15),    (45, 10, 30),   (244, 63, 94),   (251, 146, 60)),
    "Video AI":         ((20, 8, 3),     (40, 20, 5),    (249, 115, 22),  (234, 179, 8)),
    "Voice AI":         ((3, 15, 25),    (5, 30, 50),    (6, 182, 212),   (99, 102, 241)),
    "Music AI":         ((15, 5, 25),    (30, 10, 50),   (192, 38, 211),  (244, 63, 94)),
    "Coding AI":        ((3, 15, 8),     (5, 30, 15),    (16, 185, 129),  (6, 182, 212)),
    "Automation AI":    ((3, 10, 20),    (5, 20, 40),    (59, 130, 246),  (99, 102, 241)),
    "Presentation AI":  ((5, 20, 15),    (10, 40, 30),   (20, 184, 166),  (234, 179, 8)),
    "Meeting AI":       ((10, 15, 5),    (20, 30, 10),   (132, 204, 22),  (20, 184, 166)),
    "Research AI":      ((5, 15, 25),    (10, 30, 50),   (14, 165, 233),  (99, 102, 241)),
    "Search":           ((3, 10, 20),    (6, 20, 40),    (56, 189, 248),  (167, 139, 250)),
    "Indian AI":        ((25, 10, 3),    (45, 20, 5),    (249, 115, 22),  (251, 191, 36)),
    "3D/Video AI":      ((8, 3, 25),     (15, 5, 50),    (139, 92, 246),  (6, 182, 212)),
    "Chatbot AI":       ((5, 5, 25),     (10, 10, 50),   (99, 102, 241),  (244, 63, 94)),
    "AI Hub":           ((3, 15, 20),    (5, 30, 40),    (20, 184, 166),  (167, 139, 250)),
    "AI Platform":      ((5, 10, 25),    (10, 20, 50),   (139, 92, 246),  (16, 185, 129)),
    "Visual AI":        ((20, 3, 15),    (40, 5, 30),    (236, 72, 153),  (251, 146, 60)),
    "Transcription AI": ((3, 18, 15),    (5, 35, 30),    (16, 185, 129),  (14, 165, 233)),
}

# API keys
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")

# Instagram / Facebook cross-posting
IG_USER_ID          = os.getenv("IG_USER_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID          = os.getenv("FB_PAGE_ID", "")

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

OUTPUT_DIR         = "output"
TOKEN_FILE         = "youtube_ai_token.json"
CLIENT_SECRET_FILE = "client_secret.json"
SCOPES             = ["https://www.googleapis.com/auth/youtube.upload"]
