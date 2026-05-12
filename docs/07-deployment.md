# Crane Cloud Deployment — HustleCoach

National Youth Micro-Enterprise Accelerator for Uganda, deployed on Crane Cloud RENU cluster.

## Production

| Field | Value |
|-------|-------|
| URL | https://hustle-coach-ed4bc48a.renu-01.cranecloud.io |
| Image | `landwind/hustle-coach:latest` |
| Size | ~5.7 GB |
| Port | 8080 (nginx → backend:8081 + frontend:3000) |
| Cluster | RENU (`9e81a70e-8460-4e5d-b0a8-17abcac30f68`) |
| GitHub | https://github.com/mpairwe7/hustle-coach |

## Environment Variables

| Key | Value | Description |
|-----|-------|-------------|
| `GROQ_API_KEY` | `gsk_...` (secret) | Groq free tier API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model |
| `LLM_BACKEND` | `groq` | LLM provider |
| `PORT` | `8081` | Backend port (internal) |
| `LOG_LEVEL` | `info` | Logging level |

## Retrieval

HustleCoach already loads BM25 before Qdrant and has smart KB path resolution (`Path("knowledge-base")` → `Path(__file__).parents[2]` → `/app/knowledge-base`). Pre-built index: 162 docs, 4188 terms from business models, market prices, funding sources.

## Build & Deploy

```bash
docker build -t landwind/hustle-coach:latest -f Dockerfile.cranecloud .
docker push landwind/hustle-coach:latest
```

## Verified Endpoints

| Endpoint | Status | Response |
|----------|--------|----------|
| `/health` | 200 | `{"status":"ok","service":"hustle-scale","retriever":true,"market_intel":true}` |
| `/v1/chat` | 200 | Groq LLM coaching response |
| `/` | 200 | Frontend UI |
| `/docs` | 200 | Swagger API docs |

## Voice Streaming (Added 2026-05-12)

WebSocket endpoint `/v1/voice/chat/stream` added for real-time voice conversations.

| Feature | Status |
|---------|--------|
| Energy-based VAD | Enabled |
| Sentence-chunked TTS | Enabled |
| Barge-in | Enabled |
| Sunbird STT/TTS | Requires `SUNBIRD_API_TOKEN` |
| Multilingual (lg/nyn/sw) | Via Sunbird MT |

See `docs/voice-system.md` for full protocol documentation.

### Updated Production URL

```
https://hustle-coach-6774ea00.renu-01.cranecloud.io
```
