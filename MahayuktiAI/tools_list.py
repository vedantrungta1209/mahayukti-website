"""
Curated AI tools list for Mahayukti AI channel.
Each tool rotates through Shorts (1 per day) and Long-form (5 per episode).
"""

TOOLS = [
    # ── Productivity & Writing ─────────────────────────────────────────────
    {"name": "ChatGPT",         "category": "Productivity",     "maker": "OpenAI",      "pricing": "Free + $20/mo Plus",          "india_available": True,  "india_note": "Works in India; needs card for paid plan"},
    {"name": "Claude",          "category": "Productivity",     "maker": "Anthropic",   "pricing": "Free + $20/mo Pro",           "india_available": True,  "india_note": "Fully available; UPI not accepted"},
    {"name": "Gemini",          "category": "Productivity",     "maker": "Google",      "pricing": "Free + $20/mo Advanced",      "india_available": True,  "india_note": "Best India integration; works with Google Workspace"},
    {"name": "Microsoft Copilot","category": "Productivity",    "maker": "Microsoft",   "pricing": "Free; $30/mo for 365 Copilot","india_available": True,  "india_note": "Integrated into Windows 11 and Office 365"},
    {"name": "Perplexity AI",   "category": "Search",           "maker": "Perplexity",  "pricing": "Free + $20/mo Pro",           "india_available": True,  "india_note": "Works in India; excellent for research"},
    {"name": "Notion AI",       "category": "Productivity",     "maker": "Notion",      "pricing": "$10/mo add-on",               "india_available": True,  "india_note": "Popular among Indian startups and students"},
    {"name": "Jasper AI",       "category": "Writing",          "maker": "Jasper",      "pricing": "From $49/mo",                 "india_available": True,  "india_note": "Best for marketing teams; pricey for individuals"},
    {"name": "Copy.ai",         "category": "Writing",          "maker": "Copy.ai",     "pricing": "Free + $49/mo",               "india_available": True,  "india_note": "Great free tier; good for short-form content"},
    {"name": "Writesonic",      "category": "Writing",          "maker": "Writesonic",  "pricing": "Free + from $16/mo",          "india_available": True,  "india_note": "Has India-specific pricing; good value"},
    {"name": "Grammarly AI",    "category": "Writing",          "maker": "Grammarly",   "pricing": "Free + $12/mo Premium",       "india_available": True,  "india_note": "Very popular in India for English writing"},

    # ── Image Generation ──────────────────────────────────────────────────
    {"name": "Midjourney",      "category": "Image AI",         "maker": "Midjourney",  "pricing": "From $10/mo",                 "india_available": True,  "india_note": "Via Discord; needs card; worth every rupee"},
    {"name": "DALL-E 3",        "category": "Image AI",         "maker": "OpenAI",      "pricing": "Included in ChatGPT Plus",    "india_available": True,  "india_note": "Best quality; bundled with ChatGPT Plus"},
    {"name": "Adobe Firefly",   "category": "Image AI",         "maker": "Adobe",       "pricing": "25 credits/mo free",          "india_available": True,  "india_note": "Commercially safe images; great for designers"},
    {"name": "Canva AI",        "category": "Image AI",         "maker": "Canva",       "pricing": "Free + ₹3999/yr Pro",         "india_available": True,  "india_note": "India pricing in INR; most popular design tool"},
    {"name": "Leonardo AI",     "category": "Image AI",         "maker": "Leonardo",    "pricing": "Free + from $12/mo",          "india_available": True,  "india_note": "Best free tier for image generation"},
    {"name": "Ideogram",        "category": "Image AI",         "maker": "Ideogram",    "pricing": "Free + from $8/mo",           "india_available": True,  "india_note": "Best for text-in-image generation"},
    {"name": "Stable Diffusion","category": "Image AI",         "maker": "Stability AI","pricing": "Free (open source)",          "india_available": True,  "india_note": "Run locally for free; needs decent GPU"},

    # ── Video Generation ──────────────────────────────────────────────────
    {"name": "Runway ML",       "category": "Video AI",         "maker": "Runway",      "pricing": "Free + from $15/mo",          "india_available": True,  "india_note": "Limited free credits; best for short clips"},
    {"name": "Pika Labs",       "category": "Video AI",         "maker": "Pika",        "pricing": "Free + from $8/mo",           "india_available": True,  "india_note": "Great for social media video generation"},
    {"name": "Kling AI",        "category": "Video AI",         "maker": "Kuaishou",    "pricing": "Free credits available",      "india_available": True,  "india_note": "Chinese product; works globally; strong quality"},
    {"name": "HeyGen",          "category": "Video AI",         "maker": "HeyGen",      "pricing": "Free + from $24/mo",          "india_available": True,  "india_note": "Best AI avatar videos; popular for explainers"},
    {"name": "Synthesia",       "category": "Video AI",         "maker": "Synthesia",   "pricing": "From $22/mo",                 "india_available": True,  "india_note": "Enterprise favourite; professional AI avatars"},
    {"name": "Descript",        "category": "Video AI",         "maker": "Descript",    "pricing": "Free + from $24/mo",          "india_available": True,  "india_note": "Best for podcast/video editing with AI transcript"},

    # ── Audio & Voice ─────────────────────────────────────────────────────
    {"name": "ElevenLabs",      "category": "Voice AI",         "maker": "ElevenLabs",  "pricing": "Free + from $5/mo",           "india_available": True,  "india_note": "Best AI voice cloning; has Hindi voices"},
    {"name": "Murf AI",         "category": "Voice AI",         "maker": "Murf",        "pricing": "Free + from $29/mo",          "india_available": True,  "india_note": "Has Indian English and Hindi voices"},
    {"name": "Suno AI",         "category": "Music AI",         "maker": "Suno",        "pricing": "Free + from $10/mo",          "india_available": True,  "india_note": "Generate full songs from text; works in India"},
    {"name": "Udio",            "category": "Music AI",         "maker": "Udio",        "pricing": "Free + from $12/mo",          "india_available": True,  "india_note": "Suno competitor; slightly better music quality"},
    {"name": "Adobe Podcast AI","category": "Voice AI",         "maker": "Adobe",       "pricing": "Free in beta",                "india_available": True,  "india_note": "Free AI audio enhancer; removes background noise"},

    # ── Coding ────────────────────────────────────────────────────────────
    {"name": "GitHub Copilot",  "category": "Coding AI",        "maker": "GitHub",      "pricing": "Free for students + $10/mo", "india_available": True,  "india_note": "Free for Indian students with GitHub Education"},
    {"name": "Cursor AI",       "category": "Coding AI",        "maker": "Cursor",      "pricing": "Free + $20/mo Pro",           "india_available": True,  "india_note": "Favourite among Indian developers; VSCode-based"},
    {"name": "Codeium",         "category": "Coding AI",        "maker": "Codeium",     "pricing": "Free forever for individuals","india_available": True,  "india_note": "Best free Copilot alternative; works offline"},
    {"name": "Replit AI",       "category": "Coding AI",        "maker": "Replit",      "pricing": "Free + from $25/mo",          "india_available": True,  "india_note": "Best for beginners; code in browser"},
    {"name": "v0 by Vercel",    "category": "Coding AI",        "maker": "Vercel",      "pricing": "Free + from $10/mo",          "india_available": True,  "india_note": "Generate UI components from text; great for frontend"},

    # ── Automation & Business ─────────────────────────────────────────────
    {"name": "Zapier AI",       "category": "Automation AI",    "maker": "Zapier",      "pricing": "Free + from $20/mo",          "india_available": True,  "india_note": "Most popular automation tool; huge Indian user base"},
    {"name": "Make (Integromat)","category": "Automation AI",   "maker": "Make",        "pricing": "Free + from $9/mo",           "india_available": True,  "india_note": "More powerful than Zapier; better free tier"},
    {"name": "Gamma",           "category": "Presentation AI",  "maker": "Gamma",       "pricing": "Free + from $10/mo",          "india_available": True,  "india_note": "Make presentations/docs from text; beautiful output"},
    {"name": "Beautiful.ai",    "category": "Presentation AI",  "maker": "Beautiful.ai","pricing": "From $12/mo",                "india_available": True,  "india_note": "Smart presentations that auto-design themselves"},
    {"name": "Otter.ai",        "category": "Meeting AI",       "maker": "Otter",       "pricing": "Free + from $17/mo",          "india_available": True,  "india_note": "Best meeting transcription; works with Teams/Meet/Zoom"},
    {"name": "Fireflies.ai",    "category": "Meeting AI",       "maker": "Fireflies",   "pricing": "Free + from $18/mo",          "india_available": True,  "india_note": "Popular in Indian startups for meeting notes"},

    # ── Search & Research ─────────────────────────────────────────────────
    {"name": "Elicit",          "category": "Research AI",      "maker": "Elicit",      "pricing": "Free + from $12/mo",          "india_available": True,  "india_note": "Best for academic research and literature review"},
    {"name": "Consensus AI",    "category": "Research AI",      "maker": "Consensus",   "pricing": "Free + from $9/mo",           "india_available": True,  "india_note": "Search scientific papers with AI; great for students"},
    {"name": "You.com",         "category": "Search",           "maker": "You.com",     "pricing": "Free + from $15/mo",          "india_available": True,  "india_note": "AI search engine with privacy focus"},

    # ── Indian AI Tools ───────────────────────────────────────────────────
    {"name": "Sarvam AI",       "category": "Indian AI",        "maker": "Sarvam",      "pricing": "API-based pricing",           "india_available": True,  "india_note": "Best Indian LLM; supports 10 Indian languages natively"},
    {"name": "Krutrim",         "category": "Indian AI",        "maker": "Ola",         "pricing": "Free in beta",                "india_available": True,  "india_note": "India's first unicorn AI startup; made by Ola founder"},
    {"name": "Bhashini",        "category": "Indian AI",        "maker": "Govt of India","pricing": "Free",                       "india_available": True,  "india_note": "Government AI for Indian language translation — totally free"},
    {"name": "BharatGPT",       "category": "Indian AI",        "maker": "IIT Bombay",  "pricing": "Research access",             "india_available": True,  "india_note": "IIT Bombay-backed; focused on Indian context"},

    # ── Niche & Emerging ──────────────────────────────────────────────────
    {"name": "Luma AI",         "category": "3D/Video AI",      "maker": "Luma",        "pricing": "Free + from $18/mo",          "india_available": True,  "india_note": "Create 3D scenes and AI video; Dream Machine is impressive"},
    {"name": "Magnific AI",     "category": "Image AI",         "maker": "Magnific",    "pricing": "From $39/mo",                 "india_available": True,  "india_note": "AI image upscaling — makes low-res images HD"},
    {"name": "Character.ai",    "category": "Chatbot AI",       "maker": "Character.ai","pricing": "Free + $9.99/mo Plus",        "india_available": True,  "india_note": "Roleplay and character chatbots — huge in India"},
    {"name": "Poe",             "category": "AI Hub",           "maker": "Quora",       "pricing": "Free + from $20/mo",          "india_available": True,  "india_note": "Access 20+ AI models in one place; great for comparison"},
    {"name": "Hugging Face",    "category": "AI Platform",      "maker": "HuggingFace", "pricing": "Free + from $9/mo",           "india_available": True,  "india_note": "GitHub of AI models; free to use thousands of models"},
    {"name": "Replicate",       "category": "AI Platform",      "maker": "Replicate",   "pricing": "Pay per use",                 "india_available": True,  "india_note": "Run any AI model via API; pay only for what you use"},
    {"name": "Tome",            "category": "Presentation AI",  "maker": "Tome",        "pricing": "Free + from $20/mo",          "india_available": True,  "india_note": "AI presentation tool with storytelling focus"},
    {"name": "Whisper",         "category": "Transcription AI", "maker": "OpenAI",      "pricing": "Free (open source)",          "india_available": True,  "india_note": "Best free speech-to-text; works for Hindi and Hinglish"},
    {"name": "Claude Projects", "category": "Productivity",     "maker": "Anthropic",   "pricing": "Included in Claude Pro",      "india_available": True,  "india_note": "Organise AI work by project; remembers context always"},
    {"name": "NotebookLM",      "category": "Research AI",      "maker": "Google",      "pricing": "Free",                        "india_available": True,  "india_note": "Upload any PDF/doc and chat with it — completely free"},
    {"name": "DeepSeek",        "category": "Productivity",     "maker": "DeepSeek",    "pricing": "Free",                        "india_available": True,  "india_note": "Chinese AI — free, powerful, strong at coding and math"},
    {"name": "Grok",            "category": "Productivity",     "maker": "xAI",         "pricing": "Free on X + $16/mo Premium",  "india_available": True,  "india_note": "Elon Musk's AI; real-time X/Twitter data access"},
    {"name": "Napkin AI",       "category": "Visual AI",        "maker": "Napkin",      "pricing": "Free in beta",                "india_available": True,  "india_note": "Turn text into diagrams and visuals automatically — free"},
    {"name": "Lovable",         "category": "Coding AI",        "maker": "Lovable",     "pricing": "Free + from $20/mo",          "india_available": True,  "india_note": "Build full web apps from plain English — no coding needed"},
]


def get_short_tool(index: int) -> dict:
    return TOOLS[index % len(TOOLS)]


def get_long_tools(index: int) -> list[dict]:
    start = (index * 5) % len(TOOLS)
    indices = [(start + i) % len(TOOLS) for i in range(5)]
    return [TOOLS[i] for i in indices]
