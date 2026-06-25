from langchain_community.document_loaders import Docx2txtLoader, TextLoader
from ingestion.utils import process_and_store
import tempfile
import os

def ingest_word(file_bytes: bytes, filename: str, user_id: int):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    loader = Docx2txtLoader(tmp_path)
    docs = loader.load()
    os.unlink(tmp_path)

    return process_and_store(docs, filename, "word", None, user_id)

def ingest_text(file_bytes: bytes, filename: str, user_id: int):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    loader = TextLoader(tmp_path)
    docs = loader.load()
    os.unlink(tmp_path)

    return process_and_store(docs, filename, "text", None, user_id)