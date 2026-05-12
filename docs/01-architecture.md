# 1. System Architecture — HustleCoach

National Youth Micro-Enterprise Accelerator for Uganda — agentic business coaching with market intelligence.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16.2.3, React 19.2.0, Zustand 5, TanStack Query |
| Backend | FastAPI, Python 3.11, uvicorn |
| LLM | Multi-provider: Groq / OpenRouter / Claude (with 8 agentic tools) |
| Retrieval | BM25 (162 docs) + Qdrant hybrid, semantic cache |
| Voice | Sunbird AI (STT/TTS/MT), WebSocket streaming |
| Auth | JWT (signup/login, password reset) |
| Deployment | Docker → Docker Hub → Crane Cloud RENU |

## Data Flow

```
Youth entrepreneur (voice/text) → nginx:8080
    ├── / → Next.js:3000 (landing)
    ├── /chat → chat UI
    ├── /dashboard → entrepreneur dashboard
    ├── /leaderboard → national rankings
    └── /v1/* → uvicorn:8081 (FastAPI)

Backend Pipeline:
    Query → InputGuard → Domain classifier
        → Semantic cache → Market intel fetch
        → Hybrid RAG → LLM + 8 tools
        → Business plan extraction
        → OutputGuard → Response
```

## Knowledge Base (162 docs)

- 27 business model templates (poultry, salon, boda repair, etc.)
- Market prices (58+ items, regional, seasonal)
- 13 funding sources (YLP, UWEP, Emyooga, etc.)
- Financial literacy lessons
- Regulatory guides (business registration, employment law)
- Digital marketing strategies
- Success stories
