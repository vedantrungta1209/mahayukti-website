import os
from dotenv import load_dotenv

load_dotenv()

CHANNEL_NAME   = "Mahayukti AI"
CHANNEL_HANDLE = "@mahayuktiAI"
CHANNEL_TAGLINE = "AI Jo Kaam Aaye."

# Short (portrait) — YouTube Shorts
SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920

# Long-form (landscape) — YouTube regular
LONG_WIDTH  = 1920
LONG_HEIGHT = 1080

FPS = 24

# AI/tech color palette
BG_COLOR      = (8, 8, 20)          # deep dark navy
BG_COLOR_2    = (18, 10, 46)        # dark purple
PRIMARY_COLOR = (139, 92, 246)      # electric purple
ACCENT_COLOR  = (0, 212, 255)       # cyan
TEXT_COLOR    = (255, 255, 255)
SUBTLE_COLOR  = (100, 116, 139)
CARD_COLOR    = (15, 15, 35)

# API keys
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

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
