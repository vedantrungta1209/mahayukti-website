"""
Base config template — copy this to create a new channel.
Every field here must be defined in the channel config.
"""

# ── Identity ──────────────────────────────────────────────────────────────────
CHANNEL_ID   = "template"          # lowercase, no spaces — used for file names and secrets
CHANNEL_NAME = "Mahayukti Template"
CHANNEL_HANDLE = "@mahayuktitemplate"
TOKEN_ENV_VAR  = "YOUTUBE_TEMPLATE_TOKEN_JSON"  # GitHub secret name

# ── Channel character ─────────────────────────────────────────────────────────
NICHE = "One sentence describing what this channel covers and who it's for."
VIDEO_STYLE = (
    "Visual style adjectives for Wan prompts — e.g. "
    "'dark cinematic, dramatic lighting, Indian context, bold colours'"
)

# ── Audio ─────────────────────────────────────────────────────────────────────
# edge-tts voice name. Options (all free, no API key):
#   en-IN-NeerjaNeural   — Indian English female, warm (recommended)
#   en-IN-PrabhatNeural  — Indian English male, clear
#   en-US-AriaNeural     — American female, expressive
#   en-US-GuyNeural      — American male, neutral
#   en-GB-SoniaNeural    — British female, precise
VOICE = "en-IN-NeerjaNeural"

# ── Visual branding ───────────────────────────────────────────────────────────
PRIMARY_HEX = "#00C864"   # Channel brand colour for watermark bar

# ── Topics ────────────────────────────────────────────────────────────────────
# Topics are cycled through in order using a counter file.
# Add as many as you want — the counter wraps around.

SHORT_TOPICS = [
    {"name": "Topic for a short video", "category": "General"},
]

LONG_TOPICS = [
    {
        "name": "Full topic name for a long-form video",
        "category": "General",
        "angle": "The specific angle, argument, or narrative for this episode",
    },
]
