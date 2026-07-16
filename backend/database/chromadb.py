import chromadb
from config import CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE
from functools import lru_cache

@lru_cache(maxsize=1)
def get_client():
    return chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE
    )


def get_collection(user_id: str):
    client = get_client()
    collection = client.get_or_create_collection(
        name=f"user_{user_id}",
        metadata={"hnsw:space": "cosine"}
    )
    return collection