"""Hybrid retrieval using BM25 keyword search and vector search with RRF fusion."""

import re
import time
from threading import RLock
from typing import Any

from rank_bm25 import BM25Okapi

from config import TOP_K_RETRIEVAL
from database.chromadb import get_collection
from retrieval.vector_search import vector_search

STOPWORDS = {
    "is", "are", "the", "a", "an", "to", "of", "and", "in", "it", "that",
    "this", "was", "for", "on", "with", "as", "be", "at", "by", "we", "or",
    "but", "what", "how", "why", "when", "where", "who", "which", "do", "does",
    "did", "will", "can", "should", "would",
}
RRF_K = 60
BM25_CACHE_TTL_SECONDS = 60

# Keep the public cache object shape unchanged for existing callers/tests.
# Metadata stores (shared Redis corpus version, monotonic build time) separately.
bm25_cache: dict[int, tuple[Any, list[str], list[dict], list[list[str]]]] = {}
_cache_metadata: dict[int, tuple[str | None, float]] = {}
_cache_lock = RLock()
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def clean_text(text: str) -> list[str]:
    """Normalize punctuation/case consistently for corpus and queries."""
    tokens = _TOKEN_PATTERN.findall((text or "").lower())
    return [token for token in tokens if token not in STOPWORDS]


def _version_key(user_id: int) -> str:
    return f"researchmind:bm25:version:{int(user_id)}"


def _read_shared_version(user_id: int) -> str | None:
    """Read a cross-process invalidation token; TTL remains the fallback."""
    try:
        from database.redis_client import get_redis

        value = get_redis().get(_version_key(user_id))
        return str(value) if value is not None else "0"
    except Exception as exc:
        # Redis may be temporarily unavailable; the TTL below bounds staleness.
        print(f"WARNING: Could not read BM25 cache version for user {user_id}: {exc}", flush=True)
        return None


def get_bm25_index(user_id: int):
    """Return the user's cached BM25 index and aligned source records."""
    user_key = int(user_id)
    now = time.monotonic()

    with _cache_lock:
        current_version = _read_shared_version(user_key)
        cached = bm25_cache.get(user_key)
        metadata = _cache_metadata.get(user_key)
        if cached is not None and metadata is not None:
            cached_version, built_at = metadata
            fresh = now - built_at < BM25_CACHE_TTL_SECONDS
            version_matches = current_version is None or cached_version == current_version
            if fresh and version_matches:
                return cached
            bm25_cache.pop(user_key, None)
            _cache_metadata.pop(user_key, None)

        # Detect invalidation during the Chroma read. Usually one pass is enough;
        # a second pass reduces the chance of caching a corpus snapshot that raced
        # with an upload or deletion.
        docs: list[str] = []
        metadatas: list[dict] = []
        version_before = current_version
        version_after = current_version
        for attempt in range(2):
            version_before = _read_shared_version(user_key)
            collection = get_collection(str(user_key))
            all_docs = collection.get(include=["documents", "metadatas"])
            docs = list(all_docs.get("documents") or [])
            raw_metadatas = list(all_docs.get("metadatas") or [])
            metadatas = [
                (raw_metadatas[i] if i < len(raw_metadatas) else None) or {}
                for i in range(len(docs))
            ]
            version_after = _read_shared_version(user_key)
            if version_before == version_after:
                break
            if attempt == 0:
                continue

        if not docs:
            return None, [], [], []

        tokenized_docs = [clean_text(doc) for doc in docs]
        index = BM25Okapi(tokenized_docs) if any(tokenized_docs) else None
        cached_value = (index, docs, metadatas, tokenized_docs)

        bm25_cache[user_key] = cached_value
        # If Redis was unavailable, the TTL alone bounds the cache lifetime.
        # If versions kept changing during both reads, don't treat the entry as
        # valid for long; the next query will rebuild it.
        built_at = time.monotonic()
        if version_before != version_after:
            built_at -= BM25_CACHE_TTL_SECONDS
        _cache_metadata[user_key] = (version_after, built_at)
        return cached_value


def invalidate_cache(user_id: int) -> None:
    """Invalidate local cache and advance a version shared by API workers."""
    user_key = int(user_id)
    with _cache_lock:
        bm25_cache.pop(user_key, None)
        _cache_metadata.pop(user_key, None)

    # Local cache is already cleared even if Redis fails. Raising lets the durable
    # cleanup worker retry and the one-minute local TTL limits cross-process staleness.
    from database.redis_client import get_redis

    get_redis().incr(_version_key(user_key))


def bm25_search(query: str, user_id: int) -> list[dict]:
    """Return top keyword matches, including matches with negative IDF scores."""
    query_tokens = clean_text(query)
    if not query_tokens:
        return []

    index, docs, metadatas, tokenized_docs = get_bm25_index(user_id)
    if index is None:
        return []

    scores = index.get_scores(query_tokens)
    query_token_set = set(query_tokens)
    scored: list[dict] = []
    for i, score in enumerate(scores):
        if i >= len(tokenized_docs) or query_token_set.isdisjoint(tokenized_docs[i]):
            continue
        scored.append({"content": docs[i], "metadata": metadatas[i], "score": float(score)})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:TOP_K_RETRIEVAL]


def _chunk_key(chunk: dict) -> tuple:
    """Identify the same chunk across retrievers without merging source copies."""
    content = str(chunk.get("content") or "")
    metadata = chunk.get("metadata") or {}
    metadata_key = tuple(sorted((str(key), repr(value)) for key, value in metadata.items()))
    return content, metadata_key


def hybrid_search(query: str, user_id: int) -> list[dict]:
    """Fuse vector and BM25 rankings with Reciprocal Rank Fusion (RRF)."""
    vector_results = vector_search(query, user_id) or []
    bm25_results = bm25_search(query, user_id) or []
    if not vector_results and not bm25_results:
        return []

    fused: dict[tuple, dict] = {}
    first_seen_order = 0
    for results in (vector_results, bm25_results):
        for rank, chunk in enumerate(results, start=1):
            if not isinstance(chunk, dict) or not chunk.get("content"):
                continue
            key = _chunk_key(chunk)
            if key not in fused:
                fused[key] = {
                    "content": chunk["content"],
                    "metadata": chunk.get("metadata") or {},
                    "score": 0.0,
                    "_first_seen": first_seen_order,
                }
                first_seen_order += 1
            fused[key]["score"] += 1.0 / (RRF_K + rank)

    ordered = sorted(fused.values(), key=lambda item: (-item["score"], item["_first_seen"]))
    return [
        {"content": item["content"], "metadata": item["metadata"], "score": float(item["score"])}
        for item in ordered[:TOP_K_RETRIEVAL]
    ]
