import os
from functools import lru_cache

from sentence_transformers import CrossEncoder
from config import TOP_K_RERANK


RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "BAAI/bge-reranker-base",
)

RERANKER_MODE = os.getenv(
    "RERANKER_MODE",
    "off",
).strip().lower()

if RERANKER_MODE not in {"off", "on"}:
    raise ValueError("RERANKER_MODE must be 'off' or 'on'")


@lru_cache(maxsize=2)
def get_model(model_name: str = RERANKER_MODEL):
    """Load and cache the selected reranker."""
    return CrossEncoder(model_name)


def rerank(
    query: str,
    chunks: list,
    *,
    force: bool = False,
    model_name: str | None = None,
):
    """Optionally rerank candidates; otherwise preserve hybrid ranking."""
    if not chunks:
        return []

    # Fast path: no CrossEncoder inference.
    if not force and RERANKER_MODE == "off":
        return chunks[:TOP_K_RERANK]

    pairs = [
        [query, str(chunk.get("content") or "")]
        for chunk in chunks
    ]

    model = get_model(model_name or RERANKER_MODEL)
    scores = model.predict(pairs)

    ranked = sorted(
        zip(chunks, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [
        {
            **chunk,
            "metadata": chunk.get("metadata") or {},
            "score": float(score),
        }
        for chunk, score in ranked[:TOP_K_RERANK]
    ]