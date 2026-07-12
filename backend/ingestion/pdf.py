from langchain_community.document_loaders import PyPDFLoader
from ingestion.utils import process_and_store
import tempfile
import os


def ingest_pdf(file_bytes: bytes, filename: str, user_id: int):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()

        return process_and_store(
            docs,
            filename,
            "pdf",
            None,
            user_id
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)