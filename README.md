# HustleScale — The National Youth Micro-Enterprise Accelerator

> **Empowering Uganda's youth to turn business ideas into sustainable, scalable micro-enterprises.**

HustleScale is a voice-first, multilingual AI accelerator built for unemployed and underemployed youth aged 18–30 in Uganda. It goes beyond a chatbot — an agentic AI system with 8 real tools, progress tracking, funding matching, cooperative formation, business health analysis, and a national leaderboard. From idea to income, in your language.

**Claude Hackathon 2026 — Category 3: Economic Empowerment & Education**

---

## The Problem

Uganda has one of the world's youngest populations, with over 50% of youth neither in employment, education, nor training (NEET). Many have viable business ideas — poultry farming, tailoring, mobile money vending, boda repair, salons — but lack the knowledge, mentorship, and financial literacy to execute them.

Traditional business advisory services are urban-centric, English-only, and inaccessible to the youth who need them most.

## The Solution

HustleScale meets youth where they are:

- **Voice-first** — speak your idea in Luganda, Runyankole, Swahili, or English
- **Deep conversations** — ask follow-ups, dive deeper — context is retained across 8+ exchanges
- **Instant business plans** — realistic budgets, break-even analysis, and pricing for local markets
- **8 agentic tools** — AI calls real tools in a ReAct loop: market prices, budget validation, break-even math, regulatory checks, risk assessment, funding matching, supplier search, cooperative models
- **Market intelligence** — current April 2026 UGX prices for 58+ items with synonym search, seasonal trends, and mobile money charges
- **Financial literacy** — bite-sized lessons on saving, record-keeping, pricing, and avoiding debt traps
- **27 business models** — poultry, tailoring, salon, mobile money, boda-boda transport, snack vending, fish farming, brick making, juice making, event planning, second-hand clothing, phone repair, welding, piggery, digital services, urban farming, electrician, carpentry, car wash, e-commerce/reselling, photography, and more
- **Funding matcher** — 13 Uganda-specific sources (YLP, Emyooga, UWEP, PDM, BRAC, FINCA, VSLA, YVCF, Innovation Village, Mastercard Foundation, UNCDF, GROW, WE4A)
- **Business Doctor** — instant health analysis with diagnosis, quick wins, and growth opportunities
- **Progress Dashboard** — 12-milestone tracker from idea → scaling with health score ring
- **National Leaderboard** — anonymised rankings, badges, impact stats, success stories with filtering
- **Settings** — theme (dark/light/system), language preference, TTS voice rate
- **Success stories** — real Ugandan youth who built businesses from scratch
- **Offline-first PWA** — works on 2G networks with cached knowledge base, installable
- **Ethical AI** — no hype, no false promises, confidence scoring, PII partial masking, and encouragement to seek human mentorship

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Next.js 16 PWA  │────▶│  FastAPI + RAG    │────▶│  Qdrant      │
│  Dark/Light Mode │◀────│  + 8 Agentic Tools│◀────│  Hybrid DB   │
│  Voice + Offline │     │  + Guardrails     │     │  240 entries  │
│  7 Routes        │     │  + Redis Sessions │     │  34 KB files  │
└─────────────────┘     └───────┬──────────┘     └──────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Multi-Provider LLM    │
                    │  Groq (FREE default)   │
                    │  Claude / OpenRouter   │
                    │  Retry + Token Mgmt    │
                    └───────────────────────┘
```

**Agentic pipeline:** Voice input → ASR → Multilingual bridge → Domain routing → Hybrid RAG (dense + BM25 + rerank) → **Agentic tool-calling loop** (market_lookup → validate_budget → calculate_break_even → check_regulations → assess_risk → find_funding → find_suppliers → suggest_cooperative) → Business plan extraction → Ethical guardrails → Locale-aware follow-up suggestions → TTS → Voice output

### What Makes This an Agent, Not a Chatbot

HustleScale uses a **ReAct reasoning loop** with 8 real tools (up to 5 rounds). When you ask "Help me start a poultry farm with UGX 1.5 million":

1. LLM calls `market_lookup("broiler chicks")` → gets real UGX prices
2. LLM calls `market_lookup("broiler feed")` → gets feed costs
3. LLM calls `calculate_break_even(startup=1.5M, monthly_cost=X, revenue=Y)` → validates the math
4. LLM calls `check_regulations("poultry", "Kampala")` → finds KCCA and veterinary permits needed
5. LLM calls `assess_risk("poultry", "Kampala", 1500000)` → generates location-aware risk matrix
6. LLM synthesizes everything into a structured, validated business plan

This is **not prompt engineering** — it's agentic reasoning with real tool execution.

### Deep Conversation Context

Unlike simple chatbots that forget after one exchange, HustleScale retains **16 messages of history** (8 full exchanges) per session. Ask about a rolex business, then ask "what are the risks?" — it remembers you're talking about rolexes near Makerere. Ask "how do I get customers?" — it gives Makerere-specific advice. Contextual follow-up suggestions appear after each response so you can dive deeper without retyping.

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Get a FREE Groq API key at https://console.groq.com (no credit card needed)
# Set GROQ_API_KEY=gsk_your_key_here in .env

# 2. Launch with Docker
docker compose up --build
# Knowledge base auto-indexes on first start

# 3. Open
open http://localhost:3440
```

**No paid API key required.** Groq's free tier (Llama 3.3 70B) works out of the box.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind v4 (glassmorphism + dark mode) |
| Backend | FastAPI, Python 3.11+, Pydantic v2, Ruff |
| RAG | Qdrant 1.17, BAAI/bge-m3 (1024d), BM25, mxbai-rerank |
| LLM | **Groq (FREE default)**, Claude, OpenRouter — multi-provider with agentic tool_use, retry + token mgmt |
| Voice | Web Speech API (ASR + TTS), 4 locale mappings, browser-native |
| Offline | Service Worker + PWA manifest, stale-while-revalidate |
| Auth | JWT + SQLite credit system (50 free credits), password reset, rate limiting |
| Sessions | In-memory + optional Redis write-through persistence |
| Tests | pytest (177 tests across 10 files), 100% tool/guardrail/routing/auth coverage |
| CI | GitHub Actions (pytest + TypeScript + build validation) |
| Linting | ESLint (frontend), Ruff (backend), TypeScript strict mode |

## Features

### Business Plan Generation
Describe your idea → receive:
- Executive summary
- Startup budget (itemized in UGX with real market prices)
- Monthly operating costs
- Revenue projections with assumptions
- Break-even timeline (validated by `calculate_break_even` tool)
- Pricing strategy
- Marketing script (copyable to WhatsApp)
- Risk assessment with expandable mitigations
- 5 checkable next steps with progress bar

### Conversation Context
- 8-exchange deep conversation memory
- Follow-up suggestion chips after every response
- Domain-aware suggestions ("What are the risks?" / "How should I market this?")
- Session persistence via localStorage

### Chat UX (Grok-inspired)
- Glassmorphism frosted-glass UI with dark mode support (system + manual toggle)
- Animated typing dots during LLM thinking
- Tool progress indicator ("Looking up market prices...")
- Copy message button with checkmark feedback
- Listen (TTS) button on every response with per-message play/stop
- Collapsible long messages (>800 chars)
- Thumbs up/down feedback with API integration
- Scroll-to-bottom FAB with smart auto-scroll (120px threshold)
- Clear chat with focus-trapped confirmation dialog
- Mobile-safe input with `env(safe-area-inset-bottom)` and 44px touch targets
- Streaming fallback toast when SSE unavailable
- Full i18n: all UI labels translated to EN, LG, SW, NYN

### Market Intelligence
34 items with synonym search (search "chicken" → finds broiler chicks, feed, vaccines):
- Poultry, Agriculture, Telecoms, Construction, Tailoring, Salon, Food vending, Energy
- **Seasonal trends**: price variation data for agriculture, construction, poultry (peak/low periods with % swings)

### 23 Business Models
Poultry farming, tailoring, mobile money, boda-boda transport, salon, snack vending, fish farming, brick/block making, juice making, event planning, second-hand clothing (mitumba), phone repair, welding/fabrication, piggery, digital services, urban farming/mushrooms, electrician/solar, carpentry/furniture, agro-processing, restaurant/food stall, crafts/pottery, tutoring/education, boda repair

### Knowledge Base: 300+ Entries (42 files)
- business-models/: 27 micro-enterprise types with startup costs, revenue, growth strategies + digital economy guide
- market-prices/: 58 items with April 2026 UGX prices, Luganda/Swahili names, seasonal trends + mobile money charges (MTN/Airtel)
- success-stories/: 8 real youth entrepreneur narratives (diverse sectors, regions, genders)
- financial-literacy/: 13 lessons (money management, tax compliance with URA brackets, insurance, pricing)
- regulatory/: KCCA trading licenses, URA TIN/tax, NSSF, sector permits + **5 district-specific guides** + **employment law** (hiring, payroll, termination)
- uganda-challenges/: Load shedding, seasonal patterns, competition, social pressures, supply chain
- funding-sources/: 13 detailed entries (YLP, Emyooga, UWEP, PDM, VSLA, YVCF, BRAC, FINCA, Innovation Village, Mastercard Foundation, UNCDF, GROW, WE4A)
- cooperative-models/: 4 cooperative formation guides

### Ethical Guardrails
- Never promises guaranteed success (hype pattern detection)
- Confidence scoring on all advice (high/medium/low) with grounding pills
- Clear disclaimers on financial projections
- Encourages seeking mentorship from elders and successful business owners
- KCCA/URA/NSSF regulatory compliance guidance
- Uganda NDPA compliant (PII **partial masking** — `+256 7XX XXX XX3`, not full redaction)
- OWASP LLM01 prompt injection detection
- Request timeout (30s) and request size limits (1MB)
- Auth rate limiting (5 login/min, 3 signup/min per IP)

## Project Structure

```
HustleCoach/
├── README.md                  ← This file
├── ETHICS.md                  ← Ethical analysis (9 risks, Uganda laws)
├── DEMO.md                    ← 3-minute demo script
├── CLAUDE.md                  ← Architecture decisions
├── CONTRIBUTING.md            ← Dev setup, conventions, PR guidelines
├── .env.example               ← Config (Groq free key + all settings)
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── Dockerfile + entrypoint.sh (auto-indexes on first start)
│   ├── requirements.txt
│   ├── pyproject.toml         ← Ruff + pytest config
│   ├── tests/                 ← 177 pytest tests (10 files)
│   │   ├── test_tools.py      ← 14 agentic tool tests (all 8 tools)
│   │   ├── test_guardrails.py ← 22 guardrail tests (injection, hype, PII masking)
│   │   ├── test_supervisor.py ← 11 routing tests (all domains + Luganda/Swahili)
│   │   ├── test_auth.py       ← 26 auth tests (signup, login, tokens, credits, milestones)
│   │   ├── test_service.py    ← 31 follow-up generation tests (4 locales × 8 domains)
│   │   ├── test_integration.py← 38 integration tests (token mgmt, citations, business plans)
│   │   ├── test_api.py        ← 15 API endpoint tests
│   │   ├── test_business_doctor.py ← 6 health analysis tests
│   │   ├── test_funding.py    ← 6 funding matcher tests
│   │   └── test_market_intel.py ← 8 market price tests
│   └── app/
│       ├── main.py            ← FastAPI (16 endpoints, rate limiting, timeout, size limit)
│       ├── models.py          ← Pydantic v2 (ChatResponse, auth, password reset)
│       ├── service.py         ← CoachingService (Redis sessions, locale follow-ups)
│       ├── llm.py             ← Multi-provider (Groq/Claude/OpenRouter + retry + token mgmt)
│       ├── tools.py           ← 8 agentic tools (market, budget, break-even, regs, risk, funding, suppliers, coop)
│       ├── retriever.py       ← Hybrid RAG (dense+BM25+rerank+keyword fallback)
│       ├── guardrails.py      ← OWASP LLM01-09 + anti-hype + PII partial masking
│       ├── market_intel.py    ← 34 prices with synonym search
│       ├── business_plan.py   ← Structured plan extraction
│       ├── auth.py            ← JWT + credits + password reset (secure random secret)
│       ├── cache.py           ← Semantic cache
│       ├── indexer.py         ← KB ingestion
│       └── agents/supervisor.py ← Multilingual domain routing
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── eslint.config.js       ← ESLint flat config (Next.js + TypeScript)
│   ├── next.config.mjs        ← Security headers + bundle analyzer
│   └── src/
│       ├── app/
│       │   ├── layout.tsx     ← OG tags, theme persistence, locale sync
│       │   ├── page.tsx       ← Landing page (impact stats, features, CTAs)
│       │   ├── globals.css    ← Glassmorphism + dark mode (system + manual)
│       │   ├── chat/page.tsx  ← Main chat (streaming, tools, follow-ups, i18n)
│       │   ├── dashboard/page.tsx ← Dashboard (refactored, 241 lines)
│       │   ├── leaderboard/page.tsx ← Rankings + filtered success stories
│       │   ├── settings/page.tsx ← Language, theme, TTS rate, clear data
│       │   └── auth/page.tsx  ← Login/signup
│       ├── components/
│       │   ├── ChatMessage.tsx ← Rich markdown, copy, TTS, collapse, feedback (i18n)
│       │   ├── ChatInput.tsx   ← Auto-resize, Shift+Enter, voice (i18n)
│       │   ├── Markdown.tsx    ← Zero-dep renderer with code block highlighting
│       │   ├── BusinessPlanCard.tsx ← Tables, checkable steps, copyable marketing
│       │   ├── StarterPrompts.tsx, DomainNav.tsx (memo), OfflineIndicator.tsx
│       │   ├── BottomNav.tsx   ← 5-item nav (Home, Coach, Dashboard, Leaders, Settings)
│       │   ├── LocaleHtmlLang.tsx ← Syncs document.lang with locale
│       │   ├── Skeleton.tsx, Icons.tsx, Providers.tsx
│       │   └── dashboard/     ← 6 extracted components
│       │       ├── HealthRing.tsx, MilestoneList.tsx, BusinessDoctor.tsx
│       │       ├── ProfileEditor.tsx, StatsOverview.tsx, DashboardShells.tsx
│       ├── store/
│       │   ├── useChatStore.ts ← Zustand (200-msg cap, locale, followUps)
│       │   ├── useAuthStore.ts ← Auth (token sync, logout clears all)
│       │   └── useDashboardStore.ts ← Optimistic updates, rollback
│       ├── hooks/useSpeech.ts  ← useASR + useTTS hooks
│       ├── services/voiceService.ts ← Browser-native ASR/TTS (4 Uganda locales)
│       ├── lib/api.ts          ← Typed REST client (30+ interfaces)
│       └── types/speech.d.ts   ← Web Speech API types
├── knowledge-base/
│   ├── business-models/       ← 27 business types + digital economy guide
│   ├── market-prices/         ← 58 items + seasonal trends + mobile money charges
│   ├── success-stories/       ← 8 youth entrepreneur profiles
│   ├── financial-literacy/    ← 13 lessons (money, tax, insurance)
│   ├── regulatory/            ← KCCA, URA, NSSF + 5 districts + employment law
│   ├── funding-sources.json   ← 13 funding programmes
│   ├── cooperative-models.json ← 4 cooperative types
│   └── uganda-challenges/     ← Operating environment
└── scripts/reindex.sh
```

## Running Locally

```bash
# Backend (port 8808)
cd backend
export GROQ_API_KEY=gsk_your_free_key
uv run --no-project uvicorn app.main:app --port 8808

# Frontend (port 3440)
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8808 bun run dev --port 3440

# Tests
cd backend && uv run --no-project python -m pytest tests/ -v
```

## License

MIT — Built with Ubuntu philosophy: "I am because we are."

## Team

Built for the Claude Hackathon 2026 by mpairwe7 — because every young Ugandan deserves a business mentor in their pocket.
