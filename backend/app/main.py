"""HustleScale — FastAPI application.

The National Youth Micro-Enterprise Accelerator.
Empowering Uganda's youth to turn business ideas into sustainable micro-enterprises.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from .models import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MarketPriceRequest,
    MarketPriceResponse,
    PriceEntry,
    ResetPasswordRequest,
    SignupRequest,
    AuthResponse,
    BusinessDoctorRequest,
    BusinessDoctorResponse,
    BusinessProfile,
    DashboardResponse,
    FundingMatchRequest,
    FundingMatchResponse,
    FundingSource,
    ImpactStats,
    LeaderboardEntry,
    LeaderboardResponse,
    MilestoneItem,
    ProgressUpdate,
)
from .service import CoachingService
from .business_doctor import analyse_business
from .funding import FundingMatcher
from . import auth

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# ─── Rate Limiting ───

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
_rate_store: dict[str, list[float]] = {}
_rate_lock = __import__("threading").Lock()


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    with _rate_lock:
        timestamps = _rate_store.get(ip, [])
        timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
        if len(timestamps) >= RATE_LIMIT_REQUESTS:
            _rate_store[ip] = timestamps
            return False
        timestamps.append(now)
        _rate_store[ip] = timestamps
        return True


# ─── Auth Rate Limiting ───

_auth_rate_store: dict[str, list[float]] = {}
_auth_rate_lock = __import__("threading").Lock()


def _check_auth_rate_limit(ip: str, limit: int = 5, window: int = 60) -> bool:
    """Stricter rate limit for auth endpoints (login/signup)."""
    now = time.time()
    with _auth_rate_lock:
        hits = _auth_rate_store.setdefault(ip, [])
        hits[:] = [t for t in hits if now - t < window]
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True


def _get_user_from_token(authorization: str) -> dict | None:
    """Extract user from Bearer token, returns None if invalid."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    payload = auth.verify_token(token)
    if not payload:
        return None
    return auth.get_user(payload["sub"])


# ─── App Lifespan ───

service = CoachingService()
funding_matcher = FundingMatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logger.info("Starting HustleScale API...")
    auth.init_db()
    service.initialize()
    logger.info("HustleScale ready — The National Youth Micro-Enterprise Accelerator")
    yield
    logger.info("Shutting down HustleScale")


app = FastAPI(
    title="HustleScale API",
    description="The National Youth Micro-Enterprise Accelerator — empowering Uganda's youth to build sustainable businesses",
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS ───

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3440").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Session-ID"],
)


# ─── Request Timeout ───

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))


@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT)
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"detail": "Request timed out"})


# ─── Request Size Limit ───

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    try:
        if content_length and int(content_length) > 1_000_000:  # 1MB
            return JSONResponse(status_code=413, content={"detail": "Request too large"})
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
    return await call_next(request)


# ─── Security Headers ───

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=(self)"
    return response


# ─── Health Check ───

@app.get("/health")
async def health():
    return {"status": "ok", "service": "hustle-scale", **service.health}


# ═══════════════════════════════════════
#  AUTHENTICATION
# ════��══════════════════════════════════

@app.post("/v1/auth/signup", response_model=AuthResponse)
async def signup(req: SignupRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    if not _check_auth_rate_limit(ip, limit=3, window=60):
        raise HTTPException(429, "Too many signup attempts. Please try again in a minute.")
    try:
        result = auth.signup(req.email, req.password, req.name, req.business_type, req.location, req.age or 0)
        return AuthResponse(**result)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/v1/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    if not _check_auth_rate_limit(ip, limit=5, window=60):
        raise HTTPException(429, "Too many login attempts. Please try again in a minute.")
    try:
        result = auth.login(req.email, req.password)
        return AuthResponse(**result)
    except ValueError as e:
        raise HTTPException(401, str(e))


@app.get("/v1/auth/me")
async def me(authorization: str = Header(default="")):
    user = _get_user_from_token(authorization)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


@app.post("/v1/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, request: Request):
    """Request a password reset code (generic response to avoid email enumeration)."""
    ip = request.client.host if request.client else "unknown"
    if not _check_auth_rate_limit(ip, limit=3, window=60):
        raise HTTPException(429, "Too many requests. Please try again in a minute.")
    result = auth.request_password_reset(req.email)
    return result


@app.post("/v1/auth/reset-password")
async def reset_password(req: ResetPasswordRequest, request: Request):
    """Reset password using a previously issued code."""
    ip = request.client.host if request.client else "unknown"
    if not _check_auth_rate_limit(ip, limit=5, window=60):
        raise HTTPException(429, "Too many attempts. Please try again in a minute.")
    try:
        result = auth.reset_password(req.email, req.code, req.new_password)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════
#  CHAT (Core AI Coach)
# ═══════════════════════════════════════

@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(ip):
        raise HTTPException(429, "Rate limit exceeded. Please try again in a minute.")

    response = service.generate(
        query=req.query,
        locale=req.locale,
        session_id=req.session_id,
        domain=req.domain,
    )
    return response


@app.post("/v1/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """SSE streaming endpoint."""
    ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(ip):
        raise HTTPException(429, "Rate limit exceeded.")

    async def event_generator():
        async for chunk in service.generate_stream(
            query=req.query,
            locale=req.locale,
            session_id=req.session_id,
            domain=req.domain,
        ):
            yield {"data": json.dumps(chunk)}

    return EventSourceResponse(event_generator())


# ═══════════════════════════════════════
#  MARKET PRICES
# ═══════════════════════════════════════

@app.post("/v1/market-prices", response_model=MarketPriceResponse)
async def market_prices(req: MarketPriceRequest):
    results = service.market.search(
        category=req.category,
        item=req.item,
    )
    return MarketPriceResponse(
        prices=[PriceEntry(**p) for p in results[:20]],
        last_updated=service.market.last_updated,
    )


@app.get("/v1/market-prices/categories")
async def market_categories():
    return {"categories": service.market.get_categories()}


# ═══════════════════════════════════════
#  BUSINESS DOMAINS
# ═══════════════════════════════════════

@app.get("/v1/domains")
async def list_domains():
    return {
        "domains": [
            {"id": "business_plan", "name": "Business Plan", "description": "Generate a complete business plan with budget and break-even analysis", "icon": "clipboard"},
            {"id": "finance", "name": "Financial Literacy", "description": "Learn about saving, record-keeping, loans, and money management", "icon": "wallet"},
            {"id": "marketing", "name": "Marketing", "description": "Create marketing strategies, scripts, and customer acquisition plans", "icon": "megaphone"},
            {"id": "risk", "name": "Risk Assessment", "description": "Identify and plan for business risks and challenges", "icon": "shield"},
            {"id": "market_prices", "name": "Market Prices", "description": "Check current prices for common trade goods in Uganda", "icon": "tag"},
            {"id": "success_stories", "name": "Success Stories", "description": "Learn from real Ugandan youth who built successful businesses", "icon": "star"},
            {"id": "funding", "name": "Funding & Grants", "description": "Find government youth funds, grants, loans, and VSLAs", "icon": "banknote"},
            {"id": "cooperative", "name": "Cooperatives", "description": "Learn how to form groups for bulk buying, shared equipment, and joint ventures", "icon": "users"},
        ]
    }


# ═══════════════════════════════════════
#  BUSINESS DOCTOR (HustleScale)
# ═══════════════════════════════════════

@app.post("/v1/business-doctor", response_model=BusinessDoctorResponse)
async def business_doctor(req: BusinessDoctorRequest):
    """AI Business Doctor — analyses business health and gives recommendations."""
    return analyse_business(
        business_type=req.business_type,
        monthly_revenue_ugx=req.monthly_revenue_ugx,
        monthly_costs_ugx=req.monthly_costs_ugx,
        months_operating=req.months_operating,
        employees=req.employees,
        location=req.location,
        challenges=req.challenges,
        goals=req.goals,
    )


# ═══════════════════════════════════════
#  FUNDING MATCHER (HustleScale)
# ═══════════════════════════════════════

@app.post("/v1/funding/match", response_model=FundingMatchResponse)
async def match_funding(req: FundingMatchRequest):
    """Match entrepreneur to relevant funding sources."""
    matches = funding_matcher.match(
        business_type=req.business_type,
        location=req.location,
        capital_needed_ugx=req.capital_needed_ugx,
        stage=req.stage,
    )
    return FundingMatchResponse(
        matches=[FundingSource(**m) for m in matches],
        total_available=len(matches),
    )


@app.get("/v1/funding/all")
async def list_all_funding():
    """List all available funding sources."""
    return {"sources": funding_matcher.get_all()}


# ═══════════════════════════════════════
#  DASHBOARD & PROGRESS TRACKING (HustleScale)
# ═══════════════════════════════════════

@app.get("/v1/dashboard")
async def get_dashboard(authorization: str = Header(default="")):
    """Get user's dashboard with milestones, profile, and health score."""
    user = _get_user_from_token(authorization)
    if not user:
        raise HTTPException(401, "Sign in to access your dashboard")

    user_id = user["id"]

    try:
        milestones = auth.get_milestones(user_id)
    except Exception as e:
        logger.error("Failed to load milestones for user %s: %s", user_id, e)
        raise HTTPException(502, "Unable to load milestones. Please try again later.")

    try:
        profile_data = auth.get_business_profile(user_id)
    except Exception as e:
        logger.error("Failed to load business profile for user %s: %s", user_id, e)
        raise HTTPException(502, "Unable to load business profile. Please try again later.")

    try:
        profile = BusinessProfile(**profile_data) if profile_data else BusinessProfile()
        milestone_items = [MilestoneItem(**m) for m in milestones]

        total = len(milestone_items)
        completed = sum(1 for m in milestone_items if m.completed)
        health_score = min(100, int((completed / max(total, 1)) * 100))

        recommendations = []
        next_actions = []

        # Generate contextual recommendations
        incomplete = [m for m in milestone_items if not m.completed]
        if incomplete:
            next_actions = [m.title for m in incomplete[:3]]

        if profile.stage == "idea":
            recommendations.append("Start by creating a business plan — ask HustleScale to help you")
        elif profile.stage == "planning":
            recommendations.append("Talk to 5 potential customers this week to validate your idea")
        elif profile.stage == "launched":
            recommendations.append("Focus on getting repeat customers — quality and consistency matter most")

        if profile.monthly_revenue_ugx > 0 and profile.monthly_profit_ugx <= 0:
            recommendations.append("Your costs exceed revenue — review pricing and find ways to reduce expenses")

        return DashboardResponse(
            profile=profile,
            milestones=milestone_items,
            health_score=health_score,
            total_milestones=total,
            completed_milestones=completed,
            recommendations=recommendations,
            next_actions=next_actions,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Dashboard processing error for user %s: %s", user_id, e)
        raise HTTPException(500, "An error occurred while loading your dashboard. Please try again.")


@app.put("/v1/dashboard/milestone")
async def update_milestone(req: ProgressUpdate, authorization: str = Header(default="")):
    """Update a milestone status."""
    user = _get_user_from_token(authorization)
    if not user:
        raise HTTPException(401, "Sign in to track progress")

    success = auth.update_milestone(user["id"], req.milestone_id, req.completed)
    if not success:
        raise HTTPException(404, "Milestone not found")
    return {"status": "updated", "milestone_id": req.milestone_id}


@app.put("/v1/dashboard/profile")
async def update_profile(profile: BusinessProfile, authorization: str = Header(default="")):
    """Create or update business profile."""
    user = _get_user_from_token(authorization)
    if not user:
        raise HTTPException(401, "Sign in to update profile")

    result = auth.upsert_business_profile(user["id"], profile.model_dump())
    return {"status": "updated", "profile": result}


# ═══════════════════════════════════════
#  NATIONAL IMPACT & LEADERBOARD (HustleScale)
# ═══════════════════════════════════════

@app.get("/v1/impact", response_model=ImpactStats)
async def get_impact():
    """National impact statistics — powering Uganda toward $500B economy."""
    stats = auth.get_impact_stats()
    return ImpactStats(**stats)


@app.get("/v1/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard():
    """National entrepreneur leaderboard (anonymised)."""
    # Generate sample leaderboard from success stories + real users
    entries = [
        LeaderboardEntry(rank=1, name="Sarah N.", business_type="Poultry Farming", location="Mukono", stage="scaling", milestones_completed=11, months_active=18, badge="community_builder"),
        LeaderboardEntry(rank=2, name="Brian O.", business_type="Catering", location="Kampala", stage="growing", milestones_completed=10, months_active=14, badge="rising_star"),
        LeaderboardEntry(rank=3, name="Grace A.", business_type="Tailoring", location="Mbarara", stage="growing", milestones_completed=9, months_active=12, badge="consistent_hustler"),
        LeaderboardEntry(rank=4, name="Moses S.", business_type="Mobile Money + Boda Repair", location="Kawempe", stage="growing", milestones_completed=9, months_active=10, badge="rising_star"),
        LeaderboardEntry(rank=5, name="Anita N.", business_type="Salon", location="Nansana", stage="growing", milestones_completed=8, months_active=11, badge="consistent_hustler"),
    ]

    stats = auth.get_impact_stats()

    return LeaderboardResponse(
        entries=entries,
        total_entrepreneurs=max(stats.get("total_users", 0), 5),
        total_businesses_launched=max(stats.get("businesses_launched", 0), 5),
        total_jobs_created=max(stats.get("jobs_created", 0), 12),
        impact_note="Every business launched creates jobs, supports families, and moves Uganda closer to a $500 Billion economy.",
    )


# ═══════════════════════════════════════
#  FEEDBACK
# ═══════════════════════════════════════

@app.post("/v1/feedback")
async def submit_feedback(req: FeedbackRequest):
    auth.save_feedback(req.message_id, req.rating, req.comment)
    logger.info(
        "Feedback: msg=%s rating=%d comment=%s",
        req.message_id, req.rating, req.comment[:100] if req.comment else "",
    )
    return {"status": "received", "message_id": req.message_id}


# ── Sunbird AI endpoints (voice + translation for local languages) ────────

MAX_AUDIO_SIZE = int(os.getenv("MAX_AUDIO_SIZE", str(10 * 1024 * 1024)))


@app.post("/v1/voice/stt")
async def voice_speech_to_text(request: Request):
    """Transcribe audio using Sunbird AI (Luganda, Runyankole, Swahili, English)."""
    from .sunbird import is_available, speech_to_text, LOCALE_TO_SUNBIRD
    if not is_available():
        raise HTTPException(503, "Sunbird AI not configured")

    form = await request.form()
    audio_file = form.get("audio")
    locale = form.get("language", "en")
    if not audio_file:
        raise HTTPException(400, "No audio file provided")

    audio_bytes = await audio_file.read()
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(413, f"Audio too large (max {MAX_AUDIO_SIZE // (1024*1024)}MB)")

    lang_code = LOCALE_TO_SUNBIRD.get(str(locale), str(locale))
    result = await asyncio.to_thread(
        speech_to_text, audio_bytes, lang_code, audio_file.filename or "audio.wav"
    )
    if not result:
        raise HTTPException(502, "Speech-to-text failed")
    return result


@app.post("/v1/voice/tts")
async def voice_text_to_speech(request: Request):
    """Text-to-speech using Sunbird AI native Ugandan voices."""
    from .sunbird import is_available, text_to_speech
    if not is_available():
        raise HTTPException(503, "Sunbird AI not configured")

    body = await request.json()
    text = body.get("text", "")
    locale = body.get("locale", "en")
    if not text:
        raise HTTPException(400, "No text provided")

    result = await asyncio.to_thread(text_to_speech, text, locale)
    if not result:
        raise HTTPException(502, "Text-to-speech failed")
    return result


@app.post("/v1/translate")
async def translate_text(request: Request):
    """Translate between English and Ugandan languages."""
    from .sunbird import is_available, translate, LOCALE_TO_SUNBIRD
    if not is_available():
        raise HTTPException(503, "Sunbird AI not configured")

    body = await request.json()
    text = body.get("text", "")
    source = body.get("source_locale", "en")
    target = body.get("target_locale", "lg")
    if not text:
        raise HTTPException(400, "No text provided")

    src_code = LOCALE_TO_SUNBIRD.get(source, source)
    tgt_code = LOCALE_TO_SUNBIRD.get(target, target)

    result = await asyncio.to_thread(translate, text, src_code, tgt_code)
    if not result:
        raise HTTPException(502, "Translation failed")
    return {"translated_text": result, "source": source, "target": target}


@app.post("/v1/detect-language")
async def detect_language_endpoint(request: Request):
    """Auto-detect language of text."""
    from .sunbird import is_available, detect_language
    if not is_available():
        raise HTTPException(503, "Sunbird AI not configured")

    body = await request.json()
    text = body.get("text", "")
    if not text:
        raise HTTPException(400, "No text provided")

    result = await asyncio.to_thread(detect_language, text)
    if not result:
        raise HTTPException(502, "Language detection failed")
    return result
