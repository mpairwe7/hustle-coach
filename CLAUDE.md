# HustleScale — Architecture Decisions

## Origin
Forked from Magezi (A-Level STEM tutor), URA Chatbot, and Hustle Coach. Core RAG pipeline, guardrails, voice support, and auth system preserved. Evolved into a full national youth micro-enterprise accelerator with progress tracking, funding access, business health analysis, and cooperative matching.

## Multi-Provider LLM (free tier default)
- **Groq (default, FREE)**: Llama 3.3 70B / 3.1 8B via OpenAI-compatible API. No credit card needed.
- **OpenRouter**: Free models available (Llama 3.3 70B Instruct)
- **Anthropic Claude (optional premium)**: Extended thinking for complex plans, prompt caching (~90% cost reduction)
- **Any OpenAI-compatible API**: Together, Fireworks, local vLLM/Ollama

Provider auto-detected from env vars: `GROQ_API_KEY` → `OPENROUTER_API_KEY` → `OPENAI_API_KEY` → `ANTHROPIC_API_KEY`.
Set `LLM_PROVIDER` and `LLM_MODEL` to override. See `.env.example`.

## Domain Routing
Supervisor classifies queries into: business_plan, finance, marketing, risk, market_prices, success_stories, funding, cooperative, general.
Keyword-based (zero latency) with multilingual bridge (Luganda, Swahili, Runyankole → English token expansion).
Domain-specialist prompt injected per route.

## Agentic Architecture (ReAct Tool-Calling Loop)
This is the key differentiator — HustleScale is an AGENT, not a chatbot.

8 tools invoked via OpenAI-compatible `tool_use` API in a multi-round loop (max 5 rounds):
- `market_lookup(item, category)` — searches 34 Uganda market prices with synonym expansion
- `validate_budget(business_type, items)` — checks completeness per business type
- `calculate_break_even(startup, monthly_cost, revenue)` — validates math, computes ROI
- `check_regulations(business_type, location, has_employees)` — KCCA permits, URA TIN, NSSF
- `assess_risk(business_type, location, capital)` — location-aware risk matrix
- `find_funding(business_type, location, capital_needed, stage)` — matches to YLP, Emyooga, UWEP, PDM, VSLAs, microfinance
- `find_suppliers(business_type, items_needed, location)` — supplier locations, prices, tips
- `suggest_cooperative(business_type, num_members, total_capital)` — VSLA, buying coop, production coop, SACCO models

## New HustleScale Features (Beyond Chat)

### Business Doctor (Rule-Based + AI)
- Instant business health analysis from user-submitted metrics
- Diagnosis across 5 areas: revenue, costs, operations, compliance, marketing
- Health score (0-100), quick wins, growth opportunities
- No LLM required — pure rule-based for instant feedback

### Funding Matcher
- 10 Uganda-specific funding sources: YLP, Emyooga, UWEP, PDM, YVCF, BRAC, FINCA, VSLA, Innovation Village, Mastercard Foundation
- Matching algorithm considers: business type, location, stage, capital needs, gender
- Step-by-step application guides with requirements and deadlines

### Progress Dashboard
- 12 default milestones from idea → planning → launch → growth → scaling
- Checkable milestone tracker with progress bar
- Business profile with revenue/profit tracking
- Health score computed from milestone completion
- Contextual recommendations based on stage

### National Leaderboard
- Anonymised entrepreneur rankings (first name + initial)
- Badges: Rising Star, Consistent Hustler, Community Builder
- Impact stats: total users, businesses launched, jobs created
- Success stories with key lessons

### Cooperative Matcher
- 4 cooperative models: VSLA, Buying Cooperative, Production Cooperative, SACCO
- Step-by-step formation guides
- Emyooga integration (30M seed capital for SACCOs)

## Conversation Context Retention
- Session deque: `maxlen=30` (15 full exchanges stored in-memory per session)
- Optional Redis write-through: sessions persist across restarts when `REDIS_URL` is set
- LLM context: last `16` messages (8 exchanges) sent to LLM
- Token counting: `_estimate_tokens()` + `_truncate_history()` ensure messages fit within 70% of `LLM_CONTEXT_WINDOW`
- Abstention bypass: when session has history, skip retrieval-score abstention
- Follow-up suggestions: domain-aware, locale-specific (EN/LG/SW/NYN), 3 suggestions per response

## Security & Resilience
1. **JWT_SECRET**: Required env var; generates secure random on missing with warning (no hardcoded default)
2. **Auth rate limiting**: 5 login/min, 3 signup/min per IP (sliding window, thread-safe)
3. **Request timeout**: 30s default via `asyncio.wait_for` (configurable `REQUEST_TIMEOUT`)
4. **Request size limit**: 1MB max body via Content-Length middleware
5. **CORS whitelist**: Specific headers (`Authorization`, `Content-Type`, `Accept`, `X-Session-ID`) — not `*`
6. **LLM retry**: Exponential backoff (2^n + jitter) with 3 attempts on transient failures
7. **Password reset**: 6-digit code with 10-min expiry, generic response to prevent email enumeration

## Ethical Architecture
1. **Never-promise guardrail**: OutputGuard scans for absolute success claims
2. **Confidence scoring**: Every response carries confidence band (grounding pills)
3. **Mentorship nudge**: Always encourages real-world mentorship
4. **Regulatory compliance**: `check_regulations` tool provides law references
5. **PII partial masking**: Phone → `+256 7XX XXX XX3`, TIN → `123*******` (not full redaction)
6. **Prompt injection detection**: OWASP LLM01 patterns + spotlight markers
7. **Funding safety**: Prioritises interest-free government funds over commercial loans

## RAG Architecture
- Dense: BAAI/bge-m3 (1024d, multilingual — handles Luganda/Swahili natively)
- Sparse: BM25 with IDF weights, persisted to JSON
- Fusion: Reciprocal Rank Fusion via Qdrant query API
- Reranking: mxbai-rerank-base-v2 cross-encoder on top-20 candidates
- Fallback: Keyword overlap on 300+-entry in-memory knowledge base

## Knowledge Base: 300+ Entries (42 files)
- business-models/: 27 micro-enterprise types (including boda-boda, electrician, carpentry, car wash, e-commerce, photography, digital economy)
- market-prices/: 58 items with April 2026 UGX prices, Luganda/Swahili names, seasonal trends + mobile money charges
- success-stories/: 8 real youth entrepreneur narratives (diverse: e-commerce, SACCO, carpentry, poultry, catering, tailoring, mobile money, salon)
- financial-literacy/: 13 lessons (money management, tax compliance, insurance, pricing)
- regulatory/: KCCA trading licenses, URA TIN/tax, NSSF, sector permits + 5 district-specific guides + employment law (hiring, payroll, termination)
- uganda-challenges/: Load shedding, seasonal patterns, competition, social pressures
- funding-sources/: 13 detailed entries (YLP, Emyooga, UWEP, PDM, VSLA, YVCF, BRAC, FINCA, Innovation Village, Mastercard Foundation, UNCDF, GROW, WE4A)
- cooperative-models/: 4 cooperative formation guides

## Frontend (Glassmorphism + Ugandan Palette + Dark Mode)
- Next.js 16 + React 19 + TypeScript + Tailwind v4 + ESLint
- Warm Ugandan palette (gold #D4A017, green #2D6A4F, earth #8B5E3C, cream #FFF8E7)
- Dark mode: system preference + manual toggle via `data-theme` attribute (no flash on load)
- 7 pages: Landing, Chat, Dashboard, Leaderboard, Auth, Settings, 404
- Chat: rich markdown with code highlighting, business plan cards, follow-up chips, tool progress, i18n
- Dashboard: refactored into 6 sub-components (HealthRing, MilestoneList, BusinessDoctor, ProfileEditor, StatsOverview, DashboardShells)
- Leaderboard: national rankings, success stories with business-type filtering, user position highlight
- Settings: language preference, theme toggle, TTS voice rate slider, clear all data
- PWA: manifest.json, service worker, installable, offline-first
- Accessibility: ARIA tabs, focus-visible, focus trap in dialogs, aria-pressed, 44px touch targets
- Mobile: responsive grids, safe area padding, horizontal scroll for filter pills

## Ports
- Frontend: **3440** (dev), 3000 (Docker)
- Backend: **8808** (dev), 8000 (Docker)

## API Endpoints (16 total)
- `/v1/chat`, `/v1/chat/stream` — AI coaching with 8-tool agentic loop + streaming error recovery
- `/v1/business-doctor` — Business health analysis
- `/v1/funding/match`, `/v1/funding/all` — Funding matching
- `/v1/dashboard`, `/v1/dashboard/milestone`, `/v1/dashboard/profile` — Progress tracking (structured error responses)
- `/v1/leaderboard` — National rankings
- `/v1/impact` — National impact statistics
- `/v1/market-prices`, `/v1/market-prices/categories` — Market intelligence
- `/v1/auth/signup`, `/v1/auth/login`, `/v1/auth/me` — Authentication (rate-limited)
- `/v1/auth/forgot-password`, `/v1/auth/reset-password` — Password reset (rate-limited)
- `/v1/domains` — Business domain listing
- `/v1/feedback` — User feedback

## Testing (177 tests, 10 files)
- 14 agentic tool tests (all 8 tools)
- 22 guardrail tests (injection, hype, PII partial masking, grounding, sanitization)
- 11 supervisor routing tests (all domains + Luganda/Swahili + edge cases)
- 26 auth tests (signup, login, tokens, credits, milestones, profiles, impact stats)
- 31 follow-up generation tests (4 locales × 8 domains + filtering + fallbacks)
- 38 integration tests (token estimation, history truncation, system prompts, citations, business plan extraction)
- 15 API endpoint tests
- 6 business doctor tests
- 6 funding matcher tests
- 8 market price tests

## CI/CD
- GitHub Actions: `.github/workflows/hustle-coach-ci.yml`
  - `backend-test`: Python 3.11, pip install, pytest
  - `frontend-build`: bun install, tsc --noEmit, bun run build
  - Triggers on push/PR to dev/main for `HustleCoach/**` paths

## Conventions
- Package managers: bun (JS/TS), uv (Python) — never npm or pip
- Commits: conventional (feat/fix/docs/chore)
- Python: type hints, Ruff formatting (pyproject.toml)
- TypeScript: strict mode, ESLint (eslint.config.js)
- See CONTRIBUTING.md for full guidelines
