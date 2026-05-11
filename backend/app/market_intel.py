"""Local market intelligence for HustleScale.

Provides current prices for common trade goods in Uganda.
Data sourced from market surveys — updated periodically.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

MARKET_PRICES_PATH = os.getenv(
    "MARKET_PRICES_PATH",
    "knowledge-base/market-prices/uganda-prices-2026.json",
)


class MarketIntelligence:
    """In-memory market price lookup."""

    def __init__(self):
        self.prices: list[dict] = []
        self.last_updated: str = ""
        self.categories: set[str] = set()

    def load(self):
        """Load market prices from JSON."""
        path = Path(MARKET_PRICES_PATH)
        if not path.exists():
            # Try relative to script directory
            path = Path(__file__).resolve().parent.parent.parent / "knowledge-base" / "market-prices" / "uganda-prices-2026.json"
        if not path.exists():
            # Try Docker mount path
            path = Path("/app/knowledge-base/market-prices/uganda-prices-2026.json")
        if not path.exists():
            logger.warning("Market prices not found at %s", MARKET_PRICES_PATH)
            return

        try:
            with open(path) as f:
                data = json.load(f)
            self.prices = data.get("prices", [])
            self.last_updated = data.get("last_updated", "unknown")
            self.categories = {p.get("category", "") for p in self.prices}
            logger.info(
                "Loaded %d market prices (updated: %s)",
                len(self.prices),
                self.last_updated,
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load market prices: %s", e)

    def search(
        self,
        query: str | None = None,
        category: str | None = None,
        item: str | None = None,
    ) -> list[dict]:
        """Search prices by category, item name, or free text."""
        results = self.prices

        if category:
            cat_lower = category.lower()
            results = [p for p in results if p.get("category", "").lower() == cat_lower]

        if item:
            item_lower = item.lower()
            # Synonym expansion for common Uganda terms
            synonyms = {
                "chicken": ["broiler", "layer", "poultry", "enkoko", "kuku", "chick"],
                "maize": ["kasooli", "mahindi", "corn"],
                "phone": ["mobile", "simu", "ssimu"],
                "hair": ["salon", "barber", "enviiri", "nywele"],
                "cloth": ["fabric", "kitenge", "tailoring", "thread"],
            }
            search_terms = {item_lower}
            for key, syns in synonyms.items():
                if item_lower in syns or item_lower == key:
                    search_terms.add(key)
                    search_terms.update(syns)

            results = [
                p for p in results
                if any(
                    term in p.get("item", "").lower()
                    or term in p.get("item_lg", "").lower()
                    or term in p.get("item_sw", "").lower()
                    for term in search_terms
                )
            ]

        if query and not category and not item:
            query_lower = query.lower()
            scored = []
            for p in results:
                text = " ".join(
                    str(v) for v in p.values() if isinstance(v, str)
                ).lower()
                # Simple relevance: count matching words
                query_words = set(query_lower.split())
                text_words = set(text.split())
                overlap = len(query_words & text_words)
                if overlap > 0:
                    scored.append((overlap, p))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = [s[1] for s in scored]

        return results

    def get_categories(self) -> list[str]:
        return sorted(self.categories)

    def format_for_context(self, prices: list[dict]) -> str:
        """Format prices as context string for LLM."""
        if not prices:
            return "No market price data available for this query."

        lines = [f"Market Prices (last updated: {self.last_updated}):"]
        for p in prices[:15]:  # Limit to 15 items
            line = f"- {p['item']}: UGX {p['price_ugx']:,}/{p['unit']}"
            if p.get("trend"):
                line += f" (trend: {p['trend']})"
            if p.get("location"):
                line += f" — {p['location']}"
            lines.append(line)

        lines.append(
            "\nNote: Prices are approximate and vary by location/season. "
            "Always verify with local suppliers."
        )
        return "\n".join(lines)
