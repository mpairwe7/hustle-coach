"""Tests for HustleScale domain supervisor/router."""

from app.agents.supervisor import classify


def test_classify_business_plan():
    result = classify("I want to start a poultry farm business plan")
    assert result.domain == "business_plan"
    assert result.confidence > 0.3


def test_classify_finance():
    result = classify("How do I save money and manage my finances")
    assert result.domain == "finance"


def test_classify_marketing():
    result = classify("How should I advertise and sell my products to customers")
    assert result.domain == "marketing"


def test_classify_risk():
    result = classify("What are the risks and dangers of this business, what could go wrong")
    assert result.domain == "risk"


def test_classify_market_prices():
    result = classify("What is the current price of chicken, how much does it cost")
    assert result.domain == "market_prices"


def test_classify_success_stories():
    result = classify("Tell me a success story about a young person who started a business")
    assert result.domain == "success_stories"


def test_classify_luganda():
    """Luganda queries should route via multilingual bridge."""
    result = classify("Njagala okutandika bizinensi y'enkoko")
    assert result.domain is not None
    assert result.route != "redirect"


def test_classify_swahili():
    """Swahili queries should route correctly."""
    result = classify("Nataka kuanzisha biashara ya kuku")
    assert result.route != "redirect"


def test_classify_non_business_redirect():
    result = classify("Tell me about dating and love and relationships")
    assert result.route == "redirect"


def test_classify_short_ambiguous():
    result = classify("hi")
    assert result.route == "clarify"


def test_classify_general():
    result = classify("I need some advice about something important for my future career goals")
    assert result.route in ("general", "clarify")
