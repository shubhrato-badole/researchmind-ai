# ResearchMind AI

An agentic knowledge base that lets you upload documents, ask questions, and get cited answers — powered by hybrid search, reranking, and a LangGraph agent that decides when to search your docs vs the web.

## What it does

- Upload PDFs, websites, YouTube videos, images, Word docs, PowerPoints, CSVs, and markdown files
- Ask questions in natural language or by voice
- Get answers with exact source citations
- Agent automatically searches your documents first, falls back to web search if needed
- Detects contradictions between sources
- Flags knowledge gaps and suggests resources
- Generates quizzes from your uploaded content
- Builds learning roadmaps from a single goal

## Tech stack

**Backend** — Python, FastAPI, LangChain, LangGraph  
**Vector DB** — ChromaDB  
**Retrieval** — Hybrid search (vector + BM25), BGE cross-encoder reranking, multi-query RAG  
**LLM** — Gemini (SaaS) / Ollama + Llama 3 (self-hosted / private)  
**Database** — PostgreSQL  
**Auth** — JWT with httpOnly cookies  
**Frontend** — React (in progress)  
**DevOps** — Docker, GitHub Actions

## Architecture

```
User question
      ↓
Multi-query generation (3 query variants)
      ↓
Hybrid search — vector search + BM25 in parallel
      ↓
BGE reranker — top 20 → top 5
      ↓
LangGraph agent — docs enough? or search web too?
      ↓
Answer with citations + contradiction flags
```

## Running locally

```bash
# clone
git clone https://github.com/shubhrato/researchmind-ai
cd researchmind-ai/backend

# setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# configure
cp .env.example .env
# add your GEMINI_API_KEY

# run
uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`

## Deployment modes

| Mode | LLM | Privacy |
|---|---|---|
| SaaS | Gemini API | Standard |
| Self-hosted | Ollama + Llama 3 | 100% private — data never leaves your server |
| Enterprise | Azure OpenAI | Private cloud |

## Status

Backend — in progress  
Frontend — coming soon  
Docker — coming soon

---

Built by [Shubhrato Badole](https://github.com/shubhrato)