"""Authenticated ingestion, document download, and deletion endpoints."""

import hashlib
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auth.jwt import get_current_user
from database.chromadb import get_collection
from database.postgres import get_connection
from ingestion.cleanup import enqueue_cleanup_job, process_cleanup_job
from ingestion.storage_context import reset_current_s3_key, set_current_s3_key
from ingestion.s3_utils import (
    delete_file_from_s3,
    generate_presigned_url,
    upload_file_to_s3,
)
from limit.rate_limiter import check_document_limit

router = APIRouter(
    prefix="/ingest",
    tags=["ingestion"],
    dependencies=[Depends(get_current_user)],
)

MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "csv", "png", "jpg", "jpeg", "pptx", "md"}


class URLRequest(BaseModel):
    url: str


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _schedule_upload_rollback(
    user_id: int,
    s3_key: str,
    *,
    document_id: int | None = None,
    upload_id: str | None = None,
) -> dict[str, Any]:
    """Queue and immediately attempt compensation for a failed upload.

    If PostgreSQL is unavailable even for queue insertion, try the external
    cleanup directly and log any remaining work. Persistent retry is impossible
    while the queue database itself is unavailable, so this is best effort.
    """
    try:
        job_id = enqueue_cleanup_job(
            "upload_rollback",
            user_id,
            document_id=document_id,
            upload_id=upload_id,
            s3_key=s3_key,
        )
        return process_cleanup_job(job_id)
    except Exception as queue_exc:
        print(
            f"ERROR: Could not queue upload rollback (user={user_id}, upload={upload_id}): {queue_exc}",
            flush=True,
        )

    # Last-resort best effort if the database-backed queue cannot be written.
    if upload_id:
        try:
            collection = get_collection(str(user_id))
            collection.delete(
                where={"$and": [{"user_id": str(user_id)}, {"upload_id": upload_id}]}
            )
        except Exception as exc:
            print(f"ERROR: Immediate Chroma cleanup failed for {upload_id}: {exc}", flush=True)
    try:
        delete_file_from_s3(s3_key)
    except Exception as exc:
        print(f"ERROR: Immediate S3 cleanup failed for {s3_key}: {exc}", flush=True)
    try:
        from retrieval.hybrid_search import invalidate_cache

        invalidate_cache(user_id)
    except Exception as exc:
        print(f"WARNING: Immediate BM25 invalidation failed for user {user_id}: {exc}", flush=True)
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                if document_id is not None:
                    cur.execute(
                        "DELETE FROM documents WHERE id = %s AND user_id = %s",
                        (document_id, user_id),
                    )
                elif upload_id:
                    cur.execute(
                        "DELETE FROM documents WHERE user_id = %s AND upload_id = %s",
                        (user_id, upload_id),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as exc:
        print(f"ERROR: Immediate PostgreSQL cleanup failed: {exc}", flush=True)
    return {"completed": False, "error": "Cleanup queue could not be reached"}


def _find_legacy_upload_id(collection, user_id: int, title: str, source_url: str | None):
    """Return a unique legacy upload batch; refuse unsafe ambiguous deletions."""
    matches = collection.get(
        where={
            "$and": [
                {"user_id": str(user_id)},
                {"filename": title},
                {"source_url": source_url or ""},
            ]
        },
        include=["metadatas"],
    )
    metadata_items = matches.get("metadatas") or []
    upload_ids = {
        item.get("upload_id")
        for item in metadata_items
        if item and item.get("upload_id")
    }
    if len(upload_ids) > 1:
        raise HTTPException(
            status_code=409,
            detail=(
                "This older document matches multiple stored chunk batches. "
                "No data was deleted because the correct batch cannot be identified safely."
            ),
        )
    if metadata_items and not upload_ids:
        raise HTTPException(
            status_code=409,
            detail=(
                "This legacy document has chunks without an upload identifier. "
                "Deletion is paused to avoid removing another document's data."
            ),
        )
    return next(iter(upload_ids), None)


@router.post("/file")
async def upload_file(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
):
    user_id = get_current_user(request, response)
    filename = file.filename or ""
    ext = get_extension(filename)

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not supported")

    file_bytes = await file.read()
    await file.close()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 20MB.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    content_hash = hashlib.sha256(file_bytes).hexdigest()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM documents
                WHERE user_id = %s AND content_hash = %s
                  AND COALESCE(lifecycle_status, 'active') = 'active'
                LIMIT 1
                """,
                (user_id, content_hash),
            )
            existing_document = cur.fetchone()
    finally:
        conn.close()

    if existing_document:
        raise HTTPException(
            status_code=409,
            detail=(
                "This file has already been uploaded. "
                "Please delete the existing document before uploading it again."
            ),
        )

    allowed, _ = check_document_limit(user_id)
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="Document limit reached (5 max). Upgrade to Pro for unlimited uploads.",
        )

    s3_key = f"user_{user_id}/{uuid.uuid4()}_{filename}"
    try:
        upload_file_to_s3(file_bytes, s3_key)
    except Exception as exc:
        # A network timeout can occur after S3 accepted the object but before
        # the client received confirmation. Delete/queue this unique key anyway.
        cleanup = _schedule_upload_rollback(user_id, s3_key)
        detail = "File storage upload failed."
        if not cleanup.get("completed"):
            detail += " Cleanup is queued for automatic retry."
        raise HTTPException(status_code=500, detail=detail) from exc

    result: Any = None

    try:
        # Preserve all existing loader signatures while ensuring process_and_store
        # writes this file's S3 key in the SAME PostgreSQL INSERT as its row.
        token = set_current_s3_key(s3_key)
        try:
            if ext == "pdf":
                from ingestion.pdf import ingest_pdf

                result = ingest_pdf(file_bytes, filename, user_id, content_hash=content_hash)
            elif ext == "docx":
                from ingestion.document import ingest_word

                result = ingest_word(file_bytes, filename, user_id, content_hash=content_hash)
            elif ext == "txt":
                from ingestion.document import ingest_text

                result = ingest_text(file_bytes, filename, user_id, content_hash=content_hash)
            elif ext == "csv":
                from ingestion.csv import ingest_csv

                result = ingest_csv(file_bytes, filename, user_id, content_hash=content_hash)
            elif ext in {"png", "jpg", "jpeg"}:
                from ingestion.ocr import ingest_image

                result = ingest_image(file_bytes, filename, user_id, content_hash=content_hash)
            elif ext == "pptx":
                from ingestion.pptx import ingest_pptx

                result = ingest_pptx(file_bytes, filename, user_id, content_hash=content_hash)
            elif ext == "md":
                from ingestion.markdown import ingest_markdown

                result = ingest_markdown(file_bytes, filename, user_id, content_hash=content_hash)
        finally:
            reset_current_s3_key(token)

        if not isinstance(result, dict) or not result.get("document_id") or not result.get("upload_id"):
            detail = (result or {}).get("message", "Document ingestion failed.")
            cleanup = _schedule_upload_rollback(
                user_id,
                s3_key,
                document_id=(result or {}).get("document_id"),
                upload_id=(result or {}).get("upload_id"),
            )
            duplicate = (
                (result or {}).get("error_code") == "duplicate_content"
                or "already been uploaded" in str(detail).lower()
            )
            if duplicate:
                raise HTTPException(status_code=409, detail=str(detail))
            if not cleanup.get("completed"):
                detail = f"{detail} Cleanup has been queued for automatic retry."
            raise HTTPException(status_code=500, detail=str(detail))

        # `s3_key` was persisted atomically with the document row in
        # process_and_store. There is deliberately no second UPDATE here.
        return result

    except HTTPException:
        # The invalid-result path already queued rollback. If an HTTP error arose
        # after S3 upload from another layer, compensation is idempotent.
        if isinstance(result, dict) and result.get("document_id") and result.get("upload_id"):
            _schedule_upload_rollback(
                user_id,
                s3_key,
                document_id=int(result["document_id"]),
                upload_id=str(result["upload_id"]),
            )
        raise
    except Exception as exc:
        cleanup = _schedule_upload_rollback(
            user_id,
            s3_key,
            document_id=(result or {}).get("document_id") if isinstance(result, dict) else None,
            upload_id=(result or {}).get("upload_id") if isinstance(result, dict) else None,
        )
        detail = "Document upload failed."
        if not cleanup.get("completed"):
            detail += " Cleanup is pending and will be retried automatically."
        print(f"ERROR: upload failed for user {user_id}, file {filename}: {exc}", flush=True)
        raise HTTPException(status_code=500, detail=detail) from exc

@router.get("/")
def get_documents(request: Request, response: Response):
    user_id = get_current_user(request, response)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, source_type, source_url, created_at
                FROM documents
                WHERE user_id = %s
                  AND COALESCE(lifecycle_status, 'active') = 'active'
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return {
        "documents": [
            {
                "id": row[0],
                "title": row[1],
                "source_type": row[2],
                "source_url": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            }
            for row in rows
        ]
    }


@router.get("/{doc_id}/download")
def download_document(doc_id: int, request: Request, response: Response):
    user_id = get_current_user(request, response)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s3_key FROM documents
                WHERE id = %s AND user_id = %s
                  AND COALESCE(lifecycle_status, 'active') = 'active'
                """,
                (doc_id, user_id),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="File not available for download")
    return {"download_url": generate_presigned_url(row[0])}


@router.delete("/{doc_id}")
def delete_document(doc_id: int, request: Request, response: Response):
    user_id = get_current_user(request, response)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s3_key, upload_id, title, source_url, lifecycle_status
                FROM documents
                WHERE id = %s AND user_id = %s
                """,
                (doc_id, user_id),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        # A prior cleanup job may already have completed and removed the row.
        return {"status": "deleted"}

    s3_key, upload_id, title, source_url, lifecycle_status = row

    # Resolve legacy rows before marking them for deletion. If the chunk batch
    # is ambiguous, do not enqueue any destructive work.
    if not upload_id:
        collection = get_collection(str(user_id))
        upload_id = _find_legacy_upload_id(collection, user_id, title or "", source_url)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM storage_cleanup_jobs
                WHERE job_type = 'delete_document' AND user_id = %s AND document_id = %s
                ORDER BY id DESC LIMIT 1
                """,
                (user_id, doc_id),
            )
            pending = cur.fetchone()
    finally:
        conn.close()

    if lifecycle_status != "deleting" or not pending:
        job_id = enqueue_cleanup_job(
            "delete_document",
            user_id,
            document_id=doc_id,
            upload_id=upload_id,
            s3_key=s3_key,
        )
    else:
        job_id = int(pending[0])

    outcome = process_cleanup_job(job_id)
    if outcome.get("completed"):
        return {"status": "deleted"}

    warning = (
        "Deletion has started, but cleanup of one or more storage systems is still pending. "
        "The document is hidden and the backend will retry automatically."
    )
    print(
        f"WARNING: document deletion pending for document {doc_id}, user {user_id}: {outcome.get('error')}",
        flush=True,
    )
    return JSONResponse(
        status_code=202,
        content={"status": "deletion_pending", "warning": warning},
    )


@router.post("/website")
def upload_website(data: URLRequest, request: Request, response: Response):
    from ingestion.website import ingest_website

    user_id = get_current_user(request, response)
    return ingest_website(data.url, user_id)


@router.post("/youtube")
def upload_youtube(data: URLRequest, request: Request, response: Response):
    from ingestion.youtube import ingest_youtube

    user_id = get_current_user(request, response)
    return ingest_youtube(data.url, user_id)
