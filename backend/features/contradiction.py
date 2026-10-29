import re


NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")
WORD_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
CONTEXT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "in", "is", "it", "of", "on", "or", "the", "to",
    "was", "were", "with",
}


def local_contradiction_check(chunks: list):
    """Find a possible numeric conflict; this heuristic does not confirm it."""
    if len(chunks) < 2:
        return None

    source_numbers = {}

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        metadata = chunk.get("metadata") or {}
        source = str(
            metadata.get("filename")
            or metadata.get("source_url")
            or "unknown"
        )
        content = str(chunk.get("content") or "")
        words = content.split()

        for i, word in enumerate(words):
            for number in NUMBER_PATTERN.findall(word):
                start = max(0, i - 3)
                end = min(len(words), i + 4)
                context = " ".join(words[start:end])
                terms = set(WORD_PATTERN.findall(context.lower()))
                terms -= CONTEXT_STOPWORDS
                terms -= set(NUMBER_PATTERN.findall(context))

                source_numbers.setdefault(source, []).append({
                    "number": number,
                    "context": context,
                    "terms": terms,
                })

    sources = list(source_numbers)

    for i, source_a in enumerate(sources):
        for source_b in sources[i + 1:]:
            for item_a in source_numbers[source_a]:
                for item_b in source_numbers[source_b]:
                    shared_terms = item_a["terms"] & item_b["terms"]

                    if (
                        item_a["number"] != item_b["number"]
                        and len(shared_terms) >= 2
                    ):
                        return {
                            "type": "number_conflict",
                            "status": "candidate",
                            "source_a": source_a,
                            "source_b": source_b,
                            "evidence_a": item_a["context"],
                            "evidence_b": item_b["context"],
                            "message": (
                                f"{source_a} mentions {item_a['number']}; "
                                f"{source_b} mentions {item_b['number']} "
                                "in text with overlapping context. "
                                "This is a candidate, not a confirmed contradiction."
                            ),
                        }

    return None


def detect_contradictions(query: str, chunks: list):
    """Return a cheap numeric-conflict candidate for the final answer model to verify.

    Semantic comparison is performed during normal answer generation, not by
    making an additional LLM call here.
    """
    if len(chunks) < 2:
        return None

    return local_contradiction_check(chunks)
