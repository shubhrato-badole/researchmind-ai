

from io import BytesIO

from pypdf import PdfReader
from langchain_core.documents import Document

from ingestion.utils import process_and_store


def ingest_pdf(
    file_bytes: bytes,
    filename: str,
    user_id: int,
    content_hash: str | None = None,
) -> dict:
    """Extract PDF text and store its chunks in the user's knowledge base."""

    try:
        reader = PdfReader(BytesIO(file_bytes))

        docs = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            if page_text.strip():
                docs.append(
                    Document(
                        page_content=page_text,
                        metadata={
                            "source": filename,
                            "page": page_number,
                        },
                    )
                )

        if not docs:
            return {
                "message": (
                    "No extractable text found in this PDF. "
                    "It may be scanned and require OCR."
                ),
                "chunks": 0,
            }

        result = process_and_store(
            docs=docs,
            filename=filename,
            source_type="pdf",
            source_url="",
            user_id=user_id,
            content_hash=content_hash
        )

        if str(result.get("message", "")).startswith("Error:"):
            return result

        return result

    except Exception as exc:
        return {
            "message": f"Error processing PDF: {exc}",
            "chunks": 0,
        }
