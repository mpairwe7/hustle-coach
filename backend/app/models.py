"""Pydantic v2 schemas for HustleScale API — The National Youth Micro-Enterprise Accelerator."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ─── Chat ───

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    locale: str = Field(default="en", pattern=r"^(en|lg|sw|nyn)$")
    session_id: str | None = None
    domain: str | None = None


class Citation(BaseModel):
    source: str
    section: str | None = None
    page: str | None = None
    topic: str | None = None
    preview: str = ""


class BudgetItem(BaseModel):
    item: str
    amount_ugx: int
    notes: str = ""


class RevenueProjection(BaseModel):
    monthly_revenue: int = 0
    monthly_profit: int = 0
    assumptions: str = ""


class BreakEven(BaseModel):
    months: int = 0
    explanation: str = ""


class RiskItem(BaseModel):
    risk: str
    likelihood: str = "medium"
    impact: str = "medium"
    mitigation: str = ""


class BusinessPlan(BaseModel):
    """Structured business plan output."""
    business_name: str = ""
    executive_summary: str = ""
    startup_budget: list[BudgetItem] = []
    total_startup_cost: int = 0
    monthly_costs: list[BudgetItem] = []
    total_monthly_cost: int = 0
    revenue_projection: RevenueProjection | None = None
    break_even: BreakEven | None = None
    pricing_strategy: str = ""
    marketing_script: str = ""
    risks: list[RiskItem] = []
    next_steps: list[str] = []
    confidence: str = "medium"


class ToolCall(BaseModel):
    """Record of a tool invoked during agentic reasoning."""
    round: int = 1
    tool: str
    input: dict = {}
    output_preview: str = ""


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    faithfulness: float = 0.0
    domain: str = "general"
    business_plan: BusinessPlan | None = None
    confidence: str = "medium"
    locale: str = "en"
    disclaimer: str = ""
    cached: bool = False
    tool_calls: list[ToolCall] = []
    follow_ups: list[str] = []


class StreamChunk(BaseModel):
    token: str = ""
    done: bool = False
    citations: list[Citation] = []
    faithfulness: float = 0.0
    domain: str = "general"
    confidence: str = "medium"
    disclaimer: str = ""


# ─── Market Prices ───

class MarketPriceRequest(BaseModel):
    category: str | None = None
    item: str | None = None


class PriceEntry(BaseModel):
    item: str
    price_ugx: int
    unit: str
    category: str
    location: str = "Kampala"
    trend: str = "stable"


class MarketPriceResponse(BaseModel):
    prices: list[PriceEntry]
    last_updated: str
    disclaimer: str = "Prices are approximate and vary by location. Always verify locally."


# ─── Auth ───

class SignupRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    name: str = ""
    business_type: str = ""
    location: str = ""
    age: int | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    credits: int


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)


# ─── Feedback ───

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=-1, le=1)
    comment: str = ""


# ─── Progress Tracking (HustleScale) ───

class MilestoneItem(BaseModel):
    """A single milestone in a user's business journey."""
    id: str = ""
    title: str
    description: str = ""
    category: str = "general"  # planning, registration, launch, growth
    completed: bool = False
    completed_at: float | None = None


class ProgressUpdate(BaseModel):
    """User-submitted progress update."""
    milestone_id: str
    completed: bool = True
    notes: str = ""


class BusinessProfile(BaseModel):
    """User's business profile for tracking."""
    business_name: str = ""
    business_type: str = ""
    location: str = ""
    startup_capital_ugx: int = 0
    monthly_revenue_ugx: int = 0
    monthly_profit_ugx: int = 0
    employees: int = 0
    started_at: float | None = None
    stage: str = "idea"  # idea, planning, registered, launched, growing, scaling


class DashboardResponse(BaseModel):
    """Dashboard data for a user."""
    profile: BusinessProfile
    milestones: list[MilestoneItem] = []
    health_score: int = 0  # 0-100
    total_milestones: int = 0
    completed_milestones: int = 0
    recommendations: list[str] = []
    next_actions: list[str] = []


# ─── Funding Matcher (HustleScale) ───

class FundingSource(BaseModel):
    """A funding opportunity."""
    id: str
    name: str
    provider: str
    type: str  # grant, loan, fund, competition
    amount_range: str  # e.g. "UGX 500K - 5M"
    eligibility: str
    how_to_apply: str
    deadline: str = ""
    url: str = ""
    interest_rate: str = ""
    requirements: list[str] = []
    target_sectors: list[str] = []
    target_locations: list[str] = []


class FundingMatchRequest(BaseModel):
    business_type: str = ""
    location: str = ""
    capital_needed_ugx: int = 0
    stage: str = "idea"


class FundingMatchResponse(BaseModel):
    matches: list[FundingSource] = []
    total_available: int = 0
    disclaimer: str = (
        "Funding availability changes frequently. Always verify directly with "
        "the provider before applying. HustleScale does not guarantee approval."
    )


# ─── Cooperative Matching (HustleScale) ───

class CooperativeMatch(BaseModel):
    """A potential cooperative/group business match."""
    model_name: str
    description: str
    min_members: int = 3
    recommended_capital_per_person_ugx: int = 0
    benefits: list[str] = []
    how_to_start: list[str] = []
    examples: list[str] = []


class CooperativeMatchResponse(BaseModel):
    matches: list[CooperativeMatch] = []
    disclaimer: str = (
        "Cooperative formation requires trust and clear agreements. "
        "Always create a written MOU before pooling money."
    )


# ─── Business Doctor (HustleScale) ───

class BusinessDoctorRequest(BaseModel):
    """Request for AI Business Doctor analysis."""
    business_type: str
    monthly_revenue_ugx: int = 0
    monthly_costs_ugx: int = 0
    months_operating: int = 0
    employees: int = 0
    location: str = ""
    challenges: str = ""
    goals: str = ""


class DiagnosisItem(BaseModel):
    area: str  # revenue, costs, marketing, operations, compliance
    status: str  # healthy, warning, critical
    finding: str
    recommendation: str
    priority: str = "medium"  # low, medium, high, urgent


class BusinessDoctorResponse(BaseModel):
    overall_health: str = "fair"  # critical, poor, fair, good, excellent
    health_score: int = 50  # 0-100
    diagnosis: list[DiagnosisItem] = []
    quick_wins: list[str] = []
    growth_opportunities: list[str] = []
    disclaimer: str = (
        "This analysis is based on the information you provided and general "
        "market knowledge. Actual results depend on many factors. Seek advice "
        "from experienced business mentors in your community."
    )


# ─── Leaderboard (HustleScale) ───

class LeaderboardEntry(BaseModel):
    rank: int
    name: str  # anonymised
    business_type: str
    location: str
    stage: str
    milestones_completed: int
    months_active: int
    badge: str = ""  # rising_star, consistent_hustler, community_builder


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry] = []
    total_entrepreneurs: int = 0
    total_businesses_launched: int = 0
    total_jobs_created: int = 0
    impact_note: str = ""


# ─── National Impact Stats ───

class ImpactStats(BaseModel):
    total_users: int = 0
    businesses_planned: int = 0
    businesses_launched: int = 0
    jobs_created: int = 0
    total_capital_mobilised_ugx: int = 0
    regions_reached: int = 0
    avg_revenue_increase_pct: int = 0


# Rebuild forward refs
BusinessPlan.model_rebuild()
DashboardResponse.model_rebuild()
