print("1")
import os

print("2")
from fastapi import FastAPI

print("3")
from fastapi.middleware.cors import CORSMiddleware

print("4")
from starlette.middleware.sessions import SessionMiddleware

print("5")
from slowapi import Limiter, _rate_limit_exceeded_handler

print("6")
from slowapi.util import get_remote_address

print("7")
from slowapi.errors import RateLimitExceeded

print("8")
from config import JWT_SECRET

print("9")
from database.postgres import create_tables

print("10")
from auth.routes import router as auth_router

print("11")
from ingestion.routes import router as ingestion_router

print("12")
from retrieval.routes import router as retrieval_router

print("13")
from agent.routes import router as agent_router

print("14")
from features.routes import router as features_router

print("15")
from roadmap.routes import router as roadmap_router

print("16")


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
# app.include_router(documents_router)
app.include_router(roadmap_router)

@app.on_event("startup")
def startup():
    print("Startup 1")
    create_tables()
    print("Startup 2")

@app.get("/")
def health_check():
    return {
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}