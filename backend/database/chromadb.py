import chromadb
from config import CHROMA_HOST, CHROMA_PORT

def get_client():
    return chromadb.HttpClient(
        host=CHROMA_HOST,
        port=int(CHROMA_PORT)
    )

def get_collection(user_id: str):
    client = get_client()
    collection = client.get_or_create_collection(
        name=f"user_{user_id}",
        metadata={"hnsw:space": "cosine"}
    )
    return collection