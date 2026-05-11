#!/usr/bin/env bash
# Hustle Coach — Reindex knowledge base into Qdrant
# Usage: ./scripts/reindex.sh
# Or:    docker compose exec api python -m app.indexer

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Hustle Coach Knowledge Base Indexer ==="
echo "Project: $PROJECT_DIR"

# Check if running inside Docker or locally
if command -v docker &>/dev/null && docker compose ps api 2>/dev/null | grep -q "running"; then
    echo "Running inside Docker..."
    docker compose exec api python -m app.indexer
else
    echo "Running locally..."
    cd "$PROJECT_DIR/backend"

    # Check Python
    if ! command -v python3 &>/dev/null; then
        echo "Error: Python 3 not found"
        exit 1
    fi

    # Check Qdrant
    QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
    if ! curl -sf "$QDRANT_URL/healthz" >/dev/null 2>&1; then
        echo "Warning: Qdrant not reachable at $QDRANT_URL"
        echo "Start Qdrant first: docker compose up qdrant -d"
        exit 1
    fi

    export PYTHONPATH="$PROJECT_DIR/backend:$PYTHONPATH"
    python3 -m app.indexer
fi

echo "=== Indexing complete ==="
