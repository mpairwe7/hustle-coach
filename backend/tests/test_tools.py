"""Tests for HustleScale agentic tools."""

import json
import pytest
from app.tools import execute_tool, TOOL_DEFINITIONS


# ─── Tool Definitions ───

def test_tool_definitions_complete():
    """All 8 tools should be defined with proper schemas."""
    assert len(TOOL_DEFINITIONS) == 8
    names = {t["name"] for t in TOOL_DEFINITIONS}
    assert names == {"market_lookup", "validate_budget", "assess_risk", "check_regulations", "calculate_break_even", "find_funding", "find_suppliers", "suggest_cooperative"}
    for tool in TOOL_DEFINITIONS:
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"


# ─── Market Lookup ───

SAMPLE_PRICES = [
    {"item": "Day-old broiler chicks", "item_lg": "Obuwuka", "item_sw": "Vifaranga", "price_ugx": 4000, "unit": "per chick", "category": "poultry", "trend": "stable", "location": "Kampala"},
    {"item": "Broiler starter feed (50kg)", "item_lg": "", "item_sw": "", "price_ugx": 145000, "unit": "per bag", "category": "poultry", "trend": "rising", "location": "Kampala"},
    {"item": "Cement (50kg bag)", "item_lg": "Ssementi", "item_sw": "Saruji", "price_ugx": 38000, "unit": "per bag", "category": "construction", "trend": "stable", "location": "Kampala"},
]


def test_market_lookup_found():
    result = json.loads(execute_tool("market_lookup", {"item": "chicks"}, SAMPLE_PRICES))
    assert result["found"] is True
    assert len(result["prices"]) == 1
    assert result["prices"][0]["price_ugx"] == 4000


def test_market_lookup_category_filter():
    result = json.loads(execute_tool("market_lookup", {"item": "feed", "category": "poultry"}, SAMPLE_PRICES))
    assert result["found"] is True
    assert result["prices"][0]["price_ugx"] == 145000


def test_market_lookup_not_found():
    result = json.loads(execute_tool("market_lookup", {"item": "spaceship"}, SAMPLE_PRICES))
    assert result["found"] is False


# ─── Validate Budget ───

def test_validate_budget_complete():
    result = json.loads(execute_tool("validate_budget", {
        "business_type": "poultry",
        "startup_items": [
            {"item": "chicks", "amount_ugx": 400000},
            {"item": "feed", "amount_ugx": 600000},
            {"item": "vaccines", "amount_ugx": 50000},
            {"item": "housing", "amount_ugx": 300000},
            {"item": "drinkers and feeders", "amount_ugx": 100000},
        ],
    }))
    assert result["total_startup_ugx"] == 1450000
    assert len(result["issues"]) == 0  # All required items present


def test_validate_budget_missing_items():
    result = json.loads(execute_tool("validate_budget", {
        "business_type": "poultry",
        "startup_items": [
            {"item": "chicks", "amount_ugx": 400000},
        ],
    }))
    assert len(result["issues"]) > 0  # Missing feed, vaccines, housing, etc.


def test_validate_budget_too_low():
    result = json.loads(execute_tool("validate_budget", {
        "business_type": "general",
        "startup_items": [{"item": "pencil", "amount_ugx": 500}],
    }))
    assert any("very low" in issue.lower() for issue in result["issues"])


# ─── Calculate Break-Even ───

def test_break_even_viable():
    result = json.loads(execute_tool("calculate_break_even", {
        "startup_cost_ugx": 1500000,
        "monthly_cost_ugx": 800000,
        "monthly_revenue_ugx": 1200000,
    }))
    assert result["viable"] is True
    assert result["monthly_profit_ugx"] == 400000
    assert result["break_even_months"] == 4  # ceil(1.5M / 400K)


def test_break_even_not_viable():
    result = json.loads(execute_tool("calculate_break_even", {
        "startup_cost_ugx": 1000000,
        "monthly_cost_ugx": 500000,
        "monthly_revenue_ugx": 300000,
    }))
    assert result["viable"] is False


# ─── Check Regulations ───

def test_regulations_kampala():
    result = json.loads(execute_tool("check_regulations", {
        "business_type": "food_vending",
        "location": "Kampala",
        "has_employees": False,
    }))
    regs = result["regulations"]
    # Should include trading license, URA TIN, food handler's cert, business name reg
    reg_names = [r["requirement"] for r in regs]
    assert any("Trading License" in r for r in reg_names)
    assert any("URA" in r for r in reg_names)
    assert any("Food Handler" in r for r in reg_names)


def test_regulations_with_employees():
    result = json.loads(execute_tool("check_regulations", {
        "business_type": "salon",
        "location": "Mbarara",
        "has_employees": True,
    }))
    reg_names = [r["requirement"] for r in result["regulations"]]
    assert any("NSSF" in r for r in reg_names)


# ─── Assess Risk ───

def test_assess_risk_poultry():
    result = json.loads(execute_tool("assess_risk", {
        "business_type": "poultry",
        "location": "Kampala",
        "capital_ugx": 1500000,
    }))
    risks = result["risks"]
    assert len(risks) >= 4  # Universal + poultry-specific + Kampala-specific
    risk_names = [r["risk"].lower() for r in risks]
    assert any("disease" in r for r in risk_names)
    assert any("competition" in r for r in risk_names)


def test_assess_risk_low_capital():
    result = json.loads(execute_tool("assess_risk", {
        "business_type": "salon",
        "location": "rural Mukono",
        "capital_ugx": 100000,
    }))
    risk_names = [r["risk"].lower() for r in result["risks"]]
    assert any("insufficient" in r or "capital" in r for r in risk_names)
    assert any("limited customer" in r or "rural" in r for r in risk_names)


# ─── Unknown Tool ───

def test_unknown_tool():
    result = json.loads(execute_tool("nonexistent_tool", {}))
    assert "error" in result
