# RAG Architecture Comparison Platform

A full-stack platform for comparing four Retrieval-Augmented Generation (RAG) architectures against the same knowledge sources.

## Project Overview

This application lets you:

- Add knowledge from pasted text or YouTube transcripts
- Ask questions in Chat using Naive RAG
- Compare **Naive**, **Hybrid**, **Agentic**, and **GraphRAG** side by side on the same question and sources
- Run benchmark evaluation with retrieval metrics

## RAG Architectures

### Naive RAG

```
Question → Dense vector search (ChromaDB) → Top-K chunks → LLM answer
```

- Embeds the question and searches ChromaDB by vector similarity
- Returns top-K chunks above a minimum score threshold
- Generates a source-grounded answer from retrieved context

### Hybrid RAG

```
Question → Dense search + BM25 → Reciprocal Rank Fusion → Reranker → LLM answer
```

- Combines semantic and keyword retrieval over the same chunks
- RRF fusion merges ranked lists
- Lightweight composite reranker
- Returns dense/BM25/fused/reranked ranks per chunk

### Agentic RAG

```
Question → Hybrid retrieve → Grade evidence → Rewrite query (if needed) → Retry (max 3)
```

- Controlled self-correcting workflow (not an unrestricted agent)
- Evidence grader scores retrieved chunks (threshold: 0.55)
- Query rewriter improves retrieval queries only (original question unchanged)
- Returns execution trace with attempts, confidence, and decisions

### GraphRAG

```
Question → Extract entities → Match graph nodes → Traverse (2 hops) → Supporting chunks → LLM answer
```

- Entity/relationship extraction on ingestion
- NetworkX graph with JSON persistence
- Nodes and edges reference supporting chunk IDs
- Returns matched entities, relationships, paths, and hop count

## Main Features

### Sources

- Pasted text (`POST /api/lectures/`)
- YouTube transcripts (`POST /api/lectures/youtube`)
- Source deletion removes data from database, ChromaDB, BM25 corpus, and graph

**Important:** Adding a source saves text to SQLite, but RAG also requires **embedding** into ChromaDB. If embedding fails (invalid API key, quota exceeded), sources appear in the UI but queries return no results until you re-index.

### Compare (Main Feature)

`POST /api/compare`

```json
{
  "question": "Explain recursion",
  "source_ids": ["1"],
  "pipelines": ["naive", "hybrid", "agentic", "graph"]
}
```

Runs all pipelines concurrently. A failure in one pipeline does not crash the comparison.

### Evaluation

`POST /api/evaluation/run`

Benchmarks all pipelines against a fixed dataset with ground-truth chunk IDs.

**Retrieval metrics** (only where ground truth exists):
- Hit Rate@K
- Precision@K
- Recall@K
- MRR
- NDCG@K

**Operational metrics:**
- Average latency
- Average token usage

Generation quality metrics are not fabricated. They require model-judged evaluation and are not included by default.

## Tech Stack

### Backend

- FastAPI
- SQLAlchemy (SQLite default, PostgreSQL supported)
- ChromaDB
- Multi-provider LLM support (OpenAI, Gemini, Grok, Ollama, OpenAI-compatible APIs)
- NetworkX (knowledge graph)
- faster-whisper (speech-to-text)
- youtube-transcript-api

### Frontend

- React 18
- Vite
- Tailwind CSS
- lucide-react

## LLM Provider Support

The platform supports multiple LLM and embedding providers via `backend/.env`. You need a **valid API key** for both **embeddings** (indexing + search) and **chat** (answer generation).

| Provider | `LLM_PROVIDER` | API key variable | Default chat model | Default embedding model |
|----------|----------------|------------------|--------------------|-------------------------|
| OpenAI | `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` | `text-embedding-3-small` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` | `gemini-3.6-flash` | `models/gemini-embedding-001` |
| Grok (xAI) | `grok` | `GROK_API_KEY` | `grok-2-latest` | OpenAI-compatible endpoint |
| Ollama (local) | `ollama` | `LLM_API_KEY` | `llama3.2` | `nomic-embed-text` |
| Any OpenAI-compatible API | `openai_compatible` | `LLM_API_KEY` | configurable | configurable |

You can use different providers for chat and embeddings:

```env
LLM_PROVIDER=grok
GROK_API_KEY=your_grok_key

EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
```

**Do not put a Gemini key in `OPENAI_API_KEY`.** Use the variable that matches your provider.

Copy `backend/.env.example` to `backend/.env` and fill in your keys.

### Example: Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Optional — use a lighter model for higher free-tier limits
# LLM_MODEL=gemini-2.0-flash-lite

DATABASE_URL=sqlite:///./virtual_teacher.db
```

Get a Gemini key from [Google AI Studio](https://aistudio.google.com/apikey).

### Example: OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_openai_key_here

DATABASE_URL=sqlite:///./rag_platform.db
```

### Example: Grok

```env
LLM_PROVIDER=grok
GROK_API_KEY=your_grok_key_here
GROK_BASE_URL=https://api.x.ai/v1

# Grok has no embedding API — use Gemini or OpenAI for embeddings
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key_here
```

## Environment Variables

Full `backend/.env` reference:

```env
# Provider selection
LLM_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini

# API keys (set the one matching LLM_PROVIDER)
OPENAI_API_KEY=put_your_openai_api_key_here
GEMINI_API_KEY=put_your_gemini_api_key_here
GROK_API_KEY=put_your_grok_api_key_here
LLM_API_KEY=put_your_generic_api_key_here

# Optional model overrides
# LLM_MODEL=gemini-2.0-flash-lite
# EMBEDDING_MODEL=models/gemini-embedding-001

# OpenAI-compatible endpoints
GROK_BASE_URL=https://api.x.ai/v1
OLLAMA_BASE_URL=http://localhost:11434/v1
OPENAI_COMPATIBLE_BASE_URL=

DATABASE_URL=sqlite:///./virtual_teacher.db
ELEVENLABS_API_KEY=put_your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=put_your_elevenlabs_voice_id_here
```

For PostgreSQL, set `DATABASE_URL` to a PostgreSQL connection string.

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Configure `backend/.env`, then test your provider:

```bash
python scripts/test_llm_connect.py
```

### Frontend

```bash
cd frontend
npm install
```

## Running the App

You need **two terminals** running at the same time. Re-indexing scripts do **not** start the website.

### Terminal 1 — Backend (API)

```bash
cd backend
# activate your virtual environment / conda env first
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Wait for: `Uvicorn running on http://127.0.0.1:8000`

- API docs: http://localhost:8000/docs

### Terminal 2 — Frontend (UI)

```bash
cd frontend
npm run dev
```

Wait for: `Local: http://localhost:3000/` (or `3001` if port 3000 is busy)

- App UI: http://localhost:3000

**Restart the backend** after changing `backend/.env`.

## Indexing Sources

After adding sources or switching LLM/embedding providers, re-index all sources:

```bash
cd backend
python scripts/reindex_all_sources.py
```

Check indexing and retrieval status:

```bash
python scripts/check_rag_status.py
```

You should see `ChromaDB chunks: 20+` (not `0`).

Switching embedding providers creates a separate ChromaDB collection (`knowledge_sources_<provider>`), so re-indexing is required.

## Diagnostic Scripts

| Script | Purpose |
|--------|---------|
| `scripts/test_llm_connect.py` | Test chat + embedding API for configured provider |
| `scripts/check_rag_status.py` | Compare SQLite source count vs ChromaDB chunk count |
| `scripts/reindex_all_sources.py` | Re-embed all sources into ChromaDB and rebuild graph |
| `scripts/system_check.py` | Check directories, provider config, and database |

## Docker

```bash
cd docker
docker-compose up --build
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/qa/ask` | Chat Q&A (Naive RAG) |
| `POST /api/query` | Query with pipeline selection |
| `POST /api/compare` | Compare multiple RAG architectures |
| `POST /api/evaluation/run` | Run benchmark evaluation |
| `POST /api/lectures/` | Add text source |
| `POST /api/lectures/youtube` | Import YouTube transcript |
| `GET /api/lectures/` | List sources |
| `DELETE /api/lectures/{id}` | Delete source from all stores |

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend production build
cd frontend
npm run build
```

## Troubleshooting

### "No relevant information was found in the provided sources"

This means **no chunks were retrieved**, not that your text is missing from the app.

Common causes:

1. **ChromaDB is empty** — sources saved to SQLite but never embedded. Run `python scripts/reindex_all_sources.py`.
2. **Invalid API key** — embedding failed during indexing. Fix the key in `.env` and re-index.
3. **Wrong key variable** — e.g. Gemini key in `OPENAI_API_KEY` instead of `GEMINI_API_KEY` with `LLM_PROVIDER=gemini`.

### 429 quota exceeded (Gemini / OpenAI)

```
429 You exceeded your current quota...
```

The free tier has daily/minute limits. Compare runs **4 pipelines at once**, each calling the LLM.

**Fixes:**
- Wait for quota reset (usually daily)
- Use a lighter model: `LLM_MODEL=gemini-2.0-flash-lite` in `.env`
- Enable billing on your API provider account
- Test one pipeline at a time instead of full Compare

### Naive / Hybrid show 0 chunks but Agentic finds chunks

Naive and Hybrid rely on **vector embedding** for the query (API call). Agentic's hybrid retriever can still find chunks via **BM25 keyword search** when the embedding API fails. This is expected when quota is hit.

### Agentic: chunks found but no answer

Agentic requires evidence confidence **≥ 0.55** before generating an answer. If all attempts score below that, you get:

> "There is not enough information in the selected sources to answer this question."

Even when chunks look relevant. The grader may also fall back to a weaker heuristic score if the LLM grader hits quota limits.

### GraphRAG: 0 chunks / matched wrong entity

GraphRAG uses **heuristic entity extraction**, not semantic search. For "Explain recursion" it may match **"Explain"** (capitalized word) instead of **"Recursion"**, finding no graph nodes.

This is a known limitation of the lightweight graph extractor.

### Compare table shows zeros

| Metric | Meaning when zero |
|--------|-------------------|
| Chunks considered | Retrieval found nothing or failed |
| Chunks sent to LLM | No text passed to the LLM for answer generation |
| Generation time | LLM was never called |
| Tokens | No LLM call occurred |
| Citations | No answer produced |

### Re-index does not start the app

`reindex_all_sources.py` only embeds data. You still need **backend + frontend** running separately (see [Running the App](#running-the-app)).

## Known Limitations

- Graph extraction uses lightweight heuristics, not a dedicated NER/RE model
- BM25 index is rebuilt from ChromaDB chunks on each hybrid query
- Evaluation dataset is small and requires matching source/chunk IDs in your indexed data
- Chat uses Naive RAG only; use Compare for multi-architecture queries
- Document upload (PDF/DOC) is not yet implemented
- Legacy LangChain files (`vector_store.py`, `embeddings.py`) remain but are unused
- Gemini free tier has strict rate limits; Compare can exhaust daily quota quickly
- Agentic RAG may refuse to answer if evidence confidence stays below 0.55

## Architecture Diagram

```
Sources (text / YouTube)
    → Chunking
    → ChromaDB (vectors via configured embedding provider)
    → BM25 corpus (from same chunks)
    → Knowledge graph (entities + relationships)

Compare API
    → NaiveRAGPipeline
    → HybridRAGPipeline
    → AgenticRAGPipeline
    → GraphRAGPipeline
    → Normalized RAGResult per pipeline
```
