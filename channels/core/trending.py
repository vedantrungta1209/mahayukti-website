"""
Trending topic detection via YouTube search autocomplete (no API key needed).
Used to replace static round-robin topic selection with real-time search signals.
"""
import json
import urllib.parse
import urllib.request


_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _yt_autocomplete(query: str, geo: str = "IN") -> list[str]:
    """Fetch YouTube search autocomplete suggestions for a query."""
    url = (
        "https://suggestqueries.google.com/complete/search"
        f"?client=youtube&ds=yt&q={urllib.parse.quote(query)}&hl=en&gl={geo}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=8) as r:
        raw = r.read().decode("utf-8")
    data = json.loads(raw)
    if len(data) < 2:
        return []
    results = []
    for item in data[1]:
        term = item[0] if isinstance(item, list) else str(item)
        if term:
            results.append(term)
    return results


def get_trending_topics(seed_queries: list[str], geo: str = "IN", n: int = 5) -> list[str]:
    """
    Fetch trending search suggestions from YouTube for given seed queries.
    Returns up to n unique topic strings, empty list on failure.
    Falls back silently so the caller can use static topics.
    """
    seen: set[str] = set()
    topics: list[str] = []

    for seed in seed_queries:
        try:
            suggestions = _yt_autocomplete(seed, geo)
            for s in suggestions:
                key = s.lower().strip()
                if key and key not in seen and len(s) > 10:
                    seen.add(key)
                    topics.append(s)
                    if len(topics) >= n * 2:
                        break
        except Exception as e:
            print(f"  Trending fetch skip '{seed}': {e}")

    return topics[:n]


# ── Channel-specific helpers ───────────────────────────────────────────────────

FINANCE_SEEDS = [
    "mutual fund india 2025",
    "income tax india 2025",
    "stock market india today",
    "best investment india",
    "SIP investment returns 2025",
]

CRIME_SEEDS = [
    "india crime case 2025",
    "biggest scam india",
    "true crime india documentary",
]

AI_SEEDS = [
    "best AI tool 2025 india",
    "AI news this week",
    "ChatGPT vs Gemini 2025",
    "new AI app 2025",
]


def pick_topic_with_trending(static_topics: list[dict], seeds: list[str],
                              fallback_idx: int = 0) -> dict:
    """
    Try to find a trending search query that matches one of the static topics.
    If a match is found, returns that topic (moved to front of rotation).
    Otherwise returns the static topic at fallback_idx.
    """
    trending = get_trending_topics(seeds, n=10)
    if not trending:
        return static_topics[fallback_idx % len(static_topics)]

    # Check if any trending term substring-matches a static topic name
    for term in trending:
        term_l = term.lower()
        for t in static_topics:
            # Partial keyword overlap check
            topic_words = set(t["name"].lower().split())
            trend_words = set(term_l.split())
            if len(topic_words & trend_words) >= 2:
                print(f"  Trending match: '{term}' → '{t['name']}'")
                return t

    # No match — inject the top trending term as an ad-hoc topic
    top = trending[0]
    print(f"  No static match. Using trending topic: '{top}'")
    return {"name": top, "category": "Trending", "source": "live_trending"}
