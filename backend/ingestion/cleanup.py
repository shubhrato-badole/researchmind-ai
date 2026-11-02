"""Durable, retryable cleanup for operations spanning PostgreSQL, ChromaDB, and S3.

The cleanup queue is intentionally small and PostgreSQL-backed. External storage
operations are idempotent and a failed job remains queued for the worker to retry.
"""

from __future__ import annotations

from typing import Any

from database.postgres import get_connection


def enqueue_cleanup_job(
    job_type: str,
    user_id: int,
    *,
    document_id: int | None = None,
    upload_id: str | None = None,
    s3_key: str | None = None,
) -> int:
    """Persist a cleanup operation and return its stable job ID.

    For document deletion/rollback, hide the row immediately by marking it
    `deleting` in the same PostgreSQL transaction as the job insertion.
    """
    if job_type not in {"upload_rollback", "delete_document"}:
        raise ValueError(f"Unsupported cleanup job type: {job_type}")
    if document_id is None and upload_id is None and s3_key is None:
        raise ValueError("A cleanup job must identify a document, upload, or S3 key")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if document_id is not None:
                cur.execute(
                    """
                    UPDATE documents
                    SET lifecycle_status = 'deleting'
                    WHERE id = %s AND user_id = %s
                    """,
                    (document_id, user_id),
                )

            cur.execute(
                """
                INSERT INTO storage_cleanup_jobs
                    (job_type, user_id, document_id, upload_id, s3_key)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (job_type, user_id, document_id, upload_id, s3_key),
            )
            inserted = cur.fetchone()
            if inserted:
                job_id = int(inserted[0])
            else:
                cur.execute(
                    """
                    SELECT id
                    FROM storage_cleanup_jobs
                    WHERE job_type = %s
                      AND user_id = %s
                      AND document_id IS NOT DISTINCT FROM %s
                      AND upload_id IS NOT DISTINCT FROM %s
                      AND s3_key IS NOT DISTINCT FROM %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (job_type, user_id, document_id, upload_id, s3_key),
                )
                found = cur.fetchone()
                if not found:
                    raise RuntimeError("Cleanup job insert conflicted but the job could not be found")
                job_id = int(found[0])
        conn.commit()
        return job_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _claim_job(job_id: int | None = None) -> dict[str, Any] | None:
    """Claim one job with a lease so multiple API workers do not race it."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if job_id is None:
                cur.execute(
                    """
                    WITH candidate AS (
                        SELECT id
                        FROM storage_cleanup_jobs
                        WHERE (lease_until IS NULL OR lease_until < CURRENT_TIMESTAMP)
                          AND next_attempt_at <= CURRENT_TIMESTAMP
                        ORDER BY next_attempt_at, created_at, id
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    UPDATE storage_cleanup_jobs AS jobs
                    SET lease_until = CURRENT_TIMESTAMP + INTERVAL '5 minutes',
                        attempts = attempts + 1,
                        updated_at = CURRENT_TIMESTAMP
                    FROM candidate
                    WHERE jobs.id = candidate.id
                    RETURNING jobs.id, jobs.job_type, jobs.user_id, jobs.document_id,
                              jobs.upload_id, jobs.s3_key, jobs.attempts
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, job_type, user_id, document_id, upload_id, s3_key, attempts
                    FROM storage_cleanup_jobs
                    WHERE id = %s
                      AND (lease_until IS NULL OR lease_until < CURRENT_TIMESTAMP)
                      AND next_attempt_at <= CURRENT_TIMESTAMP
                    FOR UPDATE
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
                if not row:
                    conn.commit()
                    return None
                cur.execute(
                    """
                    UPDATE storage_cleanup_jobs
                    SET lease_until = CURRENT_TIMESTAMP + INTERVAL '5 minutes',
                        attempts = attempts + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING attempts
                    """,
                    (job_id,),
                )
                attempts = cur.fetchone()[0]
                row = (*row[:6], attempts)
            row = cur.fetchone() if job_id is None else row
        conn.commit()
        if not row:
            return None
        return {
            "id": int(row[0]),
            "job_type": row[1],
            "user_id": int(row[2]),
            "document_id": int(row[3]) if row[3] is not None else None,
            "upload_id": row[4],
            "s3_key": row[5],
            "attempts": int(row[6]),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _invalidate_bm25_cache(user_id: int) -> None:
    # Cache invalidation is best-effort for a completed storage mutation: the
    # retrieval cache has a short TTL, and a Redis outage must not strand a
    # document forever in deletion-pending state.
    try:
        from retrieval.hybrid_search import invalidate_cache

        invalidate_cache(user_id)
    except Exception as exc:
        print(
            f"WARNING: BM25 invalidation failed for user {user_id}; cache TTL will recover: {exc}",
            flush=True,
        )


def _run_claimed_job(job: dict[str, Any]) -> dict[str, Any]:
    """Perform idempotent external deletes; keep the job if any step fails."""
    job_id = job["id"]
    user_id = job["user_id"]
    upload_id = job["upload_id"]
    document_id = job["document_id"]
    s3_key = job["s3_key"]

    try:
        # Step 1: remove only this user's upload batch from ChromaDB.
        if upload_id:
            from database.chromadb import get_collection

            collection = get_collection(str(user_id))
            collection.delete(
                where={
                    "$and": [
                        {"user_id": str(user_id)},
                        {"upload_id": upload_id},
                    ]
                }
            )
            _invalidate_bm25_cache(user_id)

        # Step 2: delete the stored file. S3 DeleteObject is safe to retry.
        if s3_key:
            from ingestion.s3_utils import delete_file_from_s3

            delete_file_from_s3(s3_key)

        # Step 3: only remove the PostgreSQL row once Chroma/S3 cleanup succeeded.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                if document_id is not None:
                    cur.execute(
                        "DELETE FROM documents WHERE id = %s AND user_id = %s",
                        (document_id, user_id),
                    )
                elif upload_id:
                    # Upload rollback for a row that may have committed before an
                    # upstream error was observed. upload_id uniquely scopes it.
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

        # Cache invalidation also runs for a job that had no upload_id but deleted
        # a database row, so old keyword results are not left cached.
        _invalidate_bm25_cache(user_id)

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM storage_cleanup_jobs WHERE id = %s", (job_id,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return {"job_id": job_id, "completed": True}

    except Exception as exc:
        try:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE storage_cleanup_jobs
                        SET last_error = %s,
                            lease_until = NULL,
                            next_attempt_at = CURRENT_TIMESTAMP + LEAST(
                                INTERVAL '15 minutes',
                                INTERVAL '30 seconds' * POWER(2, LEAST(GREATEST(attempts - 1, 0), 5))
                            ),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (f"{type(exc).__name__}: {exc}"[:4000], job_id),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        except Exception as record_exc:
            print(
                f"ERROR: cleanup job {job_id} failed ({exc}); could not record failure ({record_exc})",
                flush=True,
            )
        print(f"WARNING: cleanup job {job_id} remains pending: {exc}", flush=True)
        return {"job_id": job_id, "completed": False, "error": str(exc)}


def process_cleanup_job(job_id: int) -> dict[str, Any]:
    """Try a specific queued job once; safe to call from an API request."""
    job = _claim_job(job_id)
    if job is None:
        return {"job_id": job_id, "completed": False, "error": "Job is already being processed"}
    return _run_claimed_job(job)


def process_pending_cleanup_jobs(limit: int = 20) -> int:
    """Process up to `limit` pending jobs. Intended for the periodic worker."""
    completed = 0
    for _ in range(max(1, min(int(limit), 100))):
        job = _claim_job()
        if job is None:
            break
        outcome = _run_claimed_job(job)
        if outcome.get("completed"):
            completed += 1
    return completed
