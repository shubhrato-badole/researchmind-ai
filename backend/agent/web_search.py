from duckduckgo_search import DDGS

def search_web(query: str):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return []

        return [
            {
                "content": r["body"],
                "metadata": {
                    "source_type": "web",
                    "source_url": r["href"],
                    "filename": r["title"]
                }
            }
            for r in results
        ]
    except Exception as e:
        return []