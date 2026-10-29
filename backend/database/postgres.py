"""PostgreSQL connection and schema initialization for ResearchMind AI."""

import psycopg2
from config import DATABASE_URL


def get_connection():
    """Open a new PostgreSQL connection. Callers own and must close it."""
    return psycopg2.connect(DATABASE_URL)


def create_tables() -> None:
    """Create application tables and apply additive, idempotent migrations.

    This function is run at application startup. Keep schema changes additive so
    an existing database can be upgraded without dropping user data.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    auth_provider VARCHAR(50) DEFAULT 'email',
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    refresh_token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(500),
                    source_type VARCHAR(50),
                    source_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    s3_key TEXT,
                    upload_id TEXT,
                    content_hash VARCHAR(64),
                    lifecycle_status VARCHAR(20) NOT NULL DEFAULT 'active'
                )
                """
            )

            # Add columns to databases created by older versions of the app.
            cur.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS s3_key TEXT")
            cur.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS upload_id TEXT")
            cur.execute(
                "ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64)"
            )
            cur.execute(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(20) NOT NULL DEFAULT 'active'
                """
            )
            cur.execute(
                "UPDATE documents SET lifecycle_status = 'active' WHERE lifecycle_status IS NULL"
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_user_content_hash
                ON documents (user_id, content_hash)
                WHERE content_hash IS NOT NULL
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_documents_user_lifecycle
                ON documents (user_id, lifecycle_status, created_at DESC)
                """
            )

            # Durable work queue for operations that span PostgreSQL, ChromaDB,
            # and S3. Jobs are intentionally not FK-cascaded from documents:
            # failed cleanup must survive deletion of a document row.
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS storage_cleanup_jobs (
                    id BIGSERIAL PRIMARY KEY,
                    job_type VARCHAR(32) NOT NULL
                        CHECK (job_type IN ('upload_rollback', 'delete_document')),
                    user_id INTEGER NOT NULL,
                    document_id INTEGER,
                    upload_id TEXT,
                    s3_key TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    lease_until TIMESTAMPTZ,
                    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK (document_id IS NOT NULL OR upload_id IS NOT NULL OR s3_key IS NOT NULL)
                )
                """
            )
            cur.execute(
                """
                ALTER TABLE storage_cleanup_jobs
                ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_storage_cleanup_job_identity
                ON storage_cleanup_jobs (
                    job_type,
                    user_id,
                    COALESCE(document_id, -1),
                    COALESCE(upload_id, ''),
                    COALESCE(s3_key, '')
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_storage_cleanup_jobs_ready_v2
                ON storage_cleanup_jobs (next_attempt_at, lease_until, created_at)
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS document_topics (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    topic VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) DEFAULT 'New chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(20),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_memory (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    memory TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quiz_scores (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    topic VARCHAR(255),
                    score INTEGER,
                    total INTEGER,
                    difficulty VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS roadmaps (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    goal VARCHAR(500),
                    current_step INTEGER DEFAULT 0,
                    streak INTEGER DEFAULT 0,
                    last_active DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS roadmap_steps (
                    id SERIAL PRIMARY KEY,
                    roadmap_id INTEGER REFERENCES roadmaps(id) ON DELETE CASCADE,
                    step_number INTEGER,
                    title VARCHAR(255),
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'upcoming',
                    estimated_days INTEGER,
                    resources_ingested BOOLEAN DEFAULT FALSE,
                    quiz_passed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS roadmap_subtopics (
                    id SERIAL PRIMARY KEY,
                    roadmap_step_id INTEGER NOT NULL REFERENCES roadmap_steps(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (roadmap_step_id, sort_order)
                )
                """
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("Tables created / migrations applied successfully", flush=True)
