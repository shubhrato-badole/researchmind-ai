"""Shared document chunking, embedding, and storage pipeline."""

import traceback
import uuid

import psycopg2
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, GEMINI_API_KEY
from database.chromadb import get_collection
from database.postgres import get_connection
from ingestion.storage_context import get_current_s3_key


def _invalidate_bm25_cache(user_id: int) -> None:
    """Invalidate local/shared keyword-search cache without masking ingestion."""
    try:
        from retrieval.hybrid_search import invalidate_cache

        invalidate_cache(user_id)
        print(f"PASS: BM25 cache invalidated for user {user_id}.", flush=True)
    except Exception as exc:
        print(
            f"WARNING: Could not invalidate BM25 cache for user {user_id}: {exc}",
            flush=True,
        )


def _queue_chroma_cleanup(user_id: int, upload_id: str) -> None:
    """Persist retry work if immediate cleanup of a failed ingestion fails."""
    try:
        from ingestion.cleanup import enqueue_cleanup_job

        enqueue_cleanup_job("upload_rollback", user_id, upload_id=upload_id)
    except Exception as exc:
        # If PostgreSQL itself is unavailable there is no durable queue to write.
        # Preserve the error in logs; the API route separately cleans up the S3 key.
        print(
            f"ERROR: Could not queue cleanup for partial upload {upload_id}: {exc}",
            flush=True,
        )


def process_and_store(
    docs: list,
    filename: str,
    source_type: str,
    source_url: str | None,
    user_id: int,
    content_hash: str | None = None,
):
    upload_id = uuid.uuid4().hex
    collection = None
    stored_ids: list[str] = []
    document_saved = False
    cleanup_failed = False

    print("\n========== INGESTION DEBUG START ==========", flush=True)
    print(f"File: {filename}", flush=True)
    print(f"Source type: {source_type}", flush=True)
    print(f"User ID: {user_id}", flush=True)
    print(f"Extracted document sections/pages: {len(docs)}", flush=True)

    try:
        total_characters = sum(len(doc.page_content or "") for doc in docs)
        print(f"Extracted characters: {total_characters}", flush=True)
        if total_characters == 0:
            return {
                "message": "No extractable text found in the document.",
                "chunks": 0,
                "upload_id": upload_id,
            }

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(docs)
        print(f"Chunks generated: {len(chunks)}", flush=True)
        if not chunks:
            return {
                "message": "No content found after text splitting.",
                "chunks": 0,
                "upload_id": upload_id,
            }

        for i, chunk in enumerate(chunks[:3]):
            print(f"Chunk {i + 1}: {len(chunk.page_content)} characters", flush=True)

        print("STEP 3: Initializing Gemini embeddings model...", flush=True)
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2",
            google_api_key=GEMINI_API_KEY,
            output_dimensionality=768,
        )
        print("PASS: Embedding model initialized.", flush=True)

        print("STEP 4: Connecting to ChromaDB...", flush=True)
        collection = get_collection(str(user_id))
        collection_name = collection.name
        print(f"Collection name: {collection_name}", flush=True)
        print(f"Vectors before upload: {collection.count()}", flush=True)

        expected_collection = f"user_{user_id}"
        if collection_name != expected_collection:
            raise RuntimeError(
                f"Wrong collection: expected {expected_collection}, received {collection_name}"
            )

        for i, chunk in enumerate(chunks):
            text = (chunk.page_content or "").strip()
            if not text:
                print(f"Skipping empty chunk {i + 1}", flush=True)
                continue

            print(f"Embedding chunk {i + 1}/{len(chunks)}...", flush=True)
            embedding = embeddings_model.embed_query(text)
            if len(embedding) != 768:
                raise RuntimeError(f"Unexpected embedding dimensions: {len(embedding)}")

            chunk_id = f"{source_type}_{upload_id}_{i}"
            metadata = dict(chunk.metadata or {})
            metadata.update(
                {
                    "source_type": source_type,
                    "filename": filename,
                    "source_url": source_url or "",
                    "user_id": str(user_id),
                    "upload_id": upload_id,
                    "chunk_index": i,
                }
            )
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
            )
            stored_ids.append(chunk_id)
            print(f"PASS: Stored chunk {i + 1}/{len(chunks)}; id={chunk_id}", flush=True)

        if not stored_ids:
            raise RuntimeError("No non-empty chunks were stored.")

        print("STEP 6: Verifying stored vectors...", flush=True)
        verification = collection.get(ids=stored_ids, include=["metadatas"])
        found_ids = set(verification.get("ids") or [])
        missing_ids = set(stored_ids) - found_ids
        if missing_ids:
            raise RuntimeError(f"{len(missing_ids)} vectors could not be verified.")

        saved_metadata = verification.get("metadatas") or []
        wrong_owner = [
            metadata
            for metadata in saved_metadata
            if not metadata
            or metadata.get("user_id") != str(user_id)
            or metadata.get("upload_id") != upload_id
        ]
        if wrong_owner:
            raise RuntimeError("Saved chunks have unexpected ownership or upload metadata.")

        print(f"PASS: All {len(found_ids)} vectors verified in {collection_name}.", flush=True)

        print("STEP 7: Saving document metadata in PostgreSQL...", flush=True)
        # For file uploads, the route sets this request-local value before invoking
        # a loader. Persist the S3 key in the same INSERT as the document row so
        # there is no crash window between document creation and key attachment.
        s3_key = get_current_s3_key()
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents
                        (user_id, title, source_type, source_url, upload_id, content_hash, s3_key)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, filename, source_type, source_url or "", upload_id, content_hash, s3_key),
                )
                document_id = int(cur.fetchone()[0])
            conn.commit()
            document_saved = True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        _invalidate_bm25_cache(user_id)
        print("PASS: Document metadata saved in PostgreSQL.", flush=True)
        print("========== INGESTION DEBUG SUCCESS ==========\n", flush=True)
        return {
            "message": f"{source_type} ingested successfully",
            "chunks": len(found_ids),
            "document_id": document_id,
            "upload_id": upload_id,
        }

    except Exception as exc:
        is_duplicate = isinstance(exc, psycopg2.errors.UniqueViolation)
        print(f"FAIL: Ingestion failed: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()

        # Only roll back Chroma chunks when this attempt did not commit its own
        # document row. Scope every deletion by both user and upload ID.
        if collection is not None and not document_saved:
            try:
                collection.delete(
                    where={"$and": [{"user_id": str(user_id)}, {"upload_id": upload_id}]}
                )
                remaining = collection.get(
                    where={"$and": [{"user_id": str(user_id)}, {"upload_id": upload_id}]},
                    include=["metadatas"],
                )
                if remaining.get("ids"):
                    raise RuntimeError("Some partial Chroma chunks remained after deletion")
                print(f"Cleanup: verified partial chunks removed for {upload_id}.", flush=True)
            except Exception as cleanup_exc:
                cleanup_failed = True
                print(f"WARNING: Could not fully clean partial Chroma chunks: {cleanup_exc}", flush=True)
                # Fallback to tracked IDs, then verify again.
                if stored_ids:
                    try:
                        collection.delete(ids=stored_ids)
                        remaining = collection.get(ids=stored_ids, include=["metadatas"])
                        if remaining.get("ids"):
                            raise RuntimeError("Tracked chunk IDs still exist after fallback cleanup")
                        cleanup_failed = False
                        print("Cleanup: verified tracked partial chunk IDs removed.", flush=True)
                    except Exception as fallback_exc:
                        cleanup_failed = True
                        print(f"WARNING: Fallback Chroma cleanup failed: {fallback_exc}", flush=True)
            _invalidate_bm25_cache(user_id)

        if cleanup_failed:
            _queue_chroma_cleanup(user_id, upload_id)

        print("========== INGESTION DEBUG FAILED ==========\n", flush=True)
        return {
            "message": (
                "This file has already been uploaded. Please delete the existing document before uploading it again."
                if is_duplicate
                else f"Error: {str(exc)}"
            ),
            "error_code": "duplicate_content" if is_duplicate else "ingestion_failed",
            "chunks": 0,
            "upload_id": upload_id,
        }
