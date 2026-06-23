from dotenv import load_dotenv
import os #os is a built-in Python library used to interact with the operating system.


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
LLM_MODE = os.getenv("LLM_MODE", "gemini")

CHROMA_HOST = "localhost"
CHROMA_PORT = 8000


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RETRIEVAL = 20
TOP_K_RERANK = 5
