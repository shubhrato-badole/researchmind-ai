from rank_bm25 import BM25Okapi
from retrieval.vector_search import vector_search
from database.chromadb import get_collection
from config import TOP_K_RETRIEVAL

STOPWORDS = {
    "is", "are", "the", "a", "an", "to", "of", "and",
    "in", "it", "that", "this", "was", "for", "on",
    "with", "as", "be", "at", "by", "we", "or", "but",
    "what", "how", "why", "when", "where", "who", "which",
    "do", "does", "did", "will", "can", "should", "would"
}


bm25_cache = {}

def clean_text(text: str):
    words = text.lower().split()
    return [w for w in words if w not in STOPWORDS]

def get_bm25_index(user_id: int):
  
    if user_id in bm25_cache:
        return bm25_cache[user_id]

   
    collection = get_collection(str(user_id))
    all_docs = collection.get()

    if not all_docs["documents"]:
        return None, [], []

    docs = all_docs["documents"]
    metadatas = all_docs["metadatas"]
    tokenized = [clean_text(doc) for doc in docs]

    index = BM25Okapi(tokenized)

    
    bm25_cache[user_id] = (index, docs, metadatas)
    return index, docs, metadatas


def invalidate_cache(user_id: int):
    if user_id in bm25_cache:
        del bm25_cache[user_id]

def bm25_search(query: str, user_id: int):
    index, docs, metadatas = get_bm25_index(user_id)

    if index is None:
        return []

    tokenized_query = clean_text(query)
    scores = index.get_scores(tokenized_query)

    scored = []
    for i, score in enumerate(scores):
        if score > 0:
            scored.append({
                "content": docs[i],
                "metadata": metadatas[i],
                "score": float(score)
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:TOP_K_RETRIEVAL]

def hybrid_search(query: str, user_id: int):
  
    vector_results = vector_search(query, user_id)
    bm25_results = bm25_search(query, user_id)

    
    scores = {}

    for rank, chunk in enumerate(vector_results):
        key = chunk["content"]
        scores[key] = scores.get(key, 0) + 1 / (rank + 1)

    for rank, chunk in enumerate(bm25_results):
        key = chunk["content"]
        scores[key] = scores.get(key, 0) + 1 / (rank + 1)

   
    all_chunks = {c["content"]: c for c in vector_results + bm25_results}
    sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    return [all_chunks[key] for key in sorted_keys[:TOP_K_RETRIEVAL]]