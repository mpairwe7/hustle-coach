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
| Project ID | `5954261f-ec9a-4e7e-9019-d842e6653e64` |

## Environment Variables

| Key | Value | Description |
|-----|-------|-------------|
| `PORT` | `8081` | Backend port (internal) |
| `LOG_LEVEL` | `info` | Logging level |
| `ANTHROPIC_API_KEY` | *(set in Crane Cloud)* | Claude API for coaching |

For multi-provider LLM, add:
- `GROQ_API_KEY` — Groq free tier
- `OPENROUTER_API_KEY` — OpenRouter (optional)

## Build & Deploy

```bash
docker build -t landwind/hustle-coach:latest -f Dockerfile.cranecloud .
docker push landwind/hustle-coach:latest
```

## Architecture

```
nginx:8080
  ├── /health, /v1/* → uvicorn:8081
  ├── /_next/static/ → cached static assets
  └── / → Next.js:3000
```

Knowledge base (27+ business models, market prices, funding sources, regulatory guides) baked into image.

## Verified Endpoints

- `/health` — `{"status": "ok", "service": "hustle-scale", "retriever": true, "market_intel": true}`
- `/` — Frontend UI (HTTP 200)
- `/docs` — Swagger API docs (HTTP 200)
