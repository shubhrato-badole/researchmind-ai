
import logging

from ddgs import DDGS

logger = logging.getLogger(__name__)


def search_web(query: str):
    try:
        with DDGS(timeout=15) as ddgs:
         results = list(
             ddgs.text(
               query,
               region="in-en",
               max_results=5,
               backend="auto",
           )
        )

        logger.info("Web search returned %d results", len(results))
        logger.warning(
              "WEB_SEARCH_QUERY=%r WEB_SEARCH_SOURCES=%s",
               query,
            [
                result.get("href")
                for result in results
                if result.get("body") and result.get("href")
            ],
)
        return [
            {
                "content": result.get("body", ""),
                "metadata": {
                    "source_type": "web",
                    "source_url": result.get("href", ""),
                    "filename": result.get("title", "Unknown"),
                },
            }
            for result in results
            if result.get("body") and result.get("href")
        ]

    except Exception:
        logger.exception("Web search failed")
        return []
