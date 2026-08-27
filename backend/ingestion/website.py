from langchain_community.document_loaders import WebBaseLoader
from ingestion.utils import process_and_store


def ingest_website(url: str, user_id: int):
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()

        if not docs:
            return {
                "message": "No text found on the website",
                "chunks": 0
            }

        return process_and_store(
            docs, url, "website", url, user_id
        )

    except Exception as e:
        return {
            "message": f"Unable to process website: {str(e)}",
            "chunks": 0
        }