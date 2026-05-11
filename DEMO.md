# HustleScale Demo Script — 3 Minutes

> National Science Week Future Makers Hackathon 2026
> "How AI Can Power Uganda Toward a $500 Billion Economy"

---

## Minute 1: The Problem + Landing Page (0:00-1:00)

### Open with Impact
> "10 million Ugandan youth aged 18-30 are unemployed or underemployed. The NEET rate exceeds 50%. These are young people with ideas, skills, and energy — but no access to business planning tools, no knowledge of available funding, and no structured support to turn a hustle into a sustainable business."

### Show Landing Page
- **HustleScale: The National Youth Micro-Enterprise Accelerator**
- Scroll through: Impact stats counter (users, businesses planned, launched, jobs created)
- Point out: 8 features (AI Business Plans, Business Doctor, Funding Matcher, Dashboard, Voice-First, Cooperative Matcher, Market Intelligence, Leaderboard)
- Show: 27 business types supported, 4 languages, 300+ knowledge entries, fully offline-capable PWA
- Toggle dark mode from Settings to show polish

> "HustleScale is not a chatbot. It's a complete business accelerator — from idea to income."

---

## Minute 2: Live Demo — Business Plan + Funding (1:00-2:00)

### Create a Business Plan
1. Click **"Start Your Hustle"**
2. Type or speak: *"I want to start a poultry farm with 100 broilers near Mukono. I have UGX 1.5 million."*
3. Show the **agentic tool pipeline**:
   - "Looking up market prices..." (real UGX prices for chicks, feed, vaccines)
   - "Validating your budget..." (checks completeness)
   - "Calculating break-even..." (real math)
   - "Assessing business risks..." (location-aware)
   - "Searching funding opportunities..." (YLP, Emyooga, VSLAs)
   - "Checking legal requirements..." (KCCA, URA TIN, vet permits)

4. Show the **BusinessPlan card**: 
   - Side-by-side startup/monthly budgets with real UGX prices
   - Revenue projection + break-even metrics
   - Risk cards (Newcastle disease, feed price spikes)
   - Copyable marketing script
   - Checkable next steps with progress bar

### Follow-up: Find Funding
5. Click follow-up chip: *"What funding can I apply for?"*
6. Show funding matches: YLP (interest-free), Emyooga SACCO, VSLA, with step-by-step application guides

> "Every number is real. Every price is current. Every risk is Uganda-specific."

---

## Minute 3: Dashboard + Voice + Architecture (2:00-3:00)

### Dashboard
1. Navigate to **My Dashboard**
2. Show: Health Score ring, milestone checklist (12 steps from idea to scaling)
3. Click **Business Doctor** tab -> Run check-up -> Show instant diagnosis with recommendations
4. Show progress tracking: mark a milestone as complete, watch health score increase

### Voice Demo (if time allows)
1. Press mic button
2. Speak in **Luganda**: *"Njagala okutandika okulunda enkoko"* (I want to start poultry farming)
3. Show: Recognised, classified, plan generated in Luganda-aware English

### Leaderboard
1. Quick flash of **National Leaderboard** with anonymised success stories
2. Filter stories by business type (Poultry, Catering, Tailoring, etc.)
3. Impact stats: "Every business launched creates jobs, supports families"

### Settings (quick flash)
1. Show **Settings page** — toggle Dark Mode, switch to Luganda, adjust TTS speed

### Architecture Slide (final 15 seconds)
> "Under the hood: 8 agentic tools in a ReAct loop, hybrid RAG with 300+ knowledge base entries across 42 files, 27 business models, 58 market prices with April 2026 data, 13 funding sources, tax compliance and employment law guides, 4-language support, 177 automated tests, ethical guardrails, and it's completely free — powered by Groq."

### Close
> "HustleScale doesn't promise success — it gives you the plan, the funding, the knowledge, and the community to earn it. Uganda's $500 billion economy starts with one young person and one business plan at a time."

---

## Backup Features (if asked)

| Feature | Demo Prompt |
|---|---|
| Multi-turn context | "start rolex business near Makerere" -> "what are the risks?" -> "how do I get customers?" |
| Market prices | "What are current prices for poultry feed?" |
| Financial literacy | "Teach me how to separate business and personal money" |
| Regulatory | "What licenses do I need for a salon in Kampala?" |
| Cooperative | "How do I start a buying cooperative with 5 friends?" |
| Success stories | "Tell me about a young person who started from nothing" |
| Business Doctor | "My business earns 800K but I spend 600K — how do I improve?" |

## Emergency Fallback

| Issue | Solution |
|---|---|
| Groq rate limit | Auto-retries with exponential backoff; fallback to OpenRouter (`LLM_PROVIDER=openrouter`) |
| Voice not working | Type demo queries instead, show voice button exists |
| Qdrant not available | Keyword fallback on 300+-entry in-memory knowledge base |
| Slow response | Streaming auto-falls back to sync `/v1/chat`; user sees toast notification |
| Dark mode glitch | Toggle via Settings page or system preference |

## Key Talking Points

1. **Impact**: Directly reduces youth unemployment by equipping them with business planning tools and funding access
2. **Scalability**: Fully free tier (Groq), works offline (PWA), multilingual, runs on any smartphone
3. **Ethics**: Never promises success, mandatory mentorship encouragement, PII partial masking, hype detection
4. **Innovation**: 8-tool agentic architecture with real-time market data, 177 automated tests, not a simple chatbot
5. **Cultural fit**: Ubuntu philosophy, UGX prices, Ugandan success stories, 5 district-specific regulatory guides, seasonal price data
6. **Measurable impact**: Dashboard tracks businesses planned -> launched -> jobs created
7. **Production-ready**: CI/CD pipeline, dark mode, i18n (4 languages), accessibility (WCAG), security hardening (rate limiting, CORS, timeouts, JWT security)
