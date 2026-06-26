from langchain_core.documents import Document
from ingestion.utils import process_and_store
from PIL import Image
import pytesseract
import tempfile
import os


def ingest_image(file_bytes:bytes ,filename: str, user_id : int):
    with tempfile.NamedTemporaryFile(delete=False , suffix=".png") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    image = Image.open(tmp_path)
    text = pytesseract.image_to_string(image)
    os.unlink(tmp_path)


    if not text.strip():
        return {"message": "No text found in image", "chunks": 0}

    docs = [Document(page_content=text, metadata={"source": filename})]
    return process_and_store(docs, filename, "ocr", None, user_id)