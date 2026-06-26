from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.postgres import create_tables
from database.chromadb import get_collection
from auth.routes import router as auth_router
from ingestion.routes import router as ingestion_router



app = FastAPI(title="ResearchMind AI")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ingestion_router)

@app.on_event("startup")
def startup():
    create_tables()
    print("ChromaDB ready")

@app.get("/")
def health_check():
    return {"status": "ResearchMind is running"}