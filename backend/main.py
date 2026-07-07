# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import JWT_SECRET
from database.postgres import create_tables

from auth.routes import router as auth_router
from ingestion.routes import router as ingestion_router
from retrieval.routes import router as retrieval_router
from agent.routes import router as agent_router
from features.routes import router as features_router
from documents.routes import router as documents_router
from roadmap.routes import router as roadmap_router


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
        os.getenv("FRONTEND_URL", "http://localhost:5173")
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
app.include_router(documents_router)
app.include_router(roadmap_router)

@app.on_event("startup")
def startup():
    create_tables()
    print("ResearchMind AI started")

@app.get("/")
def health_check():
    return {
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}