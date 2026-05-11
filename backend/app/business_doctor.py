"""Business Doctor module for HustleScale — AI-powered business health analysis.

Analyses user-provided business metrics and generates actionable diagnoses
with recommendations. Works without LLM — pure rule-based analysis
for instant feedback, optionally enhanced by LLM for deeper insights.
"""

from __future__ import annotations

import logging
from .models import BusinessDoctorResponse, DiagnosisItem

logger = logging.getLogger(__name__)


def analyse_business(
    business_type: str,
    monthly_revenue_ugx: int = 0,
    monthly_costs_ugx: int = 0,
    months_operating: int = 0,
    employees: int = 0,
    location: str = "",
    challenges: str = "",
    goals: str = "",
) -> BusinessDoctorResponse:
    """Run business health analysis and return diagnosis."""
    diagnosis: list[DiagnosisItem] = []
    quick_wins: list[str] = []
    growth_opportunities: list[str] = []
    health_points = 50  # Start at 50, adjust up/down

    biz = business_type.lower()
    monthly_profit = monthly_revenue_ugx - monthly_costs_ugx
    profit_margin = (monthly_profit / monthly_revenue_ugx * 100) if monthly_revenue_ugx > 0 else 0

    # ─── Revenue Analysis ───
    if monthly_revenue_ugx == 0:
        diagnosis.append(DiagnosisItem(
            area="revenue",
            status="critical",
            finding="No revenue reported. Your business is not generating income yet.",
            recommendation="Focus on getting your first 5 paying customers this week. Start by telling friends, family, and neighbours about your product/service.",
            priority="urgent",
        ))
        health_points -= 20
    elif monthly_revenue_ugx < 200_000:
        diagnosis.append(DiagnosisItem(
            area="revenue",
            status="warning",
            finding=f"Monthly revenue (UGX {monthly_revenue_ugx:,}) is very low. This may not cover basic operating costs.",
            recommendation="Increase your customer base: try WhatsApp marketing, offer introductory discounts, or partner with a busier business nearby to cross-sell.",
            priority="high",
        ))
        health_points -= 10
    elif monthly_revenue_ugx < 500_000:
        diagnosis.append(DiagnosisItem(
            area="revenue",
            status="warning",
            finding=f"Monthly revenue (UGX {monthly_revenue_ugx:,}) is growing but still modest for sustainable income.",
            recommendation="Look for ways to increase order value: bundle products, offer premium options, or add complementary services.",
            priority="medium",
        ))
    else:
        diagnosis.append(DiagnosisItem(
            area="revenue",
            status="healthy",
            finding=f"Monthly revenue of UGX {monthly_revenue_ugx:,} shows good traction.",
            recommendation="Focus on consistency — ensure you can maintain this level month after month.",
            priority="low",
        ))
        health_points += 10

    # ─── Profitability Analysis ───
    if monthly_revenue_ugx > 0:
        if profit_margin < 0:
            diagnosis.append(DiagnosisItem(
                area="costs",
                status="critical",
                finding=f"Your business is losing UGX {abs(monthly_profit):,}/month. Costs exceed revenue.",
                recommendation="Urgently review costs: find cheaper suppliers, reduce waste, or renegotiate rent. Also check if your prices are too low.",
                priority="urgent",
            ))
            health_points -= 25
        elif profit_margin < 15:
            diagnosis.append(DiagnosisItem(
                area="costs",
                status="warning",
                finding=f"Profit margin is only {profit_margin:.0f}% (UGX {monthly_profit:,}/month). One bad month could wipe out your profits.",
                recommendation="Target at least 25-30% profit margin. Review your pricing — many youth entrepreneurs underprice their work. Cost + 30% minimum.",
                priority="high",
            ))
            health_points -= 5
        elif profit_margin < 30:
            diagnosis.append(DiagnosisItem(
                area="costs",
                status="healthy",
                finding=f"Profit margin of {profit_margin:.0f}% (UGX {monthly_profit:,}/month) is reasonable.",
                recommendation="Keep costs controlled. Save at least 20% of profit — 10% for emergencies, 10% for growth.",
                priority="medium",
            ))
            health_points += 5
        else:
            diagnosis.append(DiagnosisItem(
                area="costs",
                status="healthy",
                finding=f"Strong profit margin of {profit_margin:.0f}% (UGX {monthly_profit:,}/month).",
                recommendation="Excellent! Reinvest some profits to grow. Consider expanding product range or serving more customers.",
                priority="low",
            ))
            health_points += 15

    # ─── Maturity Analysis ───
    if months_operating == 0:
        diagnosis.append(DiagnosisItem(
            area="operations",
            status="warning",
            finding="Business not yet started.",
            recommendation="Start small — even if you can only serve 3 customers this week. Action beats perfect planning.",
            priority="high",
        ))
    elif months_operating < 3:
        diagnosis.append(DiagnosisItem(
            area="operations",
            status="warning",
            finding=f"Operating for {months_operating} month(s) — still in early survival stage.",
            recommendation="Focus on cash flow, not profits. Keep daily records. Don't borrow money yet — first prove the model works.",
            priority="medium",
        ))
    elif months_operating < 12:
        health_points += 5
        if monthly_profit > 0:
            diagnosis.append(DiagnosisItem(
                area="operations",
                status="healthy",
                finding=f"Operating profitably for {months_operating} months — you're past the danger zone.",
                recommendation="Now is a good time to formalise: get a trading license, register with URA, and consider joining a SACCO.",
                priority="medium",
            ))
    else:
        health_points += 10
        diagnosis.append(DiagnosisItem(
            area="operations",
            status="healthy",
            finding=f"Operating for {months_operating} months — this is a proven business.",
            recommendation="Consider scaling: new location, new products, training an employee to handle operations while you focus on growth.",
            priority="low",
        ))

    # ─── Employment ───
    if employees > 0:
        health_points += 5
        diagnosis.append(DiagnosisItem(
            area="compliance",
            status="warning" if employees >= 5 else "healthy",
            finding=f"You have {employees} employee(s)." + (" NSSF registration is mandatory for 5+ employees." if employees >= 5 else ""),
            recommendation="Ensure you have written agreements with employees. Pay fair wages consistently. Consider NSSF even if under 5 staff.",
            priority="high" if employees >= 5 else "low",
        ))

    # ─── Marketing Analysis ───
    challenges_lower = challenges.lower()
    if "customer" in challenges_lower or "market" in challenges_lower or "sell" in challenges_lower:
        diagnosis.append(DiagnosisItem(
            area="marketing",
            status="warning",
            finding="Customer acquisition is a reported challenge.",
            recommendation="Try these free marketing tactics: (1) WhatsApp status updates with photos of your work, (2) Ask satisfied customers for referrals — offer 5% discount for each new customer they bring, (3) Partner with complementary businesses nearby.",
            priority="high",
        ))
        quick_wins.append("Post your product/service on your WhatsApp status today with a clear price")
        quick_wins.append("Ask your 3 best customers to refer a friend this week")

    if "competition" in challenges_lower or "compete" in challenges_lower:
        quick_wins.append("Visit your top 3 competitors and note what you can do differently or better")
        quick_wins.append("Find a niche: specialise in one thing and become the best at it in your area")

    # ─── Quick Wins ───
    if monthly_revenue_ugx > 0 and monthly_profit > 0 and not quick_wins:
        quick_wins = [
            "Start a simple record book: write down every sale and expense today",
            "Ask 3 customers what they wish you offered — then add the most requested item",
            "Set a weekly savings target: even UGX 10,000/week builds your emergency fund",
        ]

    if months_operating > 0 and monthly_profit > 0:
        growth_opportunities = [
            "Open a mobile money savings account dedicated to business growth fund",
            "Explore bulk buying with other entrepreneurs in your area to reduce costs",
            "Consider offering delivery or home service to reach more customers",
        ]

    if biz in ("poultry", "agriculture", "fish_farming", "piggery"):
        growth_opportunities.append("Connect with district agricultural officer for free extension services and training")
    if biz in ("tailoring", "salon", "welding"):
        growth_opportunities.append("Take on an apprentice — teach your skills while getting extra hands during busy periods")
    if biz in ("food_vending", "rolex", "restaurant"):
        growth_opportunities.append("Consider catering for events — higher margins than daily vending")

    # ─── Calculate overall health ───
    health_points = max(0, min(100, health_points))

    if health_points >= 75:
        overall = "excellent"
    elif health_points >= 60:
        overall = "good"
    elif health_points >= 40:
        overall = "fair"
    elif health_points >= 20:
        overall = "poor"
    else:
        overall = "critical"

    return BusinessDoctorResponse(
        overall_health=overall,
        health_score=health_points,
        diagnosis=diagnosis,
        quick_wins=quick_wins[:5],
        growth_opportunities=growth_opportunities[:5],
    )
