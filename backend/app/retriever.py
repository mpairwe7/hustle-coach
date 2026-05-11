"""Hybrid retriever for HustleScale knowledge base.

Forked from Magezi. Combines:
1. Dense retrieval (BAAI/bge-m3, 1024d, multilingual)
2. Sparse retrieval (BM25 with IDF weights)
3. Reciprocal Rank Fusion via Qdrant
4. Cross-encoder reranking (mxbai-rerank-base-v2)
5. Keyword fallback when Qdrant unavailable
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Configuration ───

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "hustle_coach_kb")
DENSE_MODEL = os.getenv("DENSE_MODEL", "BAAI/bge-m3")
DENSE_DIM = int(os.getenv("DENSE_DIM", "1024"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "mixedbread-ai/mxbai-rerank-base-v2")
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() == "true"
BM25_STATE_PATH = os.getenv("BM25_STATE_PATH", "knowledge-base/bm25_state.json")


# ─── Circuit Breaker ───

class CircuitBreaker:
    """Simple circuit breaker for external services."""

    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 10.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._failures = 0
        self._last_failure: float = 0.0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    @property
    def is_open(self) -> bool:
        if self._state == "OPEN":
            if time.time() - self._last_failure > self.reset_timeout:
                self._state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self._failures = 0
        self._state = "CLOSED"

    def record_failure(self):
        self._failures += 1
        self._last_failure = time.time()
        if self._failures >= self.failure_threshold:
            self._state = "OPEN"
            logger.warning("Circuit breaker OPEN after %d failures", self._failures)


# ─── BM25 Sparse Encoder ───

class BM25SparseEncoder:
    """BM25-weighted sparse vector encoder."""

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.avg_dl: float = 0.0
        self.n_docs: int = 0

    def fit(self, documents: list[str]):
        """Compute IDF from document corpus."""
        self.n_docs = len(documents)
        df: Counter = Counter()
        total_len = 0
        vocab_set: set[str] = set()

        for doc in documents:
            tokens = set(re.findall(r"\w+", doc.lower()))
            vocab_set.update(tokens)
            df.update(tokens)
            total_len += len(tokens)

        self.avg_dl = total_len / max(self.n_docs, 1)
        self.vocab = {t: i for i, t in enumerate(sorted(vocab_set))}
        self.idf = {
            t: math.log((self.n_docs - freq + 0.5) / (freq + 0.5) + 1)
            for t, freq in df.items()
        }

    def encode(self, text: str) -> tuple[list[int], list[float]]:
        """Encode query to sparse vector (indices, values)."""
        tokens = re.findall(r"\w+", text.lower())
        tf: Counter = Counter(tokens)
        dl = len(tokens)

        indices = []
        values = []
        for token, freq in tf.items():
            if token not in self.vocab:
                continue
            idf = self.idf.get(token, 0.0)
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * dl / max(self.avg_dl, 1))
            score = idf * numerator / denominator
            if score > 0:
                indices.append(self.vocab[token])
                values.append(round(score, 4))

        return indices, values

    def save(self, path: str):
        state = {
            "vocab": self.vocab,
            "idf": self.idf,
            "avg_dl": self.avg_dl,
            "n_docs": self.n_docs,
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(state, f)

    def load(self, path: str) -> bool:
        try:
            with open(path) as f:
                state = json.load(f)
            self.vocab = state["vocab"]
            self.idf = state["idf"]
            self.avg_dl = state["avg_dl"]
            self.n_docs = state["n_docs"]
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return False


# ─── Hybrid Retriever ───

class HybridRetriever:
    """Dense + Sparse hybrid retriever with Qdrant backend."""

    def __init__(self):
        self._dense_model = None
        self._reranker = None
        self._sparse_encoder = BM25SparseEncoder()
        self._qdrant_client = None
        self._circuit = CircuitBreaker()
        self._knowledge_base: list[dict] = []  # Fallback data

    def initialize(self):
        """Load models and connect to Qdrant."""
        try:
            from sentence_transformers import SentenceTransformer, CrossEncoder
            self._dense_model = SentenceTransformer(DENSE_MODEL)
            if RERANK_ENABLED:
                self._reranker = CrossEncoder(RERANKER_MODEL)
            logger.info("Dense model loaded: %s", DENSE_MODEL)
        except Exception as e:
            logger.warning("Failed to load embedding models: %s", e)

        # Load BM25 state
        if not self._sparse_encoder.load(BM25_STATE_PATH):
            logger.info("No BM25 state found at %s — will use dense-only", BM25_STATE_PATH)

        # Connect to Qdrant
        try:
            from qdrant_client import QdrantClient
            self._qdrant_client = QdrantClient(url=QDRANT_URL, timeout=10)
            self._qdrant_client.get_collections()
            logger.info("Connected to Qdrant at %s", QDRANT_URL)
        except Exception as e:
            logger.warning("Qdrant unavailable: %s — will use keyword fallback", e)

        # Load knowledge base JSON for fallback
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load JSON knowledge base files for keyword fallback."""
        kb_dir = Path("knowledge-base")
        if not kb_dir.exists():
            # Try relative to this file
            kb_dir = Path(__file__).resolve().parent.parent.parent / "knowledge-base"
        if not kb_dir.exists():
            kb_dir = Path("/app/knowledge-base")

        for json_file in kb_dir.rglob("*.json"):
            if json_file.name == "bm25_state.json":
                continue
            try:
                with open(json_file) as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            item.setdefault("source", json_file.stem)
                            self._knowledge_base.append(item)
                elif isinstance(data, dict):
                    # Handle nested structures
                    for key, items in data.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    item.setdefault("source", f"{json_file.stem}/{key}")
                                    self._knowledge_base.append(item)
            except (json.JSONDecodeError, OSError):
                continue
        logger.info("Loaded %d knowledge base entries for fallback", len(self._knowledge_base))

    def search(
        self,
        query: str,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[dict]:
        """Hybrid search: dense + sparse + RRF + rerank, with keyword fallback."""
        # Try Qdrant first
        if self._qdrant_client and self._dense_model and not self._circuit.is_open:
            try:
                results = self._qdrant_search(query, top_k, domain)
                self._circuit.record_success()
                if results:
                    return results
            except Exception as e:
                logger.warning("Qdrant search failed: %s", e)
                self._circuit.record_failure()

        # Fallback to keyword search
        return self._keyword_search(query, top_k, domain)

    def _qdrant_search(
        self,
        query: str,
        top_k: int,
        domain: str | None,
    ) -> list[dict]:
        """Execute hybrid search against Qdrant."""
        from qdrant_client import models

        dense_vec = self._dense_model.encode(query).tolist()

        # Build prefetch for both dense and sparse
        prefetch = [
            models.Prefetch(query=dense_vec, using="dense", limit=20),
        ]

        # Add sparse if BM25 is fitted
        if self._sparse_encoder.n_docs > 0:
            sparse_idx, sparse_val = self._sparse_encoder.encode(query)
            if sparse_idx:
                prefetch.append(
                    models.Prefetch(
                        query=models.SparseVector(indices=sparse_idx, values=sparse_val),
                        using="sparse",
                        limit=20,
                    )
                )

        # Optional domain filter
        query_filter = None
        if domain:
            query_filter = models.Filter(
                must=[models.FieldCondition(
                    key="domain",
                    match=models.MatchValue(value=domain),
                )]
            )

        results = self._qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=query_filter,
            limit=top_k * 2,
            with_payload=True,
        )

        candidates = []
        for point in results.points:
            payload = point.payload or {}
            candidates.append({
                "text": payload.get("text", ""),
                "source": payload.get("source", ""),
                "domain": payload.get("domain", ""),
                "topic": payload.get("topic", ""),
                "section": payload.get("section", ""),
                "score_rrf": point.score,
            })

        # Rerank
        if self._reranker and candidates:
            pairs = [(query, c["text"]) for c in candidates]
            rerank_scores = self._reranker.predict(pairs)
            for i, score in enumerate(rerank_scores):
                candidates[i]["score_rerank"] = float(score)
            candidates.sort(key=lambda c: c.get("score_rerank", 0), reverse=True)

        return candidates[:top_k]

    def _keyword_search(
        self,
        query: str,
        top_k: int,
        domain: str | None,
    ) -> list[dict]:
        """Simple keyword overlap search on in-memory knowledge base."""
        query_tokens = set(re.findall(r"\w+", query.lower()))

        # Expand multilingual tokens
        bridge = {
            "enkoko": "chicken", "kasooli": "maize", "ssente": "money",
            "bizinensi": "business", "okutunda": "sell", "bbeeyi": "price",
            "kuku": "chicken", "mahindi": "maize", "biashara": "business",
            "soko": "market", "bei": "price",
        }
        expanded = set()
        for t in query_tokens:
            if t in bridge:
                expanded.add(bridge[t])
        query_tokens = query_tokens | expanded

        scored = []
        for item in self._knowledge_base:
            # Check domain filter
            if domain and item.get("domain", "") != domain:
                continue

            text = " ".join(
                str(v) for v in item.values() if isinstance(v, str)
            ).lower()
            item_tokens = set(re.findall(r"\w+", text))
            overlap = len(query_tokens & item_tokens)
            if overlap > 0:
                score = overlap / max(len(query_tokens), 1)
                scored.append({
                    "text": item.get("text", item.get("content", json.dumps(item))),
                    "source": item.get("source", "knowledge-base"),
                    "domain": item.get("domain", ""),
                    "topic": item.get("topic", ""),
                    "section": item.get("section", ""),
                    "score_keyword": score,
                })

        scored.sort(key=lambda x: x.get("score_keyword", 0), reverse=True)
        return scored[:top_k]

    @property
    def is_healthy(self) -> bool:
        if self._qdrant_client and not self._circuit.is_open:
            try:
                self._qdrant_client.get_collections()
                return True
            except Exception:
                return False
        return len(self._knowledge_base) > 0


def compute_faithfulness(answer: str, contexts: list[str]) -> float:
    """Score answer faithfulness as token overlap ratio."""
    if not contexts:
        return 0.0
    answer_tokens = set(re.findall(r"\w+", answer.lower()))
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "have",
        "has", "had", "do", "does", "did", "will", "would", "could", "should",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "and",
        "or", "but", "not", "this", "that", "it", "i", "you", "we", "they",
    }
    answer_tokens -= stopwords
    if not answer_tokens:
        return 1.0
    context_tokens = set()
    for ctx in contexts:
        context_tokens.update(re.findall(r"\w+", ctx.lower()))
    context_tokens -= stopwords
    overlap = answer_tokens & context_tokens
    return len(overlap) / len(answer_tokens)


def build_citations(passages: list[dict]) -> list[dict]:
    """Build citation metadata from retrieved passages."""
    citations = []
    for p in passages:
        citations.append({
            "source": p.get("source", "knowledge-base"),
            "section": p.get("section"),
            "topic": p.get("topic"),
            "preview": (p.get("text", "")[:120] + "...") if p.get("text") else "",
        })
    return citations
