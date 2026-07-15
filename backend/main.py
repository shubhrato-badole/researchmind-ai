print("Importing os")
import os

print("Importing FastAPI")
from fastapi import FastAPI

print("Importing CORS")
from fastapi.middleware.cors import CORSMiddleware

print("Importing SessionMiddleware")
from starlette.middleware.sessions import SessionMiddleware

print("Importing SlowAPI")
from slowapi import Limiter, _rate_limit_exceeded_handler

print("Importing get_remote_address")
from slowapi.util import get_remote_address

print("Importing RateLimitExceeded")
from slowapi.errors import RateLimitExceeded

print("Importing config")
from config import JWT_SECRET

print("Importing postgres")
from database.postgres import create_tables

print("Importing auth router")
from auth.routes import router as auth_router

print("Importing ingestion router")
from ingestion.routes import router as ingestion_router

print("Importing retrieval router")
from retrieval.routes import router as retrieval_router

print("Importing agent router")
from agent.routes import router as agent_router

print("Importing features router")
from features.routes import router as features_router

print("Importing roadmap router")
from roadmap.routes import router as roadmap_router

print("Finished all imports")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ResearchMind AI",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    SessionMiddleware,
    secret_key=JWT_SECRET
)

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

print("Including auth router")
app.include_router(auth_router)

print("Including ingestion router")
app.include_router(ingestion_router)

print("Including retrieval router")
app.include_router(retrieval_router)

print("Including agent router")
app.include_router(agent_router)

print("Including features router")
app.include_router(features_router)

# app.include_router(documents_router)

print("Including roadmap router")
app.include_router(roadmap_router)

print("Routers registered successfully")


@app.on_event("startup")
def startup():
    print("========== STARTUP BEGIN ==========")

    print("Calling create_tables()")
    create_tables()

    print("create_tables() finished")

    print("========== STARTUP COMPLETE ==========")


@app.get("/")
def health_check():
    return {
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }