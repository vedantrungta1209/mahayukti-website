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
# Kokoro ONNX voice ID. Options:
#   af_heart  — American female, warm, clear (good default)
#   af_sky    — American female, bright, upbeat
#   am_adam   — American male, neutral
#   am_michael — American male, deep, authoritative
#   bf_emma   — British female, precise
#   bm_george — British male, calm
VOICE = "af_heart"

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
