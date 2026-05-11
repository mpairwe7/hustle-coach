"""Funding matcher for HustleScale — connects youth to grants, loans, and funds.

Maintains a database of Uganda-specific funding sources and matches them
to user profiles based on business type, location, capital needs, and stage.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Uganda funding sources database — curated for youth micro-enterprises
FUNDING_SOURCES = [
    {
        "id": "ylp",
        "name": "Youth Livelihood Programme (YLP)",
        "provider": "Ministry of Gender, Labour and Social Development",
        "type": "fund",
        "amount_range": "UGX 5M - 25M per group (5-15 members)",
        "eligibility": "Ugandan youth aged 18-30, in groups of 5-15 members, with a viable project proposal",
        "how_to_apply": "Form a youth group, register with your Sub-County/Division, submit project proposal to Community Development Officer (CDO). CDO forwards to District Youth Council for approval.",
        "deadline": "Rolling applications — check with your Sub-County CDO",
        "interest_rate": "Interest-free (revolving fund — repay to benefit next group)",
        "requirements": ["National ID for all members", "Group registration certificate", "Project proposal with budget", "Sub-County recommendation letter", "Bank/SACCO account in group name"],
        "target_sectors": ["agriculture", "poultry", "tailoring", "food_vending", "salon", "welding", "carpentry", "brick_making"],
        "target_locations": ["Nationwide"],
    },
    {
        "id": "emyooga",
        "name": "Emyooga Presidential Initiative on Wealth Creation",
        "provider": "Microfinance Support Centre (MSC)",
        "type": "fund",
        "amount_range": "UGX 30M per SACCO (shared among members)",
        "eligibility": "SACCOs formed around specific enterprises — bodaboda, salon, welding, produce dealers, tailors, etc.",
        "how_to_apply": "Form or join an Emyooga SACCO in your constituency. Register with MSC. Apply through SACCO leadership for seed capital allocation.",
        "deadline": "Ongoing — new SACCOs still registering",
        "interest_rate": "Low interest (negotiated by SACCO)",
        "requirements": ["Minimum 30 SACCO members", "Enterprise-specific grouping", "Registered SACCO with constitution", "Bank account in SACCO name", "Training completion certificate"],
        "target_sectors": ["boda_repair", "salon", "welding", "tailoring", "produce_dealing", "restaurant", "carpentry", "women_entrepreneurs"],
        "target_locations": ["Nationwide"],
    },
    {
        "id": "uwep",
        "name": "Uganda Women Entrepreneurship Programme (UWEP)",
        "provider": "Ministry of Gender, Labour and Social Development",
        "type": "fund",
        "amount_range": "UGX 5M - 25M per group",
        "eligibility": "Women-only groups (5-10 members), age 18+, with project in agriculture, trade, or services",
        "how_to_apply": "Form women's group, register at Sub-County, submit project proposal to CDO. Similar process to YLP.",
        "deadline": "Rolling applications",
        "interest_rate": "Interest-free revolving fund",
        "requirements": ["National ID for all members", "Women-only group (5-10 members)", "Project proposal", "Group constitution and registration"],
        "target_sectors": ["agriculture", "tailoring", "salon", "food_vending", "poultry", "piggery", "crafts"],
        "target_locations": ["Nationwide"],
    },
    {
        "id": "pdi",
        "name": "Parish Development Model (PDM)",
        "provider": "Government of Uganda",
        "type": "fund",
        "amount_range": "UGX 100M per parish (shared among eligible households)",
        "eligibility": "Households in the subsistence economy category, age 18+, with viable enterprise proposal",
        "how_to_apply": "Register with your Parish Chief, attend PDM meetings, form enterprise group (minimum 9 households), submit proposal through Parish Development Committee.",
        "deadline": "Rolling — parish-level allocation",
        "interest_rate": "Interest-free (revolving fund)",
        "requirements": ["National ID", "Parish resident", "Enterprise group formation", "Completed PDM financial literacy training", "Bank/SACCO account"],
        "target_sectors": ["agriculture", "poultry", "piggery", "fish_farming", "food_vending", "tailoring"],
        "target_locations": ["Nationwide"],
    },
    {
        "id": "yvcf",
        "name": "Youth Venture Capital Fund (YVCF)",
        "provider": "Ministry of Finance via participating banks",
        "type": "loan",
        "amount_range": "UGX 100K - 5M (individual) / up to 25M (group)",
        "eligibility": "Ugandan youth aged 18-35 with viable business plan",
        "how_to_apply": "Apply at participating banks: Centenary, Post Bank, Pride Microfinance, FINCA. Submit business plan, ID, and collateral documentation.",
        "deadline": "Ongoing",
        "interest_rate": "15% per annum (subsidised)",
        "requirements": ["National ID", "Business plan", "Some form of collateral or group guarantee", "Completed entrepreneurship training (preferred)"],
        "target_sectors": ["agriculture", "trade", "services", "manufacturing", "technology"],
        "target_locations": ["Nationwide"],
    },
    {
        "id": "brac",
        "name": "BRAC Uganda Microfinance",
        "provider": "BRAC Uganda",
        "type": "loan",
        "amount_range": "UGX 100K - 3M (individual microloans)",
        "eligibility": "Women and youth in groups of 15-25 members, with existing small business",
        "how_to_apply": "Join or form a BRAC group in your area. Attend weekly meetings. Apply for individual loan through group.",
        "deadline": "Ongoing",
        "interest_rate": "~25-30% declining balance per annum",
        "requirements": ["Group membership (15-25 members)", "Weekly savings commitment", "Existing business activity", "Group guarantee"],
        "target_sectors": ["trade", "food_vending", "agriculture", "salon", "tailoring"],
        "target_locations": ["Nationwide"],
    },
    {
        "id": "finca",
        "name": "FINCA Uganda Youth Loans",
        "provider": "FINCA Uganda",
        "type": "loan",
        "amount_range": "UGX 300K - 10M",
        "eligibility": "Youth aged 18-35 with existing or new business",
        "how_to_apply": "Visit nearest FINCA branch. Submit application with business plan, ID, and references.",
        "deadline": "Ongoing",
        "interest_rate": "~28-33% per annum",
        "requirements": ["National ID", "Business plan or existing business proof", "Guarantor or collateral"],
        "target_sectors": ["agriculture", "trade", "services", "manufacturing"],
        "target_locations": ["Urban and peri-urban areas"],
    },
    {
        "id": "vsla",
        "name": "Village Savings and Loan Associations (VSLAs)",
        "provider": "Community-based (supported by NGOs like CARE, World Vision)",
        "type": "grant",
        "amount_range": "Depends on group — typically UGX 50K-500K per cycle per member",
        "eligibility": "Any community member, minimum age 15-18 depending on group rules",
        "how_to_apply": "Join an existing VSLA in your community or form one with 15-25 members. No formal registration needed — community-based.",
        "deadline": "Always open",
        "interest_rate": "Set by group (typically 5-10% per month on loans to members)",
        "requirements": ["Weekly savings contribution (UGX 1,000-10,000)", "Group agreement", "Regular attendance at meetings"],
        "target_sectors": ["all"],
        "target_locations": ["Nationwide — especially rural areas"],
    },
    {
        "id": "innovation_village",
        "name": "Innovation Village Accelerator",
        "provider": "Innovation Village Kampala",
        "type": "competition",
        "amount_range": "Varies — seed funding UGX 5M-50M + mentorship",
        "eligibility": "Tech-enabled startups, age 18-35, with prototype or MVP",
        "how_to_apply": "Apply online at innovationvillage.co.ug during open calls. Pitch to panel.",
        "deadline": "Cohort-based — check website for next intake",
        "requirements": ["Business pitch deck", "Prototype or MVP", "Team of 2-5 members"],
        "target_sectors": ["technology", "digital_services", "agritech", "fintech", "healthtech"],
        "target_locations": ["Kampala", "Urban centres"],
    },
    {
        "id": "mastercard_foundation",
        "name": "Mastercard Foundation Young Africa Works",
        "provider": "Mastercard Foundation (via local partners)",
        "type": "grant",
        "amount_range": "Training + seed capital (varies by partner programme)",
        "eligibility": "Young Africans aged 18-35, unemployed or underemployed",
        "how_to_apply": "Apply through implementing partners: Generation Kenya/Uganda, Educate!, BRAC. Check mastercardfounda tion.org for current opportunities.",
        "deadline": "Varies by programme",
        "requirements": ["Age 18-35", "Commitment to complete training programme", "Resident of eligible area"],
        "target_sectors": ["agriculture", "hospitality", "digital_skills", "financial_services"],
        "target_locations": ["Nationwide"],
    },
]


class FundingMatcher:
    """Matches entrepreneurs to relevant funding sources."""

    def __init__(self):
        self.sources = FUNDING_SOURCES

    def match(
        self,
        business_type: str = "",
        location: str = "",
        capital_needed_ugx: int = 0,
        stage: str = "idea",
        gender: str = "",
    ) -> list[dict]:
        """Find matching funding sources for an entrepreneur."""
        results = []
        biz = business_type.lower()
        loc = location.lower()

        for source in self.sources:
            score = 0
            # Sector match
            sectors = [s.lower() for s in source["target_sectors"]]
            if "all" in sectors or any(s in biz for s in sectors) or any(biz in s for s in sectors):
                score += 3

            # Location match
            locations = [l.lower() for l in source["target_locations"]]
            if "nationwide" in locations:
                score += 1
            elif any(l in loc for l in locations):
                score += 2

            # Gender-specific boost
            if gender == "female" and source["id"] == "uwep":
                score += 5

            # Stage match
            if stage == "idea" and source["type"] in ("fund", "grant"):
                score += 2
            elif stage in ("launched", "growing") and source["type"] == "loan":
                score += 2

            # Always include VSLAs and government funds
            if source["id"] in ("vsla", "ylp", "pdm"):
                score += 1

            if score > 0:
                results.append({**source, "_score": score})

        results.sort(key=lambda x: x["_score"], reverse=True)
        for r in results:
            r.pop("_score", None)
        return results[:8]

    def get_all(self) -> list[dict]:
        """Return all funding sources."""
        return self.sources
