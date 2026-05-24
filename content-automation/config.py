import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Mahayukti")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE", "@WeAreMahayukti")
CHANNEL_TAGLINE = "Sahi Salah. Sahi Raasta."

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 24

# Color palette — dark finance theme
BG_COLOR = (13, 17, 23)
BG_COLOR_2 = (20, 27, 45)
PRIMARY_COLOR = (0, 211, 149)   # emerald green
ACCENT_COLOR = (255, 180, 0)    # gold
TEXT_COLOR = (255, 255, 255)
SUBTLE_COLOR = (100, 116, 139)

# Brand aliases
BRAND_GREEN = PRIMARY_COLOR
BRAND_GOLD = ACCENT_COLOR
BRAND_DARK = BG_COLOR

# Font search paths (Ubuntu / GitHub Actions)
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

OUTPUT_DIR = "output"
TOKEN_FILE = "youtube_token.json"
CLIENT_SECRET_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
