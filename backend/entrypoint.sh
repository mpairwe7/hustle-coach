#!/bin/bash
set -e

# Auto-index knowledge base if BM25 state doesn't exist
BM25_PATH="${BM25_STATE_PATH:-/app/knowledge-base/bm25_state.json}"
if [ ! -f "$BM25_PATH" ]; then
    echo "First run: indexing knowledge base..."
    python -m app.indexer || echo "Warning: indexing failed (Qdrant may not be ready). Keyword fallback will be used."
fi

# Start the API server
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${WORKERS:-2}"
