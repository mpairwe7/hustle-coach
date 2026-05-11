"""Tests for HustleScale Market Intelligence."""

import pytest
from app.market_intel import MarketIntelligence


class TestMarketIntelligence:
    def setup_method(self):
        self.market = MarketIntelligence()
        self.market.load()

    def test_prices_loaded(self):
        """Market prices should be loaded from JSON."""
        assert len(self.market.prices) >= 30
        assert self.market.last_updated != ""

    def test_categories_available(self):
        """Should have multiple price categories."""
        categories = self.market.get_categories()
        assert len(categories) >= 5
        assert "poultry" in categories
        assert "agriculture" in categories

    def test_search_by_item(self):
        """Search by item name should return results."""
        results = self.market.search(item="chicken")
        assert len(results) > 0

    def test_search_by_category(self):
        """Search by category should filter correctly."""
        results = self.market.search(category="poultry")
        assert len(results) > 0
        for r in results:
            assert r["category"] == "poultry"

    def test_search_synonym_expansion(self):
        """Luganda/Swahili synonyms should match."""
        results = self.market.search(item="enkoko")  # Luganda for chicken
        assert len(results) > 0

    def test_search_no_results(self):
        """Non-existent item should return empty."""
        results = self.market.search(item="nonexistent_item_xyz")
        assert len(results) == 0

    def test_price_entry_structure(self):
        """Each price entry should have required fields."""
        for p in self.market.prices[:5]:
            assert "item" in p
            assert "price_ugx" in p
            assert "unit" in p
            assert "category" in p
            assert isinstance(p["price_ugx"], (int, float))
            assert p["price_ugx"] > 0

    def test_search_combined_filters(self):
        """Search with both item and category should work."""
        results = self.market.search(item="feed", category="poultry")
        assert len(results) > 0
        for r in results:
            assert r["category"] == "poultry"
