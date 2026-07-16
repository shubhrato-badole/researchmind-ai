from sentence_transformers import CrossEncoder
from config import TOP_K_RERANK
from functools import lru_cache


@lru_cache(maxsize=1)
def get_model():
    return CrossEncoder("BAAI/bge-reranker-base")

def rerank(query: str, chunks: list):
    if not chunks:
        return []

    pairs = [[query, chunk["content"]] for chunk in chunks]
    scores = get_model().predict(pairs)

    scored = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True
    )

    result = []
    for chunk, score in scored[:TOP_K_RERANK]:
        result.append({
            "content": chunk["content"],
            "metadata": chunk["metadata"],
            "score": float(score)
        })

    return result