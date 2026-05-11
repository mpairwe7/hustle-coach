"""Query rewriting — synonym expansion, spell correction, and domain normalization.

Transforms raw user queries into optimized retrieval queries:
- Domain-specific abbreviation expansion (VSLA, SACCO, YLP, etc.)
- Common misspelling correction for business domain terms
- Query normalization (lowercasing, whitespace cleanup)
- Contextual rewriting from conversation history (coreference resolution)
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain abbreviation expansion
# ---------------------------------------------------------------------------
_ABBREVIATIONS: dict[str, str] = {
    "vsla": "Village Savings and Loan Association (VSLA)",
    "sacco": "Savings and Credit Cooperative Organization (SACCO)",
    "ylp": "Youth Livelihood Programme (YLP)",
    "uwep": "Uganda Women Entrepreneurship Programme (UWEP)",
    "pdm": "Parish Development Model (PDM)",
    "emyooga": "Emyooga Presidential Initiative on Wealth Creation",
    "ugx": "Ugandan Shillings (UGX)",
    "usd": "US Dollars (USD)",
    "roi": "Return on Investment (ROI)",
    "bep": "Break-Even Point (BEP)",
    "nssf": "National Social Security Fund (NSSF)",
    "kcca": "Kampala Capital City Authority (KCCA)",
    "unbs": "Uganda National Bureau of Standards (UNBS)",
    "uia": "Uganda Investment Authority (UIA)",
    "ura": "Uganda Revenue Authority (URA)",
    "tin": "Taxpayer Identification Number (TIN)",
    "vat": "Value Added Tax (VAT)",
    "momo": "Mobile Money (MTN MoMo / Airtel Money)",
    "coc": "Certificate of Compliance",
    "sme": "Small and Medium Enterprise (SME)",
    "bds": "Business Development Services (BDS)",
}

# ---------------------------------------------------------------------------
# Common misspellings in the URA domain
# ---------------------------------------------------------------------------
_CORRECTIONS: dict[str, str] = {
    "buisness": "business",
    "bussiness": "business",
    "busines": "business",
    "bussines": "business",
    "entrepeneur": "entrepreneur",
    "enterpreneur": "entrepreneur",
    "entreprener": "entrepreneur",
    "poultrey": "poultry",
    "polutry": "poultry",
    "tailoring": "tailoring",
    "tailorng": "tailoring",
    "investement": "investment",
    "investmet": "investment",
    "fundng": "funding",
    "fundin": "funding",
    "savigs": "savings",
    "savngs": "savings",
    "cooperatve": "cooperative",
    "cooparative": "cooperative",
    "marketting": "marketing",
    "marketng": "marketing",
    "budjet": "budget",
    "buget": "budget",
    "proffit": "profit",
    "prfit": "profit",
    "registeration": "registration",
    "registation": "registration",
    "regester": "register",
    "licencing": "licensing",
    "licencse": "license",
    "agricluture": "agriculture",
    "agirculture": "agriculture",
    "complience": "compliance",
    "compiance": "compliance",
    "decleration": "declaration",
    "declaraton": "declaration",
    "importaton": "importation",
    "clearence": "clearance",
    "clearanse": "clearance",
    "objection": "objection",
    "obejction": "objection",
    "receipting": "receipting",
    "receiping": "receipting",
    "invoiceing": "invoicing",
}


def expand_abbreviations(query: str) -> str:
    """Expand known abbreviations inline for better retrieval recall."""
    words = query.split()
    expanded = []
    for w in words:
        key = w.lower().strip(".,;:?!\"'()")
        if key in _ABBREVIATIONS:
            # Preserve trailing punctuation
            suffix = w[len(w.rstrip(".,;:?!\"'()")) :]
            expanded.append(_ABBREVIATIONS[key] + suffix)
        else:
            expanded.append(w)
    return " ".join(expanded)


def correct_spelling(query: str) -> str:
    """Fix common domain-specific misspellings."""
    result = query
    for wrong, right in _CORRECTIONS.items():
        result = re.sub(re.escape(wrong), right, result, flags=re.IGNORECASE)
    return result


def normalize(query: str) -> str:
    """Whitespace and basic cleanup."""
    return re.sub(r"\s+", " ", query.strip())


def rewrite_with_history(
    query: str,
    history: list[dict[str, str]],
) -> str:
    """Resolve coreferences using conversation history.

    Simple heuristic: if the query contains pronouns like "it", "that",
    "this", "they" without a clear subject, prepend context from the
    last assistant reply.
    """
    if not history:
        return query

    pronoun_pattern = re.compile(
        r"\b(it|that|this|they|them|those|its|their|the above|the same)\b",
        re.IGNORECASE,
    )

    if pronoun_pattern.search(query):
        last_turn = history[-1]
        last_bot = last_turn.get("bot_reply", "")
        # Extract first sentence as context hint (handle abbreviations with periods)
        first_sentence = re.split(r"(?<=[^A-Z])[.!?]\s", last_bot)[0].strip()
        if first_sentence and len(first_sentence) > 10:
            rewritten = f"Regarding '{first_sentence[:100]}': {query}"
            logger.debug("Query rewritten: %s → %s", query, rewritten)
            return rewritten

    return query


def rewrite(
    query: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Full query rewriting pipeline."""
    q = normalize(query)
    q = correct_spelling(q)
    q = expand_abbreviations(q)
    if history:
        q = rewrite_with_history(q, history)
    return q
