"""Business plan generation logic for HustleScale.

Uses extended thinking to produce structured, realistic business plans
with Uganda-specific market data.
"""

from __future__ import annotations

import json
import logging
import re

from .models import (
    BusinessPlan,
    BudgetItem,
    BreakEven,
    RevenueProjection,
    RiskItem,
)

logger = logging.getLogger(__name__)


def extract_business_plan(llm_text: str) -> BusinessPlan | None:
    """Try to extract structured business plan from LLM response.

    The LLM is prompted to include structured data. This function
    attempts to parse it, falling back gracefully if the format
    doesn't match exactly.
    """
    # Try JSON block extraction first
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", llm_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return _parse_plan_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass

    # Try to parse structured sections from markdown
    return _parse_plan_markdown(llm_text)


def _parse_plan_dict(data: dict) -> BusinessPlan:
    """Parse a plan from a JSON dict."""
    startup_items = []
    for item in data.get("startup_budget", []):
        startup_items.append(BudgetItem(
            item=item.get("item", ""),
            amount_ugx=int(item.get("amount_ugx", item.get("amount", 0))),
            notes=item.get("notes", ""),
        ))

    monthly_items = []
    for item in data.get("monthly_costs", []):
        monthly_items.append(BudgetItem(
            item=item.get("item", ""),
            amount_ugx=int(item.get("amount_ugx", item.get("amount", 0))),
            notes=item.get("notes", ""),
        ))

    revenue = None
    if "revenue_projection" in data:
        rp = data["revenue_projection"]
        revenue = RevenueProjection(
            monthly_revenue=int(rp.get("monthly_revenue", 0)),
            monthly_profit=int(rp.get("monthly_profit", 0)),
            assumptions=rp.get("assumptions", ""),
        )

    break_even = None
    if "break_even" in data:
        be = data["break_even"]
        break_even = BreakEven(
            months=int(be.get("months", 0)),
            explanation=be.get("explanation", ""),
        )

    risks = []
    for risk in data.get("risks", []):
        risks.append(RiskItem(
            risk=risk.get("risk", ""),
            likelihood=risk.get("likelihood", "medium"),
            impact=risk.get("impact", "medium"),
            mitigation=risk.get("mitigation", ""),
        ))

    return BusinessPlan(
        business_name=data.get("business_name", ""),
        executive_summary=data.get("executive_summary", ""),
        startup_budget=startup_items,
        total_startup_cost=sum(i.amount_ugx for i in startup_items),
        monthly_costs=monthly_items,
        total_monthly_cost=sum(i.amount_ugx for i in monthly_items),
        revenue_projection=revenue,
        break_even=break_even,
        pricing_strategy=data.get("pricing_strategy", ""),
        marketing_script=data.get("marketing_script", ""),
        risks=risks,
        next_steps=data.get("next_steps", []),
        confidence=data.get("confidence", "medium"),
    )


def _parse_plan_markdown(text: str) -> BusinessPlan | None:
    """Best-effort extraction from markdown-formatted LLM response."""
    # Extract budget items from bullet lists with UGX amounts
    ugx_pattern = re.compile(r"[-•]\s*(.+?):\s*(?:UGX\s*)?(\d[\d,]*)", re.IGNORECASE)

    startup_items = []
    monthly_items = []

    # Look for startup section
    startup_match = re.search(
        r"(?:startup|initial|capital|investment)\s*(?:budget|cost|expense).*?\n((?:[-•].*\n?)+)",
        text, re.IGNORECASE,
    )
    if startup_match:
        for m in ugx_pattern.finditer(startup_match.group(1)):
            startup_items.append(BudgetItem(
                item=m.group(1).strip(),
                amount_ugx=int(m.group(2).replace(",", "")),
            ))

    # Look for monthly section
    monthly_match = re.search(
        r"(?:monthly|operating|recurring)\s*(?:cost|expense).*?\n((?:[-•].*\n?)+)",
        text, re.IGNORECASE,
    )
    if monthly_match:
        for m in ugx_pattern.finditer(monthly_match.group(1)):
            monthly_items.append(BudgetItem(
                item=m.group(1).strip(),
                amount_ugx=int(m.group(2).replace(",", "")),
            ))

    # Extract next steps
    steps = []
    steps_match = re.search(
        r"(?:next\s+steps?|action\s+items?|this\s+week).*?\n((?:\d+[.)]\s*.*\n?)+)",
        text, re.IGNORECASE,
    )
    if steps_match:
        for line in steps_match.group(1).strip().split("\n"):
            step = re.sub(r"^\d+[.)]\s*", "", line).strip()
            if step:
                steps.append(step)

    if not startup_items and not steps:
        return None

    return BusinessPlan(
        startup_budget=startup_items,
        total_startup_cost=sum(i.amount_ugx for i in startup_items),
        monthly_costs=monthly_items,
        total_monthly_cost=sum(i.amount_ugx for i in monthly_items),
        next_steps=steps,
    )


def build_plan_prompt_supplement(query: str, market_context: str = "") -> str:
    """Build additional prompt context for business plan generation."""
    supplement = """
When generating this business plan, please:
1. Use REALISTIC Uganda market prices (reference the market data provided)
2. All costs in Uganda Shillings (UGX) — use commas for thousands
3. Assume the person is starting with minimal capital (UGX 200,000 - 2,000,000)
4. Include a break-even calculation showing months to recover investment
5. Marketing should focus on free/cheap methods (WhatsApp, word-of-mouth)
6. Risks should include local factors (weather, theft, competition, seasonality)
7. Next steps should be things they can do THIS WEEK with minimal money
"""

    if market_context:
        supplement += f"\n\nCurrent market data:\n{market_context}\n"

    return supplement
