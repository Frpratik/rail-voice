from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence

import numpy as np
from openai import AsyncOpenAI

from app.core.config import settings

# Normalize synonymous terms for local dev embeddings
SYNONYM_GROUPS = [
    {"dustbin", "dustbins", "garbage", "bin", "bins", "waste", "trash", "rubbish"},
    {"bridge", "fob", "footover", "foot", "overbridge"},
    {"platform", "pf"},
    {"lift", "elevator", "escalator"},
    {"broken", "not working", "damaged", "faulty"},
    {"missing", "absent", "no", "not there"},
]


def _normalize_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    normalized: list[str] = []
    for token in tokens:
        normalized.append(token)
        for group in SYNONYM_GROUPS:
            if token in group:
                normalized.append("syn:" + "_".join(sorted(group)))
                break
    # Add word bigrams for local semantic overlap
    for i in range(len(tokens) - 1):
        normalized.append(f"{tokens[i]}_{tokens[i+1]}")
    return normalized


class EmbeddingService:
    """Generate text embeddings via OpenAI or deterministic local fallback."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        if settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def uses_openai(self) -> bool:
        return self._client is not None

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        cleaned = [t.strip() for t in texts if t and t.strip()]
        if not cleaned:
            raise ValueError("No text provided for embedding")

        if self._client:
            response = await self._client.embeddings.create(
                model=settings.embedding_model,
                input=list(cleaned),
            )
            return [item.embedding for item in response.data]

        return [self._local_embedding(text) for text in cleaned]

    def _local_embedding(self, text: str) -> list[float]:
        """Deterministic embedding for dev/test — synonym-aware token hashing."""
        dim = settings.embedding_dimensions
        tokens = _normalize_tokens(text)
        vector = np.zeros(dim, dtype=np.float32)
        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            weight = 1.0 / math.sqrt(max(len(tokens), 1))
            for i, byte in enumerate(digest):
                vector[i % dim] += ((byte / 255.0) - 0.5) * weight
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    @staticmethod
    def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        denom = np.linalg.norm(va) * np.linalg.norm(vb)
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)

    @staticmethod
    def to_list(value: Sequence[float] | None) -> list[float]:
        if value is None:
            return []
        return [float(x) for x in value]


embedding_service = EmbeddingService()
