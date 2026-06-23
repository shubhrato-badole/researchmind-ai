from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.postgres import create_tables


app = FastAPI(title="ResearchMind AI")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()
    
@app.get("/")
def health_check():
    return {"status": "ResearchMind is running"}