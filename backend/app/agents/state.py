"""Route decision state for supervisor agent."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RouteDecision:
    route: str  # business_plan, finance, marketing, risk, market_prices, etc.
    domain: str | None = None
    confidence: float = 0.0
    reason: str = ""
    keywords_matched: list[str] = field(default_factory=list)
