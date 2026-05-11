"""Tests for HustleScale Funding Matcher."""

import pytest
from app.funding import FundingMatcher


class TestFundingMatcher:
    def setup_method(self):
        self.matcher = FundingMatcher()

    def test_get_all_sources(self):
        """Should return all available funding sources."""
        sources = self.matcher.get_all()
        assert len(sources) >= 6
        # Check required funding programs exist
        ids = {s["id"] for s in sources}
        assert "ylp" in ids
        assert "emyooga" in ids
        assert "uwep" in ids
        assert "pdi" in ids

    def test_match_poultry_kampala(self):
        """Poultry farmer in Kampala should match several sources."""
        matches = self.matcher.match(
            business_type="poultry",
            location="Kampala",
            capital_needed_ugx=2000000,
            stage="planning",
        )
        assert len(matches) >= 2
        # YLP should match for youth agriculture
        match_ids = {m["id"] for m in matches}
        assert "ylp" in match_ids

    def test_match_salon_emyooga(self):
        """Salon business should match Emyooga SACCO."""
        matches = self.matcher.match(
            business_type="salon",
            location="Mbarara",
            capital_needed_ugx=500000,
            stage="idea",
        )
        match_ids = {m["id"] for m in matches}
        assert "emyooga" in match_ids

    def test_match_women_uwep(self):
        """Women-focused sectors should include UWEP."""
        matches = self.matcher.match(
            business_type="tailoring",
            location="Jinja",
            capital_needed_ugx=1000000,
            stage="launched",
        )
        match_ids = {m["id"] for m in matches}
        assert "uwep" in match_ids

    def test_source_structure(self):
        """Each funding source should have required fields."""
        sources = self.matcher.get_all()
        for s in sources:
            assert "id" in s
            assert "name" in s
            assert "provider" in s
            assert "type" in s
            assert "amount_range" in s
            assert "eligibility" in s
            assert "how_to_apply" in s
            assert "requirements" in s
            assert isinstance(s["requirements"], list)

    def test_match_returns_list(self):
        """Match should always return a list."""
        matches = self.matcher.match(
            business_type="welding",
            location="Kampala",
            capital_needed_ugx=3000000,
            stage="planning",
        )
        assert isinstance(matches, list)
        # Should find at least some funding sources
        assert len(matches) >= 1
