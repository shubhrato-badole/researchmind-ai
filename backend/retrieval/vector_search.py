
from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from database.chromadb import get_collection
from config import GEMINI_API_KEY, TOP_K_RETRIEVAL


EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768


@lru_cache(maxsize=1)
def get_embeddings():
    """Return the shared embedding model used by ingestion."""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
        output_dimensionality=EMBEDDING_DIMENSIONS,
    )


def vector_search(query: str, user_id: int):
    """Search the current user's ChromaDB collection."""

    embedding = get_embeddings().embed_query(query)
    collection = get_collection(str(user_id))

    # Handle a new or empty collection safely.
    document_count = collection.count()

    if document_count == 0:
        return []

    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(TOP_K_RETRIEVAL, document_count),
    )

    chunks = []

    result_documents = results.get("documents") or [[]]
    result_metadatas = results.get("metadatas") or [[]]

    documents = result_documents[0] if result_documents else []
    metadatas = result_metadatas[0] if result_metadatas else []

    for index, document in enumerate(documents):
        chunks.append(
            {
                "content": document,
                "metadata": (
                    metadatas[index]
                    if index < len(metadatas)
                    else {}
                ),
            }
        )

    return chunks
