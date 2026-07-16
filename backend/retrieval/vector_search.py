from langchain_google_genai import GoogleGenerativeAIEmbeddings
from database.chromadb import get_collection
from config import GEMINI_API_KEY, TOP_K_RETRIEVAL
from functools import lru_cache

@lru_cache(maxsize=1)
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )

def vector_search(query:str , user_id:int):
    embedding = get_embeddings().embed_query(query)
    collection = get_collection(str(user_id))


    results= collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K_RETRIEVAL
    )

    chunks=[]
    
    for i , doc in enumerate(results["documents"][0]):
         chunks.append({
            "content": doc,
            "metadata": results["metadatas"][0][i]
        })
         
         
    return chunks
