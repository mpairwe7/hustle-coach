"""Semantic cache for HustleScale — avoids redundant LLM calls.

Forked from URA Chatbot. Embeds queries and finds cached responses
when cosine similarity exceeds threshold.
"""

from __future__ import annotations

import logging
import os
import time
import threading
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_THRESHOLD = float(os.getenv("CACHE_THRESHOLD", "0.92"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
CACHE_MAX_SIZE = 1000


@dataclass
class CacheEntry:
    query: str
    embedding: np.ndarray
    response: dict
    created_at: float = field(default_factory=time.time)
    hits: int = 0


class SemanticCache:
    """Thread-safe in-memory semantic cache."""

    def __init__(self, dense_model=None):
        self._entries: list[CacheEntry] = []
        self._lock = threading.Lock()
        self._model = dense_model

    def set_model(self, model):
        self._model = model

    def lookup(self, query: str) -> dict | None:
        """Find cached response for semantically similar query."""
        if not CACHE_ENABLED or not self._model or not self._entries:
            return None

        query_emb = self._model.encode(query)
        now = time.time()

        with self._lock:
            best_score = 0.0
            best_entry = None

            for entry in self._entries:
                if now - entry.created_at > CACHE_TTL:
                    continue
                sim = float(np.dot(query_emb, entry.embedding) / (
                    np.linalg.norm(query_emb) * np.linalg.norm(entry.embedding) + 1e-8
                ))
                if sim > best_score:
                    best_score = sim
                    best_entry = entry

            if best_entry and best_score >= CACHE_THRESHOLD:
                best_entry.hits += 1
                logger.info("Cache HIT (sim=%.4f): %s", best_score, query[:60])
                return best_entry.response

        return None

    def store(self, query: str, response: dict):
        """Cache a query-response pair."""
        if not CACHE_ENABLED or not self._model:
            return

        embedding = self._model.encode(query)

        with self._lock:
            # Evict expired and excess entries
            now = time.time()
            self._entries = [
                e for e in self._entries if now - e.created_at <= CACHE_TTL
            ]
            if len(self._entries) >= CACHE_MAX_SIZE:
                # LRU: remove least-hit entries
                self._entries.sort(key=lambda e: e.hits)
                self._entries = self._entries[len(self._entries) // 4:]

            self._entries.append(CacheEntry(
                query=query,
                embedding=embedding,
                response=response,
            ))

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._entries),
                "total_hits": sum(e.hits for e in self._entries),
            }
