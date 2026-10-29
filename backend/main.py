"""FastAPI application entry point for ResearchMind AI."""

import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware

from config import JWT_SECRET
from database.postgres import create_tables
from auth.routes import router as auth_router
from ingestion.routes import router as ingestion_router
from retrieval.routes import router as retrieval_router
from agent.routes import router as agent_router
from features.routes import router as features_router
from roadmap.routes import router as roadmap_router
from payment.routes import router as payment_router

import psycopg2
import redis

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ResearchMind AI", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SessionMiddleware, secret_key=JWT_SECRET)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ingestion_router)
app.include_router(retrieval_router)
app.include_router(agent_router)
app.include_router(features_router)
app.include_router(roadmap_router)
app.include_router(payment_router)

_cleanup_worker_task: asyncio.Task | None = None


async def _cleanup_worker() -> None:
    """Retry durable storage cleanup jobs every 30 seconds."""
    from ingestion.cleanup import process_pending_cleanup_jobs

    while True:
        try:
            completed = await asyncio.to_thread(process_pending_cleanup_jobs, 20)
            if completed:
                print(f"Cleanup worker completed {completed} pending job(s).", flush=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # A transient database/network failure must not terminate the worker.
            print(f"WARNING: Cleanup worker iteration failed: {exc}", flush=True)
        await asyncio.sleep(30)


@app.on_event("startup")
async def startup() -> None:
    global _cleanup_worker_task
    print("========== STARTUP BEGIN ==========", flush=True)
    create_tables()
    print("Database schema created / migrated.", flush=True)
    _cleanup_worker_task = asyncio.create_task(_cleanup_worker())
    print("Storage cleanup retry worker started.", flush=True)
    print("========== STARTUP COMPLETE ==========", flush=True)


@app.on_event("shutdown")
async def shutdown() -> None:
    global _cleanup_worker_task
    task = _cleanup_worker_task
    _cleanup_worker_task = None
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@app.get("/")
def health_check():
    return {"status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/health/ready")
def health_ready():
    checks = {"postgres": False, "redis": False}
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            checks["postgres"] = True
        finally:
            conn.close()
    except Exception:
        checks["postgres"] = False

    try:
        redis_client = redis.from_url(os.getenv("REDIS_URL"))
        checks["redis"] = bool(redis_client.ping())
        redis_client.close()
    except Exception:
        checks["redis"] = False

    ready = all(checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"ready": ready, **checks},
    )
