"""Agentic tools for HustleScale — tool_use integration.

8 tools the CoachAgent can call during multi-step reasoning:
- market_lookup: Search current Uganda market prices
- validate_budget: Check if a budget is realistic and complete
- assess_risk: Evaluate business risks for a specific venture
- check_regulations: Look up KCCA/URA/NSSF requirements
- calculate_break_even: Compute break-even from costs and revenue
- find_funding: Match entrepreneur to grants, loans, and funds
- find_suppliers: Locate suppliers for business inputs
- suggest_cooperative: Recommend cooperative models for group businesses
"""

from __future__ import annotations

import json
import logging
import math

logger = logging.getLogger(__name__)

# ─── Tool Definitions for Claude API ───

TOOL_DEFINITIONS = [
    {
        "name": "market_lookup",
        "description": (
            "Look up current market prices for goods and services in Uganda. "
            "Use this when you need real price data for budgets, cost estimates, "
            "or price comparisons. Returns prices in UGX."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item": {
                    "type": "string",
                    "description": "The item to look up (e.g., 'broiler chicks', 'sewing machine', 'cement')",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (poultry, agriculture, telecoms, construction, tailoring, salon, food_vending, energy)",
                },
            },
            "required": ["item"],
        },
    },
    {
        "name": "validate_budget",
        "description": (
            "Validate a business budget for completeness and realism. "
            "Checks if all necessary cost categories are included, if amounts "
            "are within typical Uganda market ranges, and flags any suspicious items."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "description": "Type of business (e.g., 'poultry', 'tailoring', 'mobile_money')",
                },
                "startup_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string"},
                            "amount_ugx": {"type": "number"},
                        },
                    },
                    "description": "List of startup cost items with amounts in UGX",
                },
                "monthly_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string"},
                            "amount_ugx": {"type": "number"},
                        },
                    },
                    "description": "List of monthly recurring cost items",
                },
            },
            "required": ["business_type", "startup_items"],
        },
    },
    {
        "name": "assess_risk",
        "description": (
            "Assess business risks for a specific type of venture in Uganda. "
            "Returns common risks, their likelihood, impact, and practical mitigations "
            "specific to the Uganda context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "description": "Type of business to assess risks for",
                },
                "location": {
                    "type": "string",
                    "description": "Location in Uganda (e.g., 'Kampala', 'Jinja', 'rural Mukono')",
                },
                "capital_ugx": {
                    "type": "number",
                    "description": "Starting capital in UGX",
                },
            },
            "required": ["business_type"],
        },
    },
    {
        "name": "check_regulations",
        "description": (
            "Check business registration and compliance requirements in Uganda. "
            "Returns KCCA permits, URA tax obligations, NSSF requirements, "
            "and sector-specific licenses needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "description": "Type of business",
                },
                "location": {
                    "type": "string",
                    "description": "City or district (affects which authority — KCCA vs district)",
                },
                "has_employees": {
                    "type": "boolean",
                    "description": "Whether the business will have employees",
                },
            },
            "required": ["business_type"],
        },
    },
    {
        "name": "calculate_break_even",
        "description": (
            "Calculate break-even point given startup costs, monthly costs, and monthly revenue. "
            "Returns months to break even and validates the math."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "startup_cost_ugx": {
                    "type": "number",
                    "description": "Total one-time startup investment in UGX",
                },
                "monthly_cost_ugx": {
                    "type": "number",
                    "description": "Total monthly operating costs in UGX",
                },
                "monthly_revenue_ugx": {
                    "type": "number",
                    "description": "Expected monthly revenue in UGX",
                },
            },
            "required": ["startup_cost_ugx", "monthly_cost_ugx", "monthly_revenue_ugx"],
        },
    },
    {
        "name": "find_funding",
        "description": (
            "Find funding opportunities for a young entrepreneur in Uganda. "
            "Searches government youth funds (YLP, Emyooga, UWEP, PDM), "
            "microfinance loans (BRAC, FINCA), VSLAs, and accelerator programmes. "
            "Returns eligibility requirements and how to apply."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "description": "Type of business needing funding",
                },
                "location": {
                    "type": "string",
                    "description": "Location in Uganda",
                },
                "capital_needed_ugx": {
                    "type": "number",
                    "description": "Amount of funding needed in UGX",
                },
                "stage": {
                    "type": "string",
                    "description": "Business stage: idea, planning, launched, growing",
                },
            },
            "required": ["business_type"],
        },
    },
    {
        "name": "find_suppliers",
        "description": (
            "Find suppliers and markets for business inputs in Uganda. "
            "Returns supplier locations, typical prices, and tips for "
            "getting the best deals."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "description": "Type of business",
                },
                "items_needed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of supplies/equipment needed",
                },
                "location": {
                    "type": "string",
                    "description": "Preferred location for sourcing",
                },
            },
            "required": ["business_type"],
        },
    },
    {
        "name": "suggest_cooperative",
        "description": (
            "Suggest cooperative or group business models. "
            "Recommends how youth can pool resources, form VSLAs or SACCOs, "
            "and start group enterprises for shared benefits."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "description": "Type of business for the cooperative",
                },
                "num_members": {
                    "type": "number",
                    "description": "Number of potential group members",
                },
                "total_capital_ugx": {
                    "type": "number",
                    "description": "Total capital pool from all members",
                },
            },
            "required": ["business_type"],
        },
    },
]


# ─── Tool Implementations ───

def execute_tool(name: str, arguments: dict, market_data: list[dict] | None = None) -> str:
    """Execute a tool and return the result as a string."""
    handlers = {
        "market_lookup": _market_lookup,
        "validate_budget": _validate_budget,
        "assess_risk": _assess_risk,
        "check_regulations": _check_regulations,
        "calculate_break_even": _calculate_break_even,
        "find_funding": _find_funding,
        "find_suppliers": _find_suppliers,
        "suggest_cooperative": _suggest_cooperative,
    }

    handler = handlers.get(name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        if name == "market_lookup":
            return handler(arguments, market_data or [])
        return handler(arguments)
    except Exception as e:
        logger.error("Tool %s failed: %s", name, e)
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


def _market_lookup(args: dict, market_data: list[dict]) -> str:
    """Search market prices."""
    item_query = args.get("item", "").lower()
    category = args.get("category", "").lower()

    results = []
    for p in market_data:
        text = f"{p.get('item', '')} {p.get('item_lg', '')} {p.get('item_sw', '')}".lower()
        cat = p.get("category", "").lower()

        if category and cat != category:
            continue
        if item_query and item_query not in text:
            query_words = set(item_query.split())
            text_words = set(text.split())
            if not query_words & text_words:
                continue

        results.append({
            "item": p["item"],
            "price_ugx": p["price_ugx"],
            "unit": p["unit"],
            "category": p.get("category", ""),
            "trend": p.get("trend", "stable"),
            "location": p.get("location", "Kampala"),
        })

    if not results:
        return json.dumps({
            "found": False,
            "message": f"No prices found for '{item_query}'. Try a broader search term.",
        })

    return json.dumps({"found": True, "prices": results[:10], "count": len(results)})


def _validate_budget(args: dict) -> str:
    """Validate budget completeness and realism."""
    biz_type = args.get("business_type", "").lower()
    startup = args.get("startup_items", [])
    monthly = args.get("monthly_items", [])

    issues = []
    suggestions = []

    required_startup = {
        "poultry": ["chicks", "feed", "vaccines", "housing", "drinkers", "feeders"],
        "tailoring": ["sewing machine", "fabric", "scissors", "thread", "workspace"],
        "mobile_money": ["float", "sim card", "kiosk", "signage"],
        "salon": ["clippers", "mirror", "chair", "products", "rent"],
        "food_vending": ["cooking equipment", "ingredients", "table", "utensils"],
        "boda_repair": ["tools", "spare parts", "workspace"],
    }

    required_monthly = ["rent", "transport", "airtime", "utilities"]

    startup_names = [s.get("item", "").lower() for s in startup]
    if biz_type in required_startup:
        for req in required_startup[biz_type]:
            if not any(req in name for name in startup_names):
                issues.append(f"Missing startup item: {req}")

    monthly_names = [m.get("item", "").lower() for m in monthly]
    for req in required_monthly:
        if not any(req in name for name in monthly_names):
            suggestions.append(f"Consider adding monthly cost: {req}")

    total_startup = sum(s.get("amount_ugx", 0) for s in startup)
    if total_startup < 100_000:
        issues.append("Startup budget seems very low (< UGX 100,000). Most businesses need at least UGX 200,000-500,000.")
    if total_startup > 50_000_000:
        issues.append("Startup budget is very high (> UGX 50M). This is unusual for a micro-enterprise.")

    for item in startup:
        amt = item.get("amount_ugx", 0)
        if amt <= 0:
            issues.append(f"Item '{item.get('item')}' has zero or negative cost")
        if amt > total_startup * 0.7:
            suggestions.append(f"Item '{item.get('item')}' is {amt/total_startup*100:.0f}% of total — very concentrated risk")

    return json.dumps({
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "total_startup_ugx": total_startup,
        "total_monthly_ugx": sum(m.get("amount_ugx", 0) for m in monthly),
    })


def _assess_risk(args: dict) -> str:
    """Assess business risks."""
    biz_type = args.get("business_type", "").lower()
    location = args.get("location", "Kampala").lower()
    capital = args.get("capital_ugx", 0)

    risks = [
        {
            "risk": "Theft and security",
            "likelihood": "medium", "impact": "high",
            "mitigation": "Lock up valuables daily, don't keep excess cash, vary banking times, install basic padlock",
        },
        {
            "risk": "Load shedding (power outages)",
            "likelihood": "high", "impact": "medium",
            "mitigation": "Invest in solar panel (UGX 200K-500K) or use manual alternatives. Have backup charcoal/gas for cooking businesses",
        },
        {
            "risk": "Seasonal demand fluctuations",
            "likelihood": "high", "impact": "medium",
            "mitigation": "Save 20% of peak-season profits for low season. Diversify products/services for year-round income",
        },
        {
            "risk": "Health emergency (you or family)",
            "likelihood": "medium", "impact": "high",
            "mitigation": "Join NHIS or community health scheme. Keep emergency fund (3 months expenses). Train someone to run business if you're sick",
        },
    ]

    specific_risks = {
        "poultry": [
            {"risk": "Disease outbreak (Newcastle, Gumboro)", "likelihood": "high", "impact": "critical",
             "mitigation": "Strict vaccination schedule, bio-security (visitor limits, foot bath), buy from certified hatcheries"},
            {"risk": "Feed price spikes", "likelihood": "medium", "impact": "high",
             "mitigation": "Buy in bulk during harvest when maize is cheap. Store properly. Join poultry farmer cooperative for bulk discounts"},
        ],
        "food_vending": [
            {"risk": "KCCA health inspection fines", "likelihood": "medium", "impact": "medium",
             "mitigation": "Get food handler's certificate (UGX 50,000). Maintain hygiene standards. Keep certificate visible"},
            {"risk": "Rain disrupting outdoor stall", "likelihood": "high", "impact": "medium",
             "mitigation": "Invest in tarpaulin cover (UGX 30,000). Consider semi-permanent structure if location is stable"},
        ],
        "mobile_money": [
            {"risk": "Armed robbery", "likelihood": "medium", "impact": "critical",
             "mitigation": "Don't keep excess cash (bank daily), vary banking routes/times, consider hiring security for high-volume locations"},
            {"risk": "Fraud and fake IDs", "likelihood": "high", "impact": "medium",
             "mitigation": "Always verify IDs carefully, never process suspicious transactions, report fraud to telecom provider immediately"},
        ],
        "tailoring": [
            {"risk": "Late delivery losing school contracts", "likelihood": "medium", "impact": "high",
             "mitigation": "Start production 2 months before term begins, hire temporary help during peak, always under-promise and over-deliver"},
        ],
        "salon": [
            {"risk": "Equipment damage from power surges", "likelihood": "medium", "impact": "high",
             "mitigation": "Use surge protectors (UGX 20,000-50,000), unplug equipment during storms, insure expensive items"},
        ],
    }

    if biz_type in specific_risks:
        risks.extend(specific_risks[biz_type])

    if "kampala" in location:
        risks.append({
            "risk": "High competition in Kampala",
            "likelihood": "high", "impact": "medium",
            "mitigation": "Differentiate through quality, customer service, and niche specialization. Build loyal customer base before expanding",
        })
    elif any(rural in location for rural in ["rural", "village", "trading centre"]):
        risks.append({
            "risk": "Limited customer base in rural area",
            "likelihood": "high", "impact": "high",
            "mitigation": "Serve multiple trading centres, offer delivery, use market days effectively, consider mobile business model",
        })

    if capital and capital < 300_000:
        risks.append({
            "risk": "Insufficient starting capital",
            "likelihood": "high", "impact": "high",
            "mitigation": "Start very small (pilot), reinvest all profits, join a VSLA for additional capital after 3-6 months track record",
        })

    return json.dumps({"business_type": biz_type, "location": location, "risks": risks})


def _check_regulations(args: dict) -> str:
    """Check regulatory requirements."""
    biz_type = args.get("business_type", "").lower()
    location = args.get("location", "Kampala").lower()
    has_employees = args.get("has_employees", False)

    regs = []

    regs.append({
        "requirement": "Trading License",
        "authority": "KCCA" if "kampala" in location else "District Local Government",
        "cost_ugx": "50,000-200,000/year depending on business size",
        "deadline": "Before starting operations",
        "details": "Required for all commercial activities. Apply at your division/sub-county office.",
        "penalty": "Fine of up to UGX 500,000 and closure order",
    })

    regs.append({
        "requirement": "URA Tax Registration (TIN)",
        "authority": "Uganda Revenue Authority",
        "cost_ugx": "Free",
        "deadline": "Within 30 days of starting business",
        "details": "Register for TIN at ura.go.ug or any URA office. Required for all businesses. "
                   "Income below UGX 150M/year: presumptive tax (1.5% of turnover). "
                   "Above UGX 150M: standard income tax rates apply.",
        "penalty": "5% of tax due per month of delay",
    })

    if has_employees:
        regs.append({
            "requirement": "NSSF Registration",
            "authority": "National Social Security Fund",
            "cost_ugx": "15% of employee salary (10% employer, 5% employee)",
            "deadline": "Within 30 days of hiring first employee",
            "details": "Mandatory for all employers with 5+ employees. Recommended even for fewer.",
            "penalty": "Penalty of 5% per month on unpaid contributions",
        })

    sector_regs = {
        "food": [
            {
                "requirement": "Food Handler's Certificate",
                "authority": "KCCA Health Department" if "kampala" in location else "District Health Office",
                "cost_ugx": "50,000",
                "deadline": "Before starting food business",
                "details": "Medical examination + hygiene training. Valid for 1 year. Must be displayed at business premises.",
            },
            {
                "requirement": "Public Health Permit",
                "authority": "Local health inspector",
                "cost_ugx": "100,000-200,000/year",
                "deadline": "Before opening to public",
                "details": "Inspection of premises for hygiene, waste disposal, water supply, and food storage.",
            },
        ],
        "poultry": [
            {
                "requirement": "Livestock Movement Permit",
                "authority": "District Veterinary Office",
                "cost_ugx": "20,000 per movement",
                "deadline": "Before transporting live birds",
                "details": "Required when moving poultry between districts. Helps control disease spread.",
            },
        ],
        "mobile_money": [
            {
                "requirement": "Telecom Agent Registration",
                "authority": "MTN/Airtel (via authorized super-agent)",
                "cost_ugx": "Free (but requires float capital)",
                "deadline": "Before operations",
                "details": "Register through authorized aggregator. Requires valid National ID, passport photo, physical location.",
            },
        ],
        "salon": [
            {
                "requirement": "Health & Safety Compliance",
                "authority": "Local health inspector",
                "cost_ugx": "50,000-100,000/year",
                "deadline": "Before opening",
                "details": "Sterilization of equipment, proper waste disposal, ventilation requirements.",
            },
        ],
    }

    sector_map = {
        "poultry": "poultry",
        "food_vending": "food", "rolex": "food", "snack": "food", "catering": "food",
        "restaurant": "food", "chapati": "food", "mandazi": "food",
        "mobile_money": "mobile_money", "airtime": "mobile_money",
        "salon": "salon", "barbershop": "salon", "hairdress": "salon",
    }

    sector = None
    for key, val in sector_map.items():
        if key in biz_type:
            sector = val
            break

    if sector and sector in sector_regs:
        regs.extend(sector_regs[sector])

    regs.append({
        "requirement": "Business Name Registration (Optional for small businesses)",
        "authority": "Uganda Registration Services Bureau (URSB)",
        "cost_ugx": "25,000 (sole proprietor) / 100,000 (partnership) / 350,000 (company)",
        "deadline": "Recommended within first 6 months of operation",
        "details": "Not legally required for sole traders under UGX 50M turnover, but helps with: "
                   "opening business bank accounts, getting supplier credit, bidding for contracts, "
                   "and building professional reputation.",
    })

    return json.dumps({
        "business_type": biz_type,
        "location": location,
        "regulations": regs,
        "disclaimer": "This is general guidance. Regulations change — always verify with the relevant authority before investing.",
    })


def _calculate_break_even(args: dict) -> str:
    """Calculate break-even point."""
    startup = args.get("startup_cost_ugx", 0)
    monthly_cost = args.get("monthly_cost_ugx", 0)
    monthly_revenue = args.get("monthly_revenue_ugx", 0)

    if monthly_revenue <= monthly_cost:
        return json.dumps({
            "viable": False,
            "message": f"Monthly costs (UGX {monthly_cost:,}) exceed or equal monthly revenue "
                       f"(UGX {monthly_revenue:,}). This business will not break even. "
                       "You need to either increase revenue or reduce costs.",
            "monthly_profit": monthly_revenue - monthly_cost,
        })

    monthly_profit = monthly_revenue - monthly_cost
    months = math.ceil(startup / monthly_profit)
    assessment = "excellent" if months <= 3 else "good" if months <= 6 else "moderate" if months <= 12 else "risky"

    return json.dumps({
        "viable": True,
        "startup_cost_ugx": startup,
        "monthly_cost_ugx": monthly_cost,
        "monthly_revenue_ugx": monthly_revenue,
        "monthly_profit_ugx": monthly_profit,
        "break_even_months": months,
        "assessment": assessment,
        "roi_annual": round((monthly_profit * 12) / max(startup, 1) * 100, 1),
        "explanation": f"With UGX {monthly_profit:,} monthly profit, you recover your "
                       f"UGX {startup:,} investment in {months} month{'s' if months != 1 else ''}. "
                       f"Annual ROI: {round((monthly_profit * 12) / max(startup, 1) * 100, 1)}%. "
                       f"Assessment: {assessment}.",
    })


def _find_funding(args: dict) -> str:
    """Find matching funding sources."""
    from .funding import FundingMatcher

    matcher = FundingMatcher()
    matches = matcher.match(
        business_type=args.get("business_type", ""),
        location=args.get("location", ""),
        capital_needed_ugx=args.get("capital_needed_ugx", 0),
        stage=args.get("stage", "idea"),
    )

    if not matches:
        return json.dumps({
            "found": False,
            "message": "No exact matches found, but consider joining a VSLA (Village Savings and Loan Association) "
                       "as a first step — no formal requirements, just community trust.",
        })

    simplified = []
    for m in matches[:5]:
        simplified.append({
            "name": m["name"],
            "type": m["type"],
            "amount": m["amount_range"],
            "eligibility": m["eligibility"],
            "how_to_apply": m["how_to_apply"],
            "interest": m.get("interest_rate", "N/A"),
        })

    return json.dumps({
        "found": True,
        "funding_options": simplified,
        "count": len(matches),
        "tip": "Start with government funds (YLP, Emyooga) — they're interest-free. "
               "Join a VSLA while you wait for approval.",
    })


def _find_suppliers(args: dict) -> str:
    """Find suppliers for business inputs."""
    biz = args.get("business_type", "").lower()
    items = args.get("items_needed", [])
    location = args.get("location", "Kampala").lower()

    suppliers_db = {
        "poultry": {
            "suppliers": [
                {"name": "Ugachick", "location": "Kampala (Namanve)", "items": "Day-old chicks, layer & broiler", "tip": "Book 2 weeks in advance, bulk discounts for 500+"},
                {"name": "Biyinzika Enterprises", "location": "Kampala", "items": "Day-old chicks, feeds, vaccines", "tip": "Established hatchery, quality guaranteed"},
                {"name": "Livestock feeds", "location": "Multiple locations", "items": "Poultry feeds, supplements", "tip": "Compare prices between dealers — varies by location"},
            ],
            "markets": ["Kalerwe Market (Kampala)", "Nakasero Market (Kampala)", "Local veterinary shops"],
            "tips": ["Buy vaccines from certified vet shops, not market vendors", "Negotiate feed prices for monthly delivery contracts", "Join a poultry WhatsApp group for shared supplier info"],
        },
        "tailoring": {
            "suppliers": [
                {"name": "Owino Market (St. Balikuddembe)", "location": "Kampala", "items": "Fabric, thread, buttons, zippers", "tip": "Cheapest fabrics in the city — go early for best selection"},
                {"name": "Kikuubo", "location": "Kampala", "items": "Wholesale fabric, sewing machines, accessories", "tip": "Wholesale prices, bargain hard — start at 50% of quoted price"},
                {"name": "Local fabric shops", "location": "All districts", "items": "Fabric, notions", "tip": "Higher prices but saves transport costs"},
            ],
            "markets": ["Owino/St. Balikuddembe Market", "Kikuubo wholesale", "Katwe (machines & parts)"],
            "tips": ["Buy quality sewing machine second-hand at Katwe — save 60%", "Stock school uniform fabric before Jan & May for peak demand", "Build relationship with one fabric dealer for credit terms"],
        },
        "food_vending": {
            "suppliers": [
                {"name": "Kalerwe Market", "location": "Kampala", "items": "Fresh vegetables, fruits, grains", "tip": "Arrive by 6am for freshest produce and best prices"},
                {"name": "Nakasero Market", "location": "Kampala", "items": "Premium produce, wholesale", "tip": "Good for bulk orders of onions, tomatoes, cabbage"},
                {"name": "Kisenyi wholesale", "location": "Kampala", "items": "Cooking oil, flour, sugar in bulk", "tip": "Cheapest bulk prices in Kampala — compare 3 shops before buying"},
            ],
            "markets": ["Kalerwe", "Nakasero", "Kisenyi wholesale", "Owino Market"],
            "tips": ["Buy perishables daily, dry goods weekly", "Compare prices at 3 different stalls before buying", "Build relationship with regular suppliers for credit"],
        },
        "salon": {
            "suppliers": [
                {"name": "Kikuubo wholesale", "location": "Kampala", "items": "Hair products, clippers, dryers", "tip": "Wholesale prices — buy in bulk for 30-40% savings"},
                {"name": "Owino Market", "location": "Kampala", "items": "Braiding hair, extensions", "tip": "Widest variety and cheapest prices in the city"},
            ],
            "markets": ["Kikuubo", "Owino Market", "Online: Jumia, Jiji"],
            "tips": ["Buy clippers from authorized dealers — they include warranty", "Stock popular hair products, not every brand — focus on top 5 sellers"],
        },
    }

    info = suppliers_db.get(biz, {
        "suppliers": [{"name": "Local market", "location": location.title(), "items": "General supplies", "tip": "Compare prices from at least 3 vendors"}],
        "markets": ["Your nearest main market", "Kampala wholesale markets for bulk orders"],
        "tips": ["Compare prices before buying", "Start with what's available locally", "Join WhatsApp groups of entrepreneurs in your sector for supplier recommendations"],
    })

    return json.dumps({
        "business_type": biz,
        "location": location,
        **info,
    })


def _suggest_cooperative(args: dict) -> str:
    """Suggest cooperative models."""
    biz = args.get("business_type", "").lower()
    members = args.get("num_members", 5)
    capital = args.get("total_capital_ugx", 0)

    models = [
        {
            "model_name": "Village Savings and Loan Association (VSLA)",
            "description": "Pool weekly savings (UGX 1,000-10,000/person), take turns borrowing for business. No bank needed.",
            "min_members": 15,
            "recommended_capital_per_person_ugx": 0,
            "benefits": ["No registration fees", "Build savings habit", "Access emergency loans", "Learn financial discipline together"],
            "how_to_start": ["Gather 15-25 trusted friends or neighbours", "Agree on weekly savings amount", "Elect leadership (chairperson, secretary, treasurer)", "Set rules in a written constitution", "Buy a lockbox with 3 keys (held by different people)", "Start saving and lending after 4 weeks"],
        },
        {
            "model_name": "Buying Cooperative (Bulk Purchasing)",
            "description": f"Pool resources to buy supplies in bulk at wholesale prices — each member saves 20-40% on inputs.",
            "min_members": 5,
            "recommended_capital_per_person_ugx": 500_000,
            "benefits": ["Wholesale prices (20-40% cheaper)", "Transport cost sharing", "Supplier negotiation power", "Quality assurance as a group"],
            "how_to_start": ["Find 5-10 entrepreneurs in the same business", "List common supplies needed monthly", "Identify cheapest wholesale suppliers", "Pool money and designate one person to buy", "Distribute supplies fairly with receipts"],
        },
        {
            "model_name": "Production Cooperative",
            "description": "Work together on large orders that one person cannot fulfil alone — especially for tailoring, catering, or farming.",
            "min_members": 3,
            "recommended_capital_per_person_ugx": 1_000_000,
            "benefits": ["Handle bigger orders and contracts", "Share equipment costs", "Learn from each other", "Build a shared brand"],
            "how_to_start": ["Find 3-5 skilled people in the same trade", "Register as a group with your Sub-County", "Create a written agreement on profit sharing", "Bid for larger contracts together", "Share workspace and equipment"],
        },
    ]

    # Add Emyooga SACCO suggestion if enough members
    if members >= 30:
        models.append({
            "model_name": "Emyooga SACCO",
            "description": "Government-backed SACCO — receive UGX 30M seed capital to lend among members at low interest.",
            "min_members": 30,
            "recommended_capital_per_person_ugx": 0,
            "benefits": ["UGX 30M government seed capital", "Low-interest loans to members", "Financial literacy training", "Government backing and recognition"],
            "how_to_start": ["Gather 30+ people in the same enterprise", "Register as SACCO with your constituency", "Complete required training", "Apply for seed capital through MSC"],
        })

    return json.dumps({
        "business_type": biz,
        "members": members,
        "cooperative_models": models,
        "tip": "Start with a VSLA — it's the easiest and builds trust before bigger ventures.",
    })
