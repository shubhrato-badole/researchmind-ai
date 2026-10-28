import threading
import logging

logger = logging.getLogger(__name__)

from langchain.tools import tool


def get_tools(user_id: int):
    search_call_state = {"count": 0}
    search_call_lock = threading.Lock()

    @tool
    def search_documents(query: str) -> str:
        """Search the user's private knowledge base.
        Use this first for any question."""
        with search_call_lock:
            if search_call_state["count"] >= 2:
                print("[RAG] Document search blocked: two-call limit reached.")
                return (
                    "FALLBACK_LIMIT_REACHED: Two document-search calls have already been used. "
                    "Use available evidence or explain what could not be verified."
                )
            search_call_state["count"] += 1
            call_number = search_call_state["count"]
        print(f"[RAG] Document search call {call_number}/2 started.")
        call_marker = f"[DOCUMENT_SEARCH_CALL: {call_number}/2]\n"
        from retrieval.hybrid_search import hybrid_search
        from features.trust_score import get_trust_score
        from retrieval.reranker import rerank

        for attempt in range(3):
            try:
                results = hybrid_search(query, user_id)

                if results:
                    results = rerank(query, results)

                    for r in results:
                        r["trust_score"] = get_trust_score(
                            r.get("metadata", {})
                        )

                    contradiction = None
                    if len(results) >= 2:
                        from features.contradiction import detect_contradictions
                        contradiction = detect_contradictions(query, results)

                    response = ""

                    for r in results:
                        metadata = r.get("metadata", {})
                        source = metadata.get("filename", "unknown")
                        source_type = metadata.get("source_type", "")
                        trust = r["trust_score"]

                        response += (
                            f"\n[{source_type}: {source} | trust: {trust}/100]\n"
                            f"{r['content']}\n"
                        )

                    if contradiction:
                        response += (
                            "\n\n⚠ NUMERIC CONFLICT CANDIDATE — NOT CONFIRMED\n"
                            "A quick rule-based check found different numbers in "
                            "similar contexts. Verify the full evidence before "
                            "calling this a contradiction.\n"
                            f"Source A: {contradiction.get('source_a', 'unknown')}\n"
                            f"Evidence A: {contradiction.get('evidence_a', '')}\n"
                            f"Source B: {contradiction.get('source_b', 'unknown')}\n"
                            f"Evidence B: {contradiction.get('evidence_b', '')}\n"
                            f"Reason: {contradiction.get('message', 'Possible numeric discrepancy')}"
                        )

                    return call_marker + response

            except Exception as e:
                print(f"Search error: {e}")
                continue

        return f"{call_marker}NO_RESULTS"


    @tool
    def search_documents_multi_query(
        query: str,
        alternate_queries: list[str],
    ) -> str:
        """Search documents using the original question and up to three
        alternative query formulations. Use only after search_documents
        returns insufficient evidence. Provide alternative queries directly;
        do not generate them using another LLM call."""

        with search_call_lock:
            if search_call_state["count"] >= 2:
                return (
                    "FALLBACK_LIMIT_REACHED: Two document-search calls "
                    "have already been used. Use the available evidence "
                    "or explain what could not be verified."
                )

            search_call_state["count"] += 1
            call_number = search_call_state["count"]

        print(
            f"[RAG] Multi-query fallback {call_number}/2 started."
        )
        call_marker = f"[DOCUMENT_SEARCH_CALL: {call_number}/2]\n"

        try:
            from retrieval.multi_query import multi_query_search
            from features.trust_score import get_trust_score

            results = multi_query_search(
                query=query,
                user_id=user_id,
                alternate_queries=alternate_queries[:3],
            )

            if not results:
                return call_marker + "NO_RESULTS"

            response = ""

            for result in results:
                metadata = result.get("metadata") or {}
                trust = get_trust_score(metadata)
                source = metadata.get("filename", "unknown")
                source_type = metadata.get("source_type", "")

                response += (
                    f"\n[{source_type}: {source} | trust: {trust}/100]\n"
                    f"{result['content']}\n"
                )

            return call_marker + response

        except Exception:
            logger.exception("Multi-query fallback failed")
            return call_marker + "NO_RESULTS"

    @tool
    def search_internet(query: str) -> str:
        """Search the web for current or missing information.
        Use only if documents don't have the answer."""
        from agent.web_search import search_web
        from limit.rate_limiter import check_daily_limit

        allowed, remaining, limit = check_daily_limit(
            user_id, "web_search"
        )

        if not allowed:
            return (
                f"WEB_SEARCH_LIMIT_REACHED: Daily web search limit "
                f"reached ({limit}/day). Upgrade to Pro for unlimited."
            )

        for attempt in range(3):
            try:
                results = search_web(query)

                if results:
                    response = ""

                    for r in results:
                        metadata = r.get("metadata", {})
                        url = metadata.get("source_url", "")
                        response += f"\n[web: {url}]\n{r['content']}\n"

                    return response

            except Exception as e:
                print(f"Web search error: {e}")
                continue

        return "NO_RESULTS"


    return [
    search_documents,
    search_documents_multi_query,
    search_internet,
]