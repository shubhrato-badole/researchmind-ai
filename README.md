<div align="center">

<img src="frontend/public/favicon.svg" alt="ResearchMind AI logo" width="72" height="72" />

# ResearchMind AI

**Your documents. Answered instantly.**

Upload PDFs, slides, websites and YouTube videos, then ask questions and get cited answers grounded in your own content.
The same knowledge base also powers quizzes, flashcards, mock interviews and step-by-step learning roadmaps.

![License: MIT](https://img.shields.io/badge/License-MIT-green)
![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

[Demo](#screenshots-and-demos) · [Features](#features) · [How it works](#how-it-works) · [Quick start](#quick-start) · [Evaluation](#evaluation) · [Project structure](#project-structure) · [Limitations](#limitations-and-roadmap)

</div>

<p align="center">
  <img src="docs/images/demo-ask.gif" alt="Asking ResearchMind a question and receiving an answer with its source document" width="88%" />
  <br />
  <sub>Ask a question, get an answer grounded in your documents, with the source shown. Waiting time is sped up in this clip.
  Full-quality MP4s: <a href="docs/videos/demo-ask.mp4">ask</a> · <a href="docs/videos/demo-quiz.mp4">quiz</a> · <a href="docs/videos/demo-roadmap.mp4">roadmap</a>.</sub>
</p>

## Why ResearchMind?

You save PDFs you never re-read, watch tutorials you forget, and bookmark articles you never open. `Ctrl+F` only finds the exact words you remember; ResearchMind finds the *meaning*.

1. **Add your content**: upload a file, paste a website URL, or drop a YouTube link.
2. **Ask anything**: type or speak a question. Search only your documents, your documents plus the web, or the web alone.
3. **Get cited answers**: every answer shows which document, page or URL it came from, and flags when sources disagree.

## Screenshots and demos

<table>
  <tr>
    <td width="50%" align="center" valign="top">
      <img src="docs/images/contradiction-detection.png" alt="An answer flagging a contradiction between two documents that give different API timeouts" /><br />
      <sub><b>Contradiction flagging.</b> Two files give different API timeouts (30 s vs 60 s). The answer says so and cites both.</sub>
    </td>
    <td width="50%" align="center" valign="top">
      <img src="docs/images/web-search-approval.png" alt="ResearchMind reporting that no relevant information was found and asking before searching the web" /><br />
      <sub><b>Asks before searching the web.</b> In <i>Docs + web</i> mode it reports when your documents lack the answer and waits for your approval.</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center" valign="top">
      <img src="docs/images/demo-quiz.gif" alt="Generating and answering a multiple-choice quiz from selected documents" /><br />
      <sub><b>Quiz mode.</b> Pick documents and a difficulty, then answer questions with explanations drawn from your sources.</sub>
    </td>
    <td width="50%" align="center" valign="top">
      <img src="docs/images/demo-roadmap.gif" alt="Creating a learning roadmap and ticking off subtopics in the first step" /><br />
      <sub><b>Learning roadmaps.</b> Enter a goal and get a step-by-step plan. Each step has a subtopic checklist that unlocks its quiz.</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center" valign="top">
      <img src="docs/images/documents.png" alt="The document library listing uploaded files with YouTube, Website and Upload file buttons" /><br />
      <sub><b>Document library.</b> Upload files or add a website or YouTube link. Download or delete anything.</sub>
    </td>
    <td width="50%" align="center" valign="top">
      <img src="docs/images/voice-input.png" alt="Voice input recording while a previous answer with a comparison table and sources is shown" /><br />
      <sub><b>Voice input.</b> Dictate a question. Answers can include tables, and every one ends with its source list.</sub>
    </td>
  </tr>
</table>

## Table of contents

- [Screenshots and demos](#screenshots-and-demos)
- [Features](#features)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Evaluation](#evaluation)
- [Testing and CI](#testing-and-ci)
- [Project structure](#project-structure)
- [Limitations and roadmap](#limitations-and-roadmap)
- [Contributing](#contributing)
- [License](#license)

## Features

### Ask your knowledge base
- **Agentic RAG chat** built on LangGraph with three search modes: *My docs only*, *Docs + web*, and *Web only*.
- **Hybrid retrieval**: Gemini vector search + BM25 keyword search, fused with Reciprocal Rank Fusion (RRF), then re-ranked by a cross-encoder (`BAAI/bge-reranker-base`).
- **Evidence check with bounded retry**: the agent judges whether the retrieved chunks actually answer the question. If not, it makes one multi-query retry. Document search is capped at two calls per turn.
- **Human-in-the-loop web search**: in *Docs + web* mode the agent pauses and asks before it goes to the internet.
- **Cited answers with trust scores**: sources show the filename, page or URL plus a 0-100 trust score per source type.
- **Contradiction flagging**: a rule-based numeric-conflict detector surfaces candidates, and the model verifies them before flagging `⚠ Contradiction detected`.
- **Streaming responses**, persistent chat sessions and history, and voice input through the browser's Web Speech API.

### Add almost any content
- **PDF, Word (.docx), PowerPoint (.pptx), CSV, Markdown, plain text**, **images** (Tesseract OCR), **websites** and **YouTube transcripts**.
- 20 MB per file, SHA-256 duplicate detection (HTTP 409), originals kept in S3 with presigned downloads.
- **Consistent deletes**: a durable, PostgreSQL-backed cleanup queue keeps PostgreSQL, ChromaDB and S3 in sync, retrying failed cleanups every 30 seconds.

### Learn from what you upload
- **Quizzes** scoped to chosen documents, with score history and weak-topic tracking.
- **Flashcards** and **summaries** generated from your content.
- **Interview mode**: an open-ended question drawn from your documents, with AI feedback checked against key points.
- **Learning roadmaps**: describe a goal and get a multi-step plan with a subtopic checklist per step and a quiz gate before each step can be completed.

### Production-minded platform
- **Auth**: email + password with OTP verification, Google sign-in, reCAPTCHA, bcrypt hashing, and short-lived JWT access tokens with refresh sessions in HTTP-only cookies.
- **Free and Pro plans** with Razorpay checkout, signature-verified payments and webhooks, and Redis-backed daily quotas.
- **Per-user isolation**: every user gets a separate vector collection.
- **Health endpoints** (`/health`, `/health/ready`), rate limiting, Docker Compose, Nginx and a CI/CD workflow.

## How it works

```mermaid
flowchart LR
    U["Browser"] --> FE["React + Vite SPA"]
    FE -->|"REST + streaming"| API["FastAPI backend"]
    API --> PG[("PostgreSQL<br/>users, chats, quizzes, roadmaps")]
    API --> RD[("Redis<br/>OTP, quotas, cache version")]
    API --> CH[("Chroma Cloud<br/>one vector collection per user")]
    API --> S3[("AWS S3<br/>original files")]
    API --> GEM["Gemini API<br/>chat + embeddings"]
    API --> WEB["DuckDuckGo<br/>web search"]
    API --> RZP["Razorpay<br/>payments"]
```

### Life of a question

```mermaid
flowchart TD
    Q["User question"] --> M{"Search mode"}
    M -->|"docs / docs + web"| D["search_documents"]
    M -->|"web only"| W["search_internet"]
    D --> H["Hybrid retrieval<br/>vector + BM25, RRF fusion, top 20"]
    H --> R["Cross-encoder rerank, top 5<br/>+ trust scores + conflict check"]
    R --> E{"Evidence sufficient?"}
    E -->|"yes"| A["Answer with citations"]
    E -->|"no, retry once"| MQ["Multi-query retry<br/>original + up to 3 rewrites"]
    MQ --> A
    E -->|"still weak, docs + web mode"| AP["Pause and ask user<br/>to approve web search"]
    AP -->|"approved"| W
    W --> A
```

**Design decisions worth knowing**

| Decision | Why |
|---|---|
| RRF instead of weighted score blending | BM25 and cosine scores live on different scales; rank-based fusion needs no tuning. |
| Max two document searches per turn | Bounds latency and API cost, and prevents retry loops. |
| BM25 index cached per user, invalidated through a Redis version token (60 s TTL fallback) | Fast keyword search without stale results across multiple API workers. |
| Durable cleanup queue in PostgreSQL | An upload or delete spans three systems; failures must be retried, not silently leave orphans. |
| Web search needs approval in *Docs + web* mode | The user stays in control of when a question leaves their own knowledge base. |

> [!NOTE]
> **Where your data goes.** Document text is sent to Google's Gemini API for embeddings and answer generation, and chunks are stored in Chroma Cloud. Original files are stored in your S3 bucket. Keep this in mind before uploading sensitive documents.

## Tech stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, Axios, react-markdown |
| **Backend** | Python 3.11, FastAPI, Uvicorn, LangChain, LangGraph, slowapi, python-jose (JWT), bcrypt, Authlib |
| **AI / retrieval** | Gemini (`gemini-3.5-flash` for chat, `gemini-embedding-2` at 768 dimensions), `BAAI/bge-reranker-base` (sentence-transformers), `rank_bm25`, DuckDuckGo search (`ddgs`) |
| **Data** | PostgreSQL 15, Redis 7, Chroma Cloud, AWS S3 |
| **Ingestion** | pypdf, docx2txt, python-pptx, Tesseract OCR, LangChain web and YouTube loaders, recursive splitter (500 characters, 50 overlap) |
| **Payments** | Razorpay |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions, Trivy, GHCR |
| **Evaluation** | Custom retrieval harness, Ragas, DeepEval, LangSmith, k6 |

## Quick start

### Prerequisites

| Needed | For |
|---|---|
| [Docker](https://docs.docker.com/get-docker/) with Compose v2 | Running the whole stack |
| [Gemini API key](https://aistudio.google.com/apikey) | Chat and embeddings |
| [Chroma Cloud](https://www.trychroma.com/) account (API key, tenant, database) | Vector storage |
| AWS S3 bucket in `ap-south-1` plus IAM credentials | Storing uploaded files |

Optional: SMTP credentials (OTP emails), Google OAuth client (Google sign-in), reCAPTCHA secret, Razorpay keys (Pro upgrades).

> [!NOTE]
> The app talks to **Chroma Cloud** (`chromadb.CloudClient`). The local `chromadb` service in `docker-compose.yml` is not used by the current code.

### Run with Docker Compose

```bash
git clone https://github.com/shubhrato-badole/researchmind-ai.git
cd researchmind-ai

# 1. Create your env files from the templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. Fill in the required values in backend/.env (see Configuration below)

# 3. Build and start PostgreSQL, Redis, the API and the web app
docker compose up --build
```

| Service | URL |
|---|---|
| Web app | http://localhost |
| API docs (Swagger) | http://localhost:8000/docs |
| Readiness check | http://localhost:8000/health/ready |

The first build downloads CPU PyTorch, and the first search downloads the reranker model, so expect a slow first run.

> [!TIP]
> **No SMTP server?** Leave the `SMTP_*` variables empty. The sign-up OTP is printed in the backend logs instead: `docker compose logs -f backend` and look for `[DEV] OTP for ...`.

### Run locally for development

```bash
# Infrastructure only
docker compose up -d postgres redis

# Backend (Python 3.11; Tesseract installed: `brew install tesseract` or `sudo apt install tesseract-ocr`)
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# In backend/.env use localhost addresses:
#   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/researchmind
#   REDIS_URL=redis://localhost:6379/0
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev          # http://localhost:5173, /api is proxied to :8000
```

Tables are created and migrated automatically when the backend starts.

## Configuration

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`. Never commit real `.env` files; they are already in `.gitignore`.

<details>
<summary><strong>All environment variables</strong></summary>

**Backend (`backend/.env`)**

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Gemini API key for chat, embeddings and study features |
| `JWT_SECRET` | Yes | Secret for signing JWTs and sessions. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | Yes (local) | PostgreSQL connection string. Docker Compose sets this for you |
| `REDIS_URL` | Yes | Redis connection string (`redis://redis:6379/0` in Docker, `redis://localhost:6379/0` locally). Used for OTPs, quotas and cache invalidation |
| `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE` | Yes | Chroma Cloud credentials |
| `S3_BUCKET_NAME` | Yes | Bucket for uploaded files (region is set to `ap-south-1` in `ingestion/s3_utils.py`) |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Yes* | Standard AWS credentials (*or use an IAM role) |
| `FRONTEND_URL` | No | Used for CORS and the post-login redirect. Default `http://localhost:5173`; set to `http://localhost` when using the Docker web app |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` | No | OTP emails. If unset, OTPs are logged |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | No | Google sign-in. Authorized redirect URI: `<backend-url>/auth/google/callback` (locally `http://localhost:8000/auth/google/callback`) |
| `RECAPTCHA_SECRET_KEY` | No | reCAPTCHA verification on sign-up and login |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | No | Pro upgrades |
| `RERANKER_MODEL` | No | Cross-encoder model name. Default `BAAI/bge-reranker-base` |

**Frontend (`frontend/.env`)**

| Variable | Description |
|---|---|
| `VITE_API_URL` | API base URL. Use `/api` (proxied by Vite in dev and by Nginx in Docker) |
| `VITE_RAZORPAY_KEY_ID` | Razorpay public key id, only needed for checkout |

</details>

### Plans and limits

| | Free | Pro |
|---|---|---|
| Document uploads | 5 | Unlimited |
| Web searches | 10 / day | Unlimited |
| Direct document search API | 10 / day | Unlimited |
| Learning roadmaps | 1 per 30 days | Unlimited |

Limits live in `backend/limit/rate_limiter.py`.

## API overview

Interactive docs are served at `/docs`. All routes except `/auth/*`, `/payment/webhook` and the health checks require the HTTP-only auth cookie set at login.

| Prefix | Purpose |
|---|---|
| `/auth` | `signup`, `verify-otp`, `resend-otp`, `login`, `google/login`, `me`, `refresh`, `logout`, `change-password`, `delete-account` |
| `/ingest` | Upload a `file`, add a `website` or `youtube` URL, list, download, delete documents |
| `/chat` | Create and list sessions, send a message (optionally streamed), `resume` after a web-search approval, history |
| `/search` | Direct multi-query retrieval over your documents |
| `/features` | Quizzes (`/quiz`, `/quiz/score`, `/quiz/history`, `/quiz/weak-topics`), `flashcards`, `summary`, `interview/question`, `interview/evaluate` |
| `/roadmap` | Create and list roadmaps, `start-step`, `complete-step`, subtopic checklist, step quiz, progress |
| `/payment` | `create-order`, `verify`, `webhook` |

<details>
<summary><strong>Example: chat with web-search approval</strong></summary>

```http
POST /chat/
{ "query": "What does the contract say about termination?", "search_mode": "docs_web", "stream": false, "session_id": null }
```

If the documents fully answer the question:

```json
{ "status": "complete", "answer": "…", "session_id": 12 }
```

If the evidence is thin, the agent pauses before searching the web:

```json
{ "status": "awaiting_approval", "message": "I found limited information in your documents. Should I also search the web?", "thread_id": "7:12", "session_id": 12 }
```

Continue (or decline) with:

```http
POST /chat/resume
{ "thread_id": "7:12", "approved": true, "session_id": 12 }
```

`search_mode` is one of `docs`, `docs_web` or `web`. Set `"stream": true` for a plain-text token stream.

</details>

## Evaluation

Quality claims are only useful when they can be reproduced, so the repository ships its own benchmark in [`backend/evaluation/`](backend/evaluation/README.md):

- **Synthetic corpus**: 9 Markdown documents with 43 labelled evidence sections.
- **100 RAG questions**: 80 evidence-level, 10 multi-hop, 5 unanswerable (abstention), 5 security and conflict cases, split 70 development / 15 validation / 15 held-out test.
- **50 agent scenarios** checking tool routing per search mode.
- **Scripts** for retrieval metrics (Precision, Recall, MRR, nDCG, Hit Rate at K = 2, 5, 10), Ragas, DeepEval, LangSmith export and k6 smoke tests.

### Retrieval results (development split, 70 questions, 67 answerable)

| Retriever | Recall@5 | MRR@5 | nDCG@5 | Median latency |
|---|---|---|---|---|
| BM25 only | 0.970 | 0.884 | 0.898 | 0.1 s |
| Vector only | 0.973 | **0.949** | 0.945 | 1.9 s |
| **Hybrid (vector + BM25, RRF)** | 0.975 | 0.938 | **0.953** | 2.0 s |
| Hybrid + BGE rerank | 0.958 | 0.884 | 0.899 | 3.5 s |
| Hybrid + BGE rank fusion (experimental) | **0.980** | 0.933 | 0.949 | 3.6 s |

On the held-out test split (15 questions, 14 answerable), hybrid retrieval reached Recall@5 0.911, MRR@5 0.929 and a 100% hit rate; adding the BGE reranker lowered MRR@5 to 0.705.

**What this tells us:** on this small corpus all retrievers find the right evidence (Recall@5 between 0.96 and 0.98), so differences are small. Hybrid and vector retrieval rank best, BM25 is by far the fastest, and the cross-encoder reranker added about 1.5 s of latency without a measurable gain.

<details>
<summary><strong>Full metrics at K = 2, 5 and 10</strong></summary>

**Development split** (70 questions, 67 answerable). *Hybrid BGE/RRF* is the experimental BGE rank-fusion variant.

<img src="docs/images/benchmark-development.png" alt="Retrieval metrics for BM25, vector, hybrid, hybrid with rerank and hybrid BGE/RRF on the development split" width="760" />

**Held-out test split** (15 questions, 14 answerable).

<img src="docs/images/benchmark-test.png" alt="Retrieval metrics for hybrid, hybrid with rerank and hybrid BGE/RRF on the held-out test split" width="760" />

</details>

### Answer quality (Ragas smoke test, 6 real app traces)

| Context precision | Context recall | Faithfulness | Answer relevancy | Answer correctness |
|---|---|---|---|---|
| 0.95 | 1.00 | 0.95 | 0.92 | 0.39 |

Judge: `gemini-3.5-flash-lite`. Six cases is a smoke test, not a benchmark; the reference answers are one-line summaries while generated answers are long, which likely depresses the correctness score.

> [!IMPORTANT]
> The benchmark is **synthetic and small**. These numbers describe a controlled test, not production performance. Every run records per-case results so you can audit them in `backend/evaluation/results/`.

<details>
<summary><strong>Reproduce the results</strong></summary>

```bash
# Offline checks: no API calls (run from backend/)
cd backend
python evaluation/scripts/validate_dataset.py     # expects: VALIDATION PASSED
python evaluation/scripts/check_metric_math.py

# 1. Upload the 9 files from backend/evaluation/corpus/ through the Documents page.
#    Use a dedicated test account so other documents don't dilute the scores.
# 2. Find that account's numeric id:
docker compose exec postgres psql -U postgres -d researchmind -c "SELECT id, email FROM users;"

# 3. Run the retrieval benchmark inside the backend container (backend/ is mounted at /app)
docker compose exec backend python evaluation/scripts/run_local_retrieval.py \
  --user-id <ID> --retrievers bm25,vector,hybrid,hybrid_rerank --split development

# Optional: Ragas, DeepEval and LangSmith tooling
pip install -r backend/evaluation/requirements-eval.txt
```

See [`backend/evaluation/README.md`](backend/evaluation/README.md) for metric definitions and the Ragas, LangSmith and k6 workflows.

</details>

## Testing and CI

```bash
cd backend
pip install pytest
pytest -q
```

- Unit tests are mocked and never touch real S3 or databases. They cover the cleanup queue, the contradiction detector and the two-call document-search guard.
- [`FAILURE_TEST_PLAN.md`](FAILURE_TEST_PLAN.md) is a manual failure-injection plan (duplicate uploads, S3 outages, retry worker). Use a disposable account and a non-production bucket.
- [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) defines the CI/CD pipeline: lint and test the backend (ruff, pytest), lint and build the frontend, build and scan images with Trivy, push to GHCR, and deploy over SSH with a readiness check.
- The frontend can also be hosted on Vercel (`frontend/vercel.json` provides the SPA rewrite).

## Project structure

<details>
<summary><strong>Show the folder tree</strong></summary>

```text
researchmind-ai/
├── backend/
│   ├── main.py            # FastAPI app, middleware, health checks, cleanup worker
│   ├── config.py          # Env-driven settings, chunking and retrieval constants
│   ├── agent/             # LangGraph agent, tools, web search, sessions and chat memory
│   ├── retrieval/         # BM25 + vector + RRF hybrid search, multi-query, reranker
│   ├── ingestion/         # Loaders (PDF, DOCX, PPTX, CSV, MD, OCR, web, YouTube), S3, cleanup queue
│   ├── features/          # Quiz, flashcards, summary, interview, trust score, contradictions
│   ├── roadmap/           # Learning roadmaps, subtopic checklist, step quizzes
│   ├── auth/              # Sign-up and OTP, login, Google OAuth, JWT, reCAPTCHA
│   ├── payment/           # Razorpay orders, signature and webhook verification
│   ├── limit/             # Free and Pro quotas (Redis + PostgreSQL)
│   ├── database/          # PostgreSQL schema and migrations, Chroma Cloud and Redis clients
│   ├── mcp/               # MCP server scaffold (not yet enabled)
│   ├── evaluation/        # Benchmark corpus, datasets, scripts, k6 tests, results
│   └── tests/             # Unit tests
├── frontend/
│   └── src/
│       ├── pages/         # Landing, Login, Register, Chat, Documents, StudyMode, Roadmap, Profile, Pricing, Enterprise
│       ├── Components/    # Layout, document picker, search-mode dropdown, upgrade modal, UI primitives
│       ├── hooks/         # Data hooks (documents, sessions, roadmaps, voice input)
│       ├── context/       # Auth context
│       └── Api/           # Axios client
├── docker/                # Dockerfiles and nginx.conf
├── docker-compose.yml     # PostgreSQL, Redis, backend, frontend
├── .github/workflows/     # CI/CD pipeline
├── FAILURE_TEST_PLAN.md   # Manual failure-recovery test plan
└── LICENSE
```

</details>

## Limitations and roadmap

**Known limitations**

- Scanned PDFs are not OCR'd (text-layer PDFs only). Upload page images (PNG or JPG) to use OCR.
- Pending web-search approvals are held in LangGraph's in-memory checkpointer, so they are lost on restart and not shared between workers.
- Web search uses DuckDuckGo through the `ddgs` library, which is best-effort. Voice input is English (`en-US`) and depends on browser support.
- Requires Chroma Cloud and AWS S3; there is no fully offline mode yet.
- Benchmarks use a small synthetic corpus (see [Evaluation](#evaluation)).

**Scaffolded, not yet enabled**

- An MCP server exposing the knowledge base to MCP clients (`backend/mcp/`).
- Server-side voice transcription with Whisper.
- An on-demand RAG quality scoring endpoint (Ragas-based).
- A knowledge-gap detector.

## Contributing

Contributions are welcome.

1. Fork the repo and create a branch: `git checkout -b feature/my-change`.
2. Run the checks that CI runs: `ruff check .` and `pytest` in `backend/`, `npm run lint` and `npm run build` in `frontend/`.
3. Open a pull request describing what changed and why. For larger changes, open an issue first.

Found a bug or have an idea? [Open an issue](https://github.com/shubhrato-badole/researchmind-ai/issues).

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Shubhrato Badole.

---

<div align="center">

Built by [Shubhrato Badole](https://github.com/shubhrato-badole)

</div>
