"""Tests for HustleScale Business Doctor — rule-based health analysis."""

import pytest
from app.business_doctor import analyse_business


def _to_dict(result):
    """Convert Pydantic model or dict to plain dict."""
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


class TestBusinessDoctor:
    def test_healthy_business(self):
        """Business with good margins should score well."""
        result = _to_dict(analyse_business(
            business_type="poultry",
            monthly_revenue_ugx=1200000,
            monthly_costs_ugx=700000,
            months_operating=6,
            employees=2,
            location="Kampala",
        ))
        assert result["health_score"] >= 50
        assert result["overall_health"] in ("healthy", "good", "stable", "excellent")
        assert len(result["diagnosis"]) >= 3
        assert isinstance(result["quick_wins"], list)
        assert result["disclaimer"]

    def test_zero_revenue_warning(self):
        """Zero revenue should trigger critical finding."""
        result = _to_dict(analyse_business(
            business_type="salon",
            monthly_revenue_ugx=0,
            monthly_costs_ugx=300000,
            months_operating=1,
            employees=0,
            location="Mbarara",
        ))
        assert result["health_score"] < 50
        statuses = [d["status"] for d in result["diagnosis"]]
        assert "critical" in statuses or "warning" in statuses

    def test_high_cost_ratio(self):
        """Costs exceeding revenue should flag issues."""
        result = _to_dict(analyse_business(
            business_type="food_vending",
            monthly_revenue_ugx=500000,
            monthly_costs_ugx=600000,
            months_operating=3,
            employees=1,
            location="Kampala",
        ))
        findings = [d["finding"].lower() for d in result["diagnosis"]]
        assert any("cost" in f or "expense" in f or "loss" in f or "exceed" in f or "negative" in f for f in findings)

    def test_new_business(self):
        """Brand new business should get startup-appropriate advice."""
        result = _to_dict(analyse_business(
            business_type="tailoring",
            monthly_revenue_ugx=200000,
            monthly_costs_ugx=100000,
            months_operating=0,
            employees=0,
            location="Mukono",
        ))
        assert isinstance(result["growth_opportunities"], list)
        assert len(result["quick_wins"]) > 0

    def test_all_diagnosis_areas(self):
        """Diagnosis should cover multiple business areas."""
        result = _to_dict(analyse_business(
            business_type="mobile_money",
            monthly_revenue_ugx=800000,
            monthly_costs_ugx=200000,
            months_operating=12,
            employees=1,
            location="Kampala",
        ))
        areas = {d["area"] for d in result["diagnosis"]}
        assert len(areas) >= 3

    def test_diagnosis_structure(self):
        """Each diagnosis entry should have required fields."""
        result = _to_dict(analyse_business(
            business_type="general",
            monthly_revenue_ugx=300000,
            monthly_costs_ugx=200000,
            months_operating=2,
            employees=0,
            location="Gulu",
        ))
        for d in result["diagnosis"]:
            assert "area" in d
            assert "status" in d
            assert "finding" in d
            assert "recommendation" in d
            assert "priority" in d
            assert d["priority"] in ("low", "medium", "high", "urgent")
