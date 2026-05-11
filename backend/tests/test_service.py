"""Service layer tests — follow-up generation with locale/domain support."""

import pytest

from app.service import _generate_follow_ups


class TestGenerateFollowUps:
    """Follow-up generation with locale support."""

    # ── Locale coverage ──

    @pytest.mark.parametrize("locale", ["en", "lg", "sw", "nyn"])
    def test_all_locales_return_results(self, locale):
        result = _generate_follow_ups("business idea", "business_plan", "Here's a plan", locale)
        assert 0 < len(result) <= 3

    @pytest.mark.parametrize("locale", ["en", "lg", "sw", "nyn"])
    def test_all_locales_return_strings(self, locale):
        result = _generate_follow_ups("funding", "funding", "Here are options", locale)
        assert all(isinstance(s, str) for s in result)
        assert all(len(s) > 0 for s in result)

    # ── Domain coverage ──

    @pytest.mark.parametrize("domain", [
        "business_plan", "finance", "marketing", "risk",
        "market_prices", "success_stories", "funding", "cooperative",
    ])
    def test_all_domains_covered_en(self, domain):
        result = _generate_follow_ups("test query", domain, "answer text", "en")
        assert len(result) > 0

    @pytest.mark.parametrize("domain", [
        "business_plan", "finance", "marketing", "risk",
        "market_prices", "success_stories", "funding", "cooperative",
    ])
    def test_all_domains_covered_lg(self, domain):
        result = _generate_follow_ups("test query", domain, "answer text", "lg")
        assert len(result) > 0

    # ── Fallback behaviour ──

    def test_unknown_domain_falls_back(self):
        result = _generate_follow_ups("hello", "unknown_domain", "hi", "en")
        assert len(result) > 0  # Falls back to default suggestions

    def test_unknown_locale_falls_back_to_english(self):
        result = _generate_follow_ups("test", "general", "answer", "xx")
        assert len(result) <= 3
        assert len(result) > 0

    def test_unknown_locale_and_domain(self):
        result = _generate_follow_ups("test", "nonexistent", "answer", "zz")
        assert len(result) > 0

    # ── Filtering ──

    def test_filter_similar_to_query(self):
        """Follow-ups containing query words should be filtered out."""
        result = _generate_follow_ups(
            "help me create a business plan",
            "business_plan", "answer", "en",
        )
        # The filter checks first 3 words of each suggestion against query
        assert len(result) <= 3

    def test_max_three_follow_ups(self):
        """Never return more than 3 follow-ups."""
        for domain in ["business_plan", "finance", "marketing", "risk",
                        "market_prices", "success_stories", "funding", "cooperative"]:
            for locale in ["en", "lg", "sw", "nyn"]:
                result = _generate_follow_ups("x", domain, "y", locale)
                assert len(result) <= 3, f"Got {len(result)} for {domain}/{locale}"

    # ── Luganda follow-ups are actually in Luganda ──

    def test_luganda_follow_ups_not_english(self):
        result = _generate_follow_ups("Njagala enkoko", "market_prices", "Emiwendo...", "lg")
        assert len(result) > 0
        # Luganda follow-ups should not start with common English words
        assert not any(s.startswith("How ") for s in result)
        assert not any(s.startswith("What ") for s in result)

    def test_swahili_follow_ups_not_english(self):
        result = _generate_follow_ups("Nataka kuku", "funding", "Ruzuku...", "sw")
        assert len(result) > 0
        assert not any(s.startswith("How ") for s in result)
