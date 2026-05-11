"""Knowledge base indexer for HustleScale.

Reads JSON files from knowledge-base/ directory and indexes them
into Qdrant with dense (BAAI/bge-m3) and sparse (BM25) vectors.

Usage:
    python -m app.indexer
    # Or: docker compose exec api python -m app.indexer
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "hustle_coach_kb")
DENSE_MODEL = os.getenv("DENSE_MODEL", "BAAI/bge-m3")
DENSE_DIM = int(os.getenv("DENSE_DIM", "1024"))
BM25_STATE_PATH = os.getenv("BM25_STATE_PATH", "knowledge-base/bm25_state.json")
KB_DIR = os.getenv("KB_DIR", "knowledge-base")


def load_documents() -> list[dict]:
    """Load all JSON documents from knowledge base."""
    kb_path = Path(KB_DIR)
    if not kb_path.exists():
        kb_path = Path("/app/knowledge-base")

    docs = []
    for json_file in sorted(kb_path.rglob("*.json")):
        if json_file.name == "bm25_state.json":
            continue
        try:
            with open(json_file) as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("text"):
                        item.setdefault("source", json_file.stem)
                        docs.append(item)
            elif isinstance(data, dict):
                # Handle market prices format
                if "prices" in data:
                    for price in data["prices"]:
                        doc = {
                            "text": f"{price['item']}: UGX {price['price_ugx']:,}/{price['unit']} ({price.get('category', '')})",
                            "source": "market-prices",
                            "domain": "market_prices",
                            "topic": price.get("category", ""),
                            "section": "Market Price",
                        }
                        docs.append(doc)
                else:
                    for key, items in data.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and item.get("text"):
                                    item.setdefault("source", f"{json_file.stem}/{key}")
                                    docs.append(item)

            logger.info("Loaded %s: %d entries", json_file.name, len(docs))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", json_file, e)

    return docs


def index():
    """Main indexing pipeline."""
    docs = load_documents()
    if not docs:
        logger.error("No documents found in %s", KB_DIR)
        sys.exit(1)

    logger.info("Total documents to index: %d", len(docs))

    # Load embedding model
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(DENSE_MODEL)
        logger.info("Loaded dense model: %s", DENSE_MODEL)
    except Exception as e:
        logger.error("Failed to load embedding model: %s", e)
        sys.exit(1)

    # Fit BM25
    from .retriever import BM25SparseEncoder
    bm25 = BM25SparseEncoder()
    texts = [d["text"] for d in docs]
    bm25.fit(texts)
    bm25.save(BM25_STATE_PATH)
    logger.info("BM25 fitted on %d docs, saved to %s", len(texts), BM25_STATE_PATH)

    # Encode dense vectors
    logger.info("Encoding %d documents with %s...", len(docs), DENSE_MODEL)
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    logger.info("Encoded %d vectors of dim %d", len(embeddings), embeddings.shape[1])

    # Connect to Qdrant
    try:
        from qdrant_client import QdrantClient, models
        client = QdrantClient(url=QDRANT_URL, timeout=30)

        # Recreate collection
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config={
                "dense": models.VectorParams(
                    size=DENSE_DIM,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(),
            },
        )
        logger.info("Created collection: %s", QDRANT_COLLECTION)

        # Upload in batches
        batch_size = 100
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            points = []
            for j, (doc, emb) in enumerate(zip(batch_docs, batch_embeddings)):
                # Sparse vector
                sparse_idx, sparse_val = bm25.encode(doc["text"])

                point = models.PointStruct(
                    id=i + j,
                    vector={
                        "dense": emb.tolist(),
                        "sparse": models.SparseVector(
                            indices=sparse_idx,
                            values=sparse_val,
                        ),
                    },
                    payload={
                        "text": doc["text"],
                        "source": doc.get("source", ""),
                        "domain": doc.get("domain", ""),
                        "topic": doc.get("topic", ""),
                        "section": doc.get("section", ""),
                    },
                )
                points.append(point)

            client.upsert(
                collection_name=QDRANT_COLLECTION,
                points=points,
            )
            logger.info("Uploaded batch %d-%d", i, i + len(batch_docs))

        # Verify
        info = client.get_collection(QDRANT_COLLECTION)
        logger.info(
            "Indexing complete! Collection '%s': %d points",
            QDRANT_COLLECTION,
            info.points_count,
        )

    except Exception as e:
        logger.error("Qdrant indexing failed: %s", e)
        logger.info("BM25 state saved — keyword fallback will still work")
        sys.exit(1)


if __name__ == "__main__":
    index()
