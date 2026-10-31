import logging

from retrieval.hybrid_search import hybrid_search
from retrieval.reranker import rerank

logger = logging.getLogger(__name__)


def multi_query_search(
    query: str,
    user_id: int,
    alternate_queries: list[str] | None = None,
) -> list[dict]:
    """Search with the original question and up to three alternatives."""

    original_query = query.strip()
    if not original_query:
        return []

    # Always search the original question first.
    queries = [original_query]
    seen_queries = {" ".join(original_query.casefold().split())}

    # The agent supplies alternatives; this function makes no LLM calls.
    for alternative in (alternate_queries or [])[:3]:
        if not isinstance(alternative, str) or not alternative.strip():
            continue

        cleaned = " ".join(alternative.split())
        normalized = cleaned.casefold()

        if normalized not in seen_queries:
            queries.append(cleaned)
            seen_queries.add(normalized)

    all_chunks = {}

    for search_query in queries:
        try:
            results = hybrid_search(search_query, user_id) or []
        except Exception:
            logger.exception(
                "Multi-query search failed for query: %s",
                search_query,
            )
            continue

        for chunk in results:
            if not isinstance(chunk, dict) or not chunk.get("content"):
                continue

            metadata = chunk.get("metadata") or {}
            metadata_key = tuple(
                sorted(
                    (str(key), repr(value))
                    for key, value in metadata.items()
                )
            ) if isinstance(metadata, dict) else repr(metadata)

            # Deduplicate chunks without merging different source records.
            chunk_key = (chunk["content"], metadata_key)

            if chunk_key not in all_chunks:
                all_chunks[chunk_key] = chunk

    if not all_chunks:
        return []

    return rerank(original_query, list(all_chunks.values()))