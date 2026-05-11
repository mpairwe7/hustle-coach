# Contributing to HustleScale

## Prerequisites

- **Python 3.11+** with [uv](https://docs.astral.sh/uv/) (never use pip directly)
- **Bun** (latest) for frontend (never use npm)
- **Docker** and **Docker Compose** (optional, for full-stack setup)
- **Qdrant** vector database (local or Docker)

## Setup

```bash
# Clone and enter the project
git clone https://github.com/mpairwe7/FinalYearProject.git
cd FinalYearProject/HustleCoach

# Copy environment config
cp .env.example .env
# Edit .env with your API keys (Groq is free — no credit card needed)

# Backend
cd backend
uv sync            # installs dependencies from pyproject.toml / requirements.txt
uv run python -m pytest tests/ -q   # verify tests pass

# Frontend
cd ../frontend
bun install
bun run dev        # starts on port 3440
```

## Development Servers

| Service  | Port  | Command              |
|----------|-------|----------------------|
| Frontend | 3440  | `bun run dev`        |
| Backend  | 8808  | `uv run uvicorn app.main:app --port 8808 --reload` |
| Qdrant   | 6333  | Docker or local      |

## Running Tests

```bash
# Backend (from HustleCoach/backend)
uv run python -m pytest tests/ -q --tb=short

# Frontend type-check (from HustleCoach/frontend)
bunx tsc --noEmit
```

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `chore:` — maintenance, CI, dependencies
- `refactor:` — code change that neither fixes a bug nor adds a feature
- `test:` — adding or updating tests

Examples:
```
feat(dashboard): add business health score ring
fix(chat): handle empty LLM response gracefully
chore(ci): add frontend build step to workflow
```

## Pull Request Guidelines

1. Branch from `dev` (never push directly to `main` or `dev`).
2. Keep PRs focused — one feature or fix per PR.
3. Ensure all tests pass and `tsc --noEmit` reports no errors.
4. Write a clear PR description with a summary and test plan.
5. Request review from at least one maintainer.

## Code Style

- **Python**: Type hints required. Formatted with Ruff (`line-length = 120`).
- **TypeScript**: Strict mode. Formatted with Prettier via editor config.
- **Package managers**: `bun` for JS/TS, `uv` for Python. Never use `npm` or `pip`.
