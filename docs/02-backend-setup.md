# 2. Backend Setup — HustleCoach

## Endpoints (26 total)

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/auth/signup` | Entrepreneur registration |
| POST | `/v1/auth/login` | JWT authentication |
| GET | `/v1/auth/me` | Current user profile |
| POST | `/v1/auth/forgot-password` | Password reset request |
| POST | `/v1/auth/reset-password` | Password reset confirm |

### Chat & Coaching
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat` | Single-shot coaching response |
| POST | `/v1/chat/stream` | SSE streaming coaching |
| GET | `/v1/domains` | Business domain list |

### Market Intelligence
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/market-prices` | Current market prices |
| GET | `/v1/market-prices/categories` | Price categories |
| POST | `/v1/business-doctor` | Business health diagnostic |
| POST | `/v1/funding/match` | Funding opportunity matcher |
| GET | `/v1/funding/all` | All funding sources |

### Dashboard & Gamification
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/dashboard` | Entrepreneur dashboard |
| PUT | `/v1/dashboard/milestone` | Update milestone |
| PUT | `/v1/dashboard/profile` | Update profile |
| GET | `/v1/impact` | Platform impact stats |
| GET | `/v1/leaderboard` | National rankings |

### Voice & Language
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/voice/stt` | Speech-to-text |
| POST | `/v1/voice/tts` | Text-to-speech |
| POST | `/v1/translate` | Translation |
| POST | `/v1/detect-language` | Language detection |
| WS | `/v1/voice/chat/stream` | Streaming voice coaching |

## Service Layer — CoachingService

9-stage pipeline:
1. InputGuard (injection, blocked content, PII)
2. Semantic cache lookup (cosine similarity)
3. Domain classification (supervisor routing)
4. Market intelligence fetch (real-time prices)
5. Hybrid RAG retrieval (BM25 + dense + rerank)
6. LLM synthesis with 8 agentic tools
7. Business plan extraction (structured output)
8. OutputGuard (hype detection, PII, grounding)
9. Cache store (for future hits)
