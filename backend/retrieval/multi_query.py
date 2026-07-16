from langchain_google_genai import ChatGoogleGenerativeAI
from retrieval.hybrid_search import hybrid_search
# from retrieval.reranker import rerank
from config import GEMINI_API_KEY
from functools import lru_cache

@lru_cache(maxsize=1)
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY
    )

def generate_queries(query: str):
    prompt = f"""Generate 3 different versions of this question to improve document search.
Each version should use different words but mean the same thing.
Return only the 3 questions, one per line, no numbering, no extra text.

Question: {query}"""

    try:
        response = get_llm().invoke(prompt)
        lines = response.content.strip().split("\n")
        queries = [line.strip() for line in lines if line.strip()]
        return queries[:3]
    except:
        return []
    
def multi_query_search(query: str, user_id: int):
   
    variants = generate_queries(query)   
    all_queries = [query] + variants
    all_chunks = {}

    for q in all_queries:
        try:
            results = hybrid_search(q, user_id)
            for chunk in results:
                key = chunk["content"]
                if key not in all_chunks:
                    all_chunks[key] = chunk
        except:
            continue

    if not all_chunks:
        return []
    
    combined = list(all_chunks.values())
    return combined
