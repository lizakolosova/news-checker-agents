from typing import Tuple

LOW_SIGNAL_DOMAINS: Tuple[str, ...] = (
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "pinterest.com",
    "reddit.com",
    "quora.com",
    "twitter.com",
    "x.com",
)

GOVERNMENT_MARKERS: Tuple[str, ...] = (
    ".gov", ".gouv", ".gov.uk", ".gv.", ".stat.",
    "europa.eu", ".int", ".parliament", ".senate", ".congress"
)

REPUTABLE_NEWS_MARKERS: Tuple[str, ...] = (
    "reuters.com", "apnews.com", "bbc.com", "nytimes.com",
    "ft.com", "bloomberg.com", "wsj.com", "theguardian.com",
    "economist.com", "washingtonpost.com", "npr.org",
)

AUTHORITY_WEIGHTS = {
    "government": 0.9,
    "news": 0.6,
    "default": 0.0,
}

QUALITY_WEIGHTS = {
    "relevance": 0.6,
    "size": 0.4,
}

DEFAULT_MIN_EVIDENCE = 3
DEFAULT_MAX_EVIDENCE = 10
DEFAULT_PER_QUERY_RESULTS = 3
DEFAULT_MAX_QUERIES = 5

MIN_RELEVANCE_AUTHORITY = 0.35
MIN_RELEVANCE_NEWS = 0.30

AUTHORITY_RELEVANCE_WEIGHT = 0.7
AUTHORITY_WEIGHT_CONTRIBUTION = 0.3

SEARCH_TIMEOUT_SECONDS = 15
SERPER_ENDPOINT = "https://google.serper.dev/search"

LLM_TEMPERATURE = 0.1
LLM_MODEL_GROQ = "llama-3.3-70b-versatile"
LLM_MODEL_OLLAMA = "llama3"

QUALITY_MIN_SOURCES = 5

SNIPPET_MAX_LENGTH = 300
TITLE_MAX_LENGTH = 160
SNIPPET_DISPLAY_MAX_LENGTH = 1200

DOMAIN_CATEGORIES = (
    "government_statistics",
    "entertainment",
    "sports",
    "corporate",
    "mixed",
    "other"
)