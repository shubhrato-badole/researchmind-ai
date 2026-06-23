import chromadb 
from chromadb.config import Settings


client = chromadb.PersistentClient(path="./chromadb_data")

def collection(user_id:str):
    collection_name= f"user{user_id}"
    collection = client.get_or_create_collection(
        name=collection_name,
         metadata={"hnsw:space": "cosine"}
    )

    return collection