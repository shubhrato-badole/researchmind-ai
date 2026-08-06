from langchain.tools import tool


def get_tools(user_id: int):

    @tool
    def search_documents(query: str) -> str:
        """Search the user's private knowledge base.
        Use this first for any question."""
        from retrieval.multi_query import multi_query_search
        from features.trust_score import get_trust_score

        for attempt in range(3):
            try:
                results = multi_query_search(query, user_id)
                if results:
                    for r in results:
                        r["trust_score"] = get_trust_score(r.get("metadata", {}))

                    contradiction = None
                    if len(results) >= 2:
                        from features.contradiction import detect_contradictions
                        contradiction = detect_contradictions(query, results)

                    response = ""
                    for r in results:
                        source = r["metadata"].get("filename", "unknown")
                        source_type = r["metadata"].get("source_type", "")
                        trust = r["trust_score"]
                        response += f"\n[{source_type}: {source} | trust: {trust}/100]\n{r['content']}\n"

                    if contradiction:
                        response += f"\n\n⚠ NOTE: Potential contradiction — {contradiction['message']}"

                    return response

            except Exception as e:
                print(f"Search error: {e}")
                continue

        return "NO_RESULTS"

    @tool
    def search_internet(query: str) -> str:
        """Search the web for current or missing information.
        Use only if documents don't have the answer."""
        from agent.web_search import search_web
        from limit.rate_limiter import check_daily_limit

        allowed, remaining, limit = check_daily_limit(user_id, "web_search")
        if not allowed:
            return f"WEB_SEARCH_LIMIT_REACHED: Daily web search limit reached ({limit}/day). Upgrade to Pro for unlimited."

        for attempt in range(3):
            try:
                results = search_web(query)
                if results:
                    response = ""
                    for r in results:
                        url = r["metadata"].get("source_url", "")
                        response += f"\n[web: {url}]\n{r['content']}\n"
                    return response
            except Exception:
                continue

        return "NO_RESULTS"

    return [search_documents, search_internet]