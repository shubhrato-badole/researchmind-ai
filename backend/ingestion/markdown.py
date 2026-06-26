from langchain.schema import Document
from ingestion.utils import process_and_store

def ingest_markdown(file_bytes: bytes, filename: str, user_id: int):
    try:
        text = file_bytes.decode("utf-8")
        if not text.strip():
            return {"message": "Empty file", "chunks": 0}

        docs = [Document(page_content=text, metadata={"source": filename})]
        return process_and_store(docs, filename, "markdown", None, user_id)

    except Exception as e:
        return {"message": f"Error: {str(e)}", "chunks": 0}