"""Zero-latency keyword-based domain classifier for HustleScale.

Routes user queries to the appropriate business domain specialist:
- business_plan: full plan generation with budget, break-even, pricing
- finance: financial literacy, record-keeping, loans, savings
- marketing: marketing strategies, customer acquisition, branding
- risk: risk assessment, insurance, contingency planning
- market_prices: current market prices for trade goods
- success_stories: inspiration from real youth entrepreneurs
- funding: grants, youth funds, micro-loans, VSLAs
- cooperative: group businesses, bulk buying, SACCOs
- general: general business advice and encouragement
"""

from __future__ import annotations

import re

from .state import RouteDecision

# Domain keyword sets — tuned for Ugandan youth micro-enterprise context
DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "business_plan": {
        "business plan", "plan", "start", "startup", "begin", "launch",
        "idea", "budget", "capital", "investment", "break even", "breakeven",
        "how much", "cost", "money needed", "requirements",
        # Luganda
        "ntandikire", "pulani", "bizinensi",
        # Swahili
        "mpango", "biashara", "kuanzisha",
    },
    "finance": {
        "save", "saving", "savings", "loan", "borrow", "interest", "debt",
        "record", "bookkeeping", "accounting", "profit", "loss", "revenue",
        "cash flow", "expense", "bank", "sacco", "mobile money",
        "financial", "money management", "reinvest",
        # Luganda
        "ssente", "okuteekawo", "okuwola", "bbanka",
        # Swahili
        "akiba", "mkopo", "faida", "hasara",
    },
    "marketing": {
        "market", "marketing", "customer", "sell", "selling", "sales",
        "advertise", "advertising", "promote", "promotion", "brand",
        "social media", "whatsapp", "facebook", "poster", "flyer",
        "price", "pricing", "discount", "competition", "competitor",
        # Luganda
        "okutunda", "bakasitoma", "omuguzi",
        # Swahili
        "soko", "wateja", "kuuza", "bei",
    },
    "risk": {
        "risk", "risks", "danger", "dangers", "fail", "failure", "problem",
        "challenge", "challenges", "insurance", "loss", "theft", "disaster",
        "flood", "drought", "competition", "threat", "contingency",
        "backup plan", "what could go wrong", "pitfall", "obstacle",
        # Luganda
        "akabi", "obuzibu", "okugwa",
        # Swahili
        "hatari", "tatizo", "bima",
    },
    "market_prices": {
        "price", "prices", "how much", "cost of", "market price", "current price",
        "what is the price", "how much does", "how much is",
        "chicken", "poultry", "maize", "beans", "rice", "cement",
        "airtime", "data bundle", "charcoal", "tomato", "onion",
        "sugar", "flour", "cooking oil", "paraffin", "timber",
        "salon", "hair", "fabric", "cloth", "thread",
        # Luganda
        "emiwendo", "bbeeyi", "enkoko", "kasooli",
        # Swahili
        "bei", "kuku", "mahindi",
    },
    "success_stories": {
        "success story", "success", "inspiration", "inspire", "example",
        "who has", "someone who", "role model", "mentor", "story",
        "youth who", "young person who", "started from",
        # Luganda
        "ekyokulabirako", "omuntu eyafuuka",
        # Swahili
        "hadithi ya mafanikio", "mfano",
    },
    "funding": {
        "fund", "funding", "grant", "grants", "loan", "loans",
        "government fund", "youth fund", "ylp", "emyooga", "uwep", "pdm",
        "parish development", "microfinance", "brac", "finca",
        "vsla", "sacco", "capital", "where to get money",
        "how to get funding", "apply for", "sponsor",
        # Luganda
        "enfuna", "okusaba ssente",
        # Swahili
        "mfuko", "ruzuku",
    },
    "cooperative": {
        "cooperative", "coop", "group business", "group buying",
        "pool money", "pool resources", "together", "partnership",
        "sacco", "vsla", "joint venture", "collective",
        "bulk buying", "combine", "team up",
        # Luganda
        "okukola wamu", "ekibinja",
        # Swahili
        "ushirika", "kikundi",
    },
}

# Non-business indicators — route to gentle redirect
NON_BUSINESS_INDICATORS: set[str] = {
    "dating", "boyfriend", "girlfriend", "love", "sex",
    "politics", "election", "vote", "president",
    "gambling", "betting", "casino", "lottery",
    "hack", "crack", "pirate", "torrent",
    "weapon", "gun", "knife", "fight",
}

# Multilingual bridge — expand non-English tokens
_MULTILINGUAL_BRIDGE: dict[str, str] = {
    # Luganda
    "ntandikire": "start",
    "bizinensi": "business",
    "ssente": "money",
    "okutunda": "sell",
    "enkoko": "chicken",
    "kasooli": "maize",
    "bbeeyi": "price",
    "emiwendo": "prices",
    "okuteekawo": "save",
    "okuwola": "borrow",
    "bakasitoma": "customers",
    "omuguzi": "buyer",
    "akabi": "risk",
    "obuzibu": "problem",
    "pulani": "plan",
    # Swahili
    "biashara": "business",
    "mpango": "plan",
    "kuanzisha": "start",
    "soko": "market",
    "bei": "price",
    "kuku": "chicken",
    "mahindi": "maize",
    "wateja": "customers",
    "kuuza": "sell",
    "akiba": "savings",
    "mkopo": "loan",
    "faida": "profit",
    "hasara": "loss",
    "hatari": "risk",
    "bima": "insurance",
    # Runyankole
    "okurangura": "buy",
    "okugurisha": "sell",
    "enshonga": "problem",
    "omupango": "plan",
}


def classify(query: str) -> RouteDecision:
    """Classify a user query into a business domain."""
    query_lower = query.lower().strip()
    tokens = set(re.findall(r"\w+", query_lower))

    # Expand multilingual tokens
    expanded = set()
    for token in tokens:
        if token in _MULTILINGUAL_BRIDGE:
            expanded.add(_MULTILINGUAL_BRIDGE[token])
    tokens = tokens | expanded

    # Check non-business content
    non_biz_hits = tokens & NON_BUSINESS_INDICATORS
    if len(non_biz_hits) >= 2:
        return RouteDecision(
            route="redirect",
            confidence=0.9,
            reason=f"Non-business content detected: {', '.join(non_biz_hits)}",
        )

    # Score each domain
    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        hits = []
        for kw in keywords:
            if " " in kw:
                # Multi-word keyword
                if kw in query_lower:
                    score += 2
                    hits.append(kw)
            elif kw in tokens:
                score += 1
                hits.append(kw)
        scores[domain] = score
        matched[domain] = hits

    total = sum(scores.values())
    if total == 0:
        if len(tokens) < 3:
            return RouteDecision(
                route="clarify",
                confidence=0.5,
                reason="Query too short or ambiguous — ask for more detail",
            )
        return RouteDecision(
            route="general",
            domain="general",
            confidence=0.3,
            reason="No strong domain signal — use general business coaching",
        )

    best_domain = max(scores, key=lambda k: scores[k])
    confidence = scores[best_domain] / max(total, 1)

    return RouteDecision(
        route=best_domain,
        domain=best_domain,
        confidence=round(confidence, 2),
        reason=f"Keyword match: {best_domain} ({scores[best_domain]} hits)",
        keywords_matched=matched.get(best_domain, []),
    )
