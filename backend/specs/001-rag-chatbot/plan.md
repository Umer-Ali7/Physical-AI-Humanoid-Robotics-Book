# Implementation Plan: RAG Chatbot for AI-Native Textbook

**Branch**: `001-rag-chatbot` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rag-chatbot/spec.md`

## Summary

Implement an end-to-end Retrieval-Augmented Generation (RAG) system for a Physical AI and Humanoid Robotics textbook. The system uses Cohere models (embed-english-v3.0, Rerank v3, Command-R-Plus) for grounded question answering with zero hallucinations. Key features include:

1. **Standard RAG Mode**: Vector search (Qdrant) → Rerank → Grounded generation with citations
2. **User-Selected-Text Mode**: Context override that bypasses vector search, answering only from highlighted text
3. **Zero Hallucination Guarantee**: All answers traceable to book chunks or explicit "not in book" message
4. **FastAPI Backend**: 4 endpoints (health, embed, query, selected-query) with OpenAPI documentation
5. **Dual Storage**: Qdrant (vectors) + Neon Postgres (metadata + citations)

**Technical Approach**: Python 3.11, FastAPI, async I/O, Pydantic validation, sliding window chunking (700 tokens, 100-token overlap), cosine similarity search, exponential backoff for API retries, structured logging with correlation IDs.

---

## Technical Context

**Language/Version**: Python 3.11+ (type hints, async/await, pattern matching)
**Primary Dependencies**: FastAPI 0.100+, Pydantic v2, Cohere SDK v5+, qdrant-client, psycopg3, uvicorn
**Storage**: Qdrant Cloud (vectors, 1GB free tier), Neon Serverless Postgres (metadata, 0.5GB free tier)
**Testing**: pytest + pytest-asyncio, pytest-mock, Testcontainers-Python (future), Schemathesis (contract testing)
**Target Platform**: Linux server (Render/Railway/Fly.io), Docker container (python:3.11-slim)
**Project Type**: Web backend (API-only, no frontend in this repo)
**Performance Goals**: <500ms p95 latency (POST /query), 100 chunks/min ingestion (POST /embed)
**Constraints**: <200ms retrieval from Qdrant, <150ms Cohere Rerank, 700 tokens/chunk max, 10-2000 tokens selected_text
**Scale/Scope**: 1000-2000 chunks (10-15 chapters), 100 concurrent users (MVP), stateless queries (no conversation history)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Grounded Reasoning
**Requirement**: All answers traceable to book content; zero hallucinations permitted.
**Implementation**:
- `generation.py`: Includes `chunks_used` (list of chunk_ids) in every response
- Similarity threshold (0.7): Filters low-confidence results
- Transparency fallback: "This topic isn't mentioned in the book sections I have access to."
- **Testing**: Automated fact-checking against ground-truth Q&A dataset (95% factuality target, SC-004)

**Status**: ✅ PASS — Design enforces traceability via chunk_ids + citations; out-of-scope queries return explicit message.

---

### ✅ Principle II: Cohere-Native Alignment
**Requirement**: Embeddings, reranking, and generation MUST use Cohere models (no alternatives).
**Implementation**:
- Embeddings: Cohere embed-english-v3.0 (1024 dims)
- Reranking: Cohere Rerank v3 (refines top_k=4 to top_n=3)
- Generation: Cohere Command-R-Plus (grounded, reasoning-focused)
- **No OpenAI, Anthropic, or other providers** (enforced in `config.py` and service layer)

**Status**: ✅ PASS — Tech stack locked to Cohere; no alternative providers considered.

---

### ✅ Principle III: Context Prioritization
**Requirement**: User-selected text MUST override global vector search results.
**Implementation**:
- Separate endpoint: POST /selected-query (bypasses Qdrant entirely)
- Logic in `query.py`: If `selected_text` provided, skip vector search, use text as sole context
- Response metadata: `no_search_performed: true`, `source: "user_selection"`
- **Testing**: Verify Qdrant logs show zero queries for POST /selected-query requests

**Status**: ✅ PASS — Selected-text mode implemented as distinct code path; vector search explicitly skipped.

---

### ✅ Principle IV: Transparency
**Requirement**: Explicit message when answer cannot be derived from book content.
**Implementation**:
- Similarity threshold filter (0.7): If top chunk < 0.7, return transparency message
- Hardcoded message: "This topic isn't mentioned in the book sections I have access to."
- Never fabricate content (enforced by grounded generation prompt)
- **Testing**: Out-of-distribution query dataset (100 queries about non-book topics, 100% transparency target)

**Status**: ✅ PASS — Transparency message hardcoded; no hallucination pathways in design.

---

### ✅ Principle V: Academic Clarity
**Requirement**: Responses suitable for intermediate tech learners; include citations.
**Implementation**:
- Default response length: 200 words (configurable 50-500 via `max_words` param)
- Citations: Every response includes `citations` array (chapter_id, section_name, chunk_id, similarity_score)
- Pedagogical tone: Enforced via Cohere generation prompt template
- **Testing**: Citation completeness (100% of responses with chunks_used have corresponding citations, SC-006)

**Status**: ✅ PASS — Citations included in response schema; response length configurable.

---

**Constitution Gate Result**: ✅ ALL PRINCIPLES SATISFIED — Proceed to implementation.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-rag-chatbot/
├── plan.md              # This file (/sp.plan command output)
├── spec.md              # Feature specification (input to /sp.plan)
├── research.md          # Phase 0 output (technical decisions)
├── data-model.md        # Phase 1 output (Postgres, Qdrant, Pydantic schemas)
├── quickstart.md        # Phase 1 output (setup guide)
├── contracts/           # Phase 1 output (OpenAPI spec)
│   ├── openapi.yaml
│   └── README.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

---

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                 # FastAPI app + middleware (CORS, logging, rate limit, errors)
│   ├── config.py               # Pydantic Settings (env var validation)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py         # Pydantic request models (EmbedRequest, QueryRequest, SelectedQueryRequest)
│   │   └── responses.py        # Pydantic response models (EmbedResponse, QueryResponse, HealthResponse, ErrorResponse)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embeddings.py       # Chunking logic + Cohere embedding (embed-english-v3.0)
│   │   ├── retrieval.py        # Qdrant search + Cohere Rerank orchestration
│   │   ├── generation.py       # Cohere Command-R-Plus answer generation with grounded context
│   │   └── ingestion.py        # End-to-end book content ingestion (chunk → embed → store)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py    # Qdrant connection singleton (collection management)
│   │   ├── neon_client.py      # Postgres pool singleton (AsyncConnectionPool)
│   │   └── migrations/
│   │       └── 001_initial_schema.sql  # CREATE TABLE chapters, chunks + indexes
│   └── routers/
│       ├── __init__.py
│       ├── embed.py            # POST /embed (ingestion endpoint)
│       ├── query.py            # POST /query, POST /selected-query (RAG endpoints)
│       └── health.py           # GET /health (monitoring)
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_chunking.py
│   │   ├── test_validation.py
│   │   └── test_utils.py
│   ├── integration/
│   │   ├── test_embed_endpoint.py
│   │   ├── test_query_endpoint.py
│   │   └── test_selected_query_endpoint.py
│   └── benchmarks/
│       ├── test_grounding.py       # Zero hallucination validation
│       ├── test_context_override.py # Selected-text accuracy
│       └── test_transparency.py    # Out-of-scope query handling
├── scripts/
│   ├── init_qdrant.py          # Create Qdrant collection (manual setup)
│   └── seed_sample_data.py     # Ingest sample book for testing
├── .specify/
│   ├── memory/
│   │   ├── constitution.md     # Project constitution (source of truth)
│   │   └── agent-context-claude.md  # Agent-specific context (auto-updated)
│   └── templates/              # (inherited from SpecKit Plus)
├── pyproject.toml              # uv dependencies (FastAPI, Cohere, Qdrant, psycopg3, pytest, etc.)
├── uv.lock                     # Locked dependency versions
├── .env.example                # Example environment variables
├── .gitignore
├── Dockerfile                  # Production container (python:3.11-slim)
└── README.md                   # Project overview + setup instructions
```

**Structure Decision**: Web backend (API-only) pattern selected. Frontend integration via JSON API (no UI in this repo). Separation of concerns: routers (HTTP layer) → services (business logic) → clients (external APIs/DBs). Async I/O throughout (FastAPI + async clients for Cohere, Qdrant, Neon).

---

## Complexity Tracking

**No constitution violations requiring justification.** All design decisions align with core principles.

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Dual storage (Qdrant + Neon) | Qdrant for vector search, Neon for structured metadata + citations | Single DB (Postgres with pgvector): Rejected due to limited vector search performance |
| Separate selected-query endpoint | Explicit separation enforces context prioritization (Principle III) | Single endpoint with mode param: Rejected for clarity (easier to audit no-search behavior) |
| Sliding window chunking (100-token overlap) | Prevents information loss at chunk boundaries | No overlap: Rejected due to semantic fragmentation |
| Cohere-only stack | Constitution requirement (Principle II) | Multi-model (OpenAI embeddings + Cohere rerank): Rejected as constitution violation |

---

## Phase 0: Research (Complete ✅)

**Output**: `specs/001-rag-chatbot/research.md`

**Resolved Unknowns**:
1. Chunking strategy → Sliding window, 100-token overlap, sentence-boundary-aware
2. Cohere API integration → Async client, exponential backoff, max 3 retries
3. Qdrant architecture → Single collection, cosine similarity, payload filtering
4. Neon schema design → Two-table schema (chapters, chunks), JSONB metadata
5. FastAPI structure → Layered (routers → services → clients)
6. RAG pipeline → Three-stage (Retrieve → Rerank → Generate)
7. Testing strategy → Three-tier (unit, integration, factuality benchmarks)
8. Environment config → Pydantic Settings, .env file, secret masking
9. Deployment → Docker + Render/Railway/Fly.io
10. Open questions → Single-book MVP, 1000-2000 chunks, no page numbers, stateless queries, exponential backoff for rate limits

**Key Decisions**:
- **Chunking**: 700 tokens max, 100-token overlap, respecting sentence boundaries
- **Qdrant**: Free tier (1GB), cosine similarity, batch upsert (100 points)
- **Neon**: Foreign key constraints, JSONB for extensibility, connection pooling (5-20 connections)
- **Cohere**: embed-english-v3.0 (1024 dims), Rerank v3 (top_n=3), Command-R-Plus (generation)
- **Testing**: pytest + pytest-asyncio, ground-truth Q&A dataset, 95% factuality target

---

## Phase 1: Design & Contracts (Complete ✅)

### 1.1 Data Model (`data-model.md`)

**Entities**:
1. **Chapter** (Postgres `chapters` table)
   - `chapter_id` (VARCHAR(50), PK): Pattern `^ch\d{2}$`
   - `chapter_title` (TEXT, NOT NULL)
   - `total_chunks` (INTEGER, DEFAULT 0): Auto-updated via trigger
   - `ingestion_timestamp` (TIMESTAMP, DEFAULT NOW())
   - `metadata` (JSONB): Extensible (author, version, tags)

2. **Chunk** (Postgres `chunks` table)
   - `chunk_id` (UUID, PK): Auto-generated
   - `chapter_id` (VARCHAR(50), FK): References `chapters.chapter_id` ON DELETE CASCADE
   - `section_name` (TEXT, NOT NULL): Section identifier (e.g., "1.1 What is AI?")
   - `content` (TEXT, NOT NULL): Full chunk text
   - `token_count` (INTEGER, NOT NULL): CHECK (1 <= token_count <= 700)
   - `embedding_id` (TEXT, NOT NULL, UNIQUE): Qdrant point ID (1:1 mapping)
   - `created_at` (TIMESTAMP, DEFAULT NOW())
   - `metadata` (JSONB): Extensible (overlap_with, page_range)

3. **Qdrant Point** (Collection: `book_chunks`)
   - `id` (UUID): Matches `chunks.embedding_id`
   - `vector` (float[]): 1024-dim embedding
   - `payload` (JSON): `{chunk_id, chapter_id, section_name, content, token_count, created_at}`

**Relationships**:
- One-to-Many: `chapters (1) ──< (M) chunks`
- One-to-One: `chunks.embedding_id (1:1) Qdrant point.id`

**Indexes**:
- Postgres: `idx_chapter_chunks` (chapter_id), `idx_embedding_id` (embedding_id), `idx_created_at` (created_at DESC)
- Qdrant: HNSW vector index, keyword indexes on `chapter_id`, `section_name`

---

### 1.2 API Contracts (`contracts/openapi.yaml`)

**Endpoints**:
1. **GET /health**
   - Response: `HealthResponse` (status, qdrant_connected, neon_connected, total_chunks_indexed, total_chapters, uptime_seconds)
   - Status Codes: 200 (healthy), 503 (degraded)

2. **POST /embed**
   - Request: `EmbedRequest` (chapters: [{chapter_id, chapter_title, sections: [{section_name, content}]}])
   - Response: `EmbedResponse` (status, total_chunks_created, total_chapters_processed, ingestion_time_seconds)
   - Status Codes: 200 (success), 400 (validation error), 500 (storage failure)

3. **POST /query**
   - Request: `QueryRequest` (query_text, max_words=200)
   - Response: `QueryResponse` (answer, citations, chunks_used, confidence_score, no_search_performed)
   - Status Codes: 200 (success or transparency message), 400 (invalid query), 503 (service unavailable)

4. **POST /selected-query**
   - Request: `SelectedQueryRequest` (query_text, selected_text, max_words=200)
   - Response: `QueryResponse` (answer, source="user_selection", no_search_performed=true, selected_text_length)
   - Status Codes: 200 (success), 400 (selected_text too short/long), 429 (rate limit)

**Validation Rules**:
- `chapter_id`: Pattern `^ch\d{2}$`
- `query_text`: 1-2000 chars, max 500 tokens
- `selected_text`: 40-8000 chars (approx. 10-2000 tokens)
- `max_words`: 50-500 (default 200)

---

### 1.3 Quickstart Guide (`quickstart.md`)

**Setup Steps**:
1. Clone repo, install dependencies (`uv sync`)
2. Configure `.env` (Cohere, Qdrant, Neon API keys)
3. Initialize databases (Neon schema, Qdrant collection)
4. Start FastAPI server (`uvicorn app.main:app --reload`)
5. Test health endpoint (`curl /health`)
6. Ingest sample book (`curl POST /embed`)
7. Test standard query (`curl POST /query`)
8. Test selected-query (`curl POST /selected-query`)
9. Test out-of-scope query (verify transparency message)
10. View Swagger UI (`http://localhost:8000/docs`)

**Estimated Time**: 15 minutes (assuming API accounts already created)

---

### 1.4 Agent Context (`agent-context-claude.md`)

**Technology Stack**: Python 3.11, FastAPI, Pydantic v2, Cohere SDK v5, qdrant-client, psycopg3, uv, pytest
**Project Structure**: Layered (routers → services → clients)
**Design Patterns**: Dependency injection, service layer, repository pattern (minimal)
**Configuration**: Pydantic Settings, `.env` file, secret masking
**Testing**: pytest + pytest-asyncio, ground-truth Q&A dataset, Schemathesis contract testing
**Constitution Compliance**: All 5 principles mapped to implementation details

---

## Phase 2: Implementation (Next Step — Use `/sp.tasks`)

**NOT PART OF /sp.plan OUTPUT.** Use `/sp.tasks` to generate `tasks.md` with:
- Task breakdown (atomic, testable tasks)
- Dependency graph (task execution order)
- Acceptance criteria (per task)
- Test cases (red-green-refactor)

**Suggested Task Categories** (for `/sp.tasks` reference):
1. **Database Setup**: Neon schema, Qdrant collection, connection singletons
2. **Core Services**: Chunking, embedding, retrieval, reranking, generation
3. **API Endpoints**: Health, embed, query, selected-query
4. **Middleware**: CORS, logging, rate limiting, error handling
5. **Testing**: Unit tests, integration tests, factuality benchmarks
6. **Deployment**: Dockerfile, environment config, platform setup

---

## Risk Analysis

### Risk 1: Cohere API Rate Limiting (Medium Impact, Medium Likelihood)
**Mitigation**:
- Exponential backoff (3 retries, backoff factor 2)
- Return 429 to user if retries exhausted
- Monitor rate limit events in logs
- **Future**: Implement request queue with user notification

### Risk 2: Qdrant Free Tier Exhaustion (Low Impact, Low Likelihood)
**Trigger**: Book exceeds 1000-2000 chunks (~1.5M tokens)
**Mitigation**:
- Track `total_chunks_indexed` via GET /health
- Alert when approaching 80% of 1GB limit
- Upgrade to Qdrant paid tier ($25/month) if needed
- **Alternative**: Implement chunk archival (remove old chapters)

### Risk 3: Neon Connection Pool Exhaustion (Medium Impact, Low Likelihood)
**Trigger**: >100 concurrent requests
**Mitigation**:
- Connection pool size: 5-20 (configured in `neon_client.py`)
- Health checks: Reconnect on pool failure
- Rate limiting: 100 req/min per IP (app-level)
- **Future**: Auto-scaling connection pool based on load

### Risk 4: Hallucination in Edge Cases (High Impact, Low Likelihood)
**Trigger**: Cohere model generates content not in retrieved chunks
**Mitigation**:
- Hardcode grounded generation prompt (explicit instruction: "Only use provided context")
- Post-generation validation: Check if answer contains chunk content
- Factuality benchmarks: 95% threshold (SC-004)
- **Monitoring**: Log all responses for manual review during MVP

### Risk 5: Selected-Text Too Short to Answer (Low Impact, High Likelihood)
**Trigger**: User highlights <10 tokens and asks complex question
**Mitigation**:
- Validation: Return 400 if `selected_text` <40 chars (~10 tokens)
- Graceful degradation: If generation produces "insufficient context", return that message
- User education: Frontend should warn users if selection is too short

---

## Deployment Strategy

### Local Development
```bash
# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v --cov=app

# Lint + type check
ruff check app/ && mypy app/
```

### Production (Render Recommended)
1. **Dockerfile** (already defined in project structure)
2. **Environment Variables**: Configure in Render dashboard (COHERE_API_KEY, QDRANT_URL, etc.)
3. **Health Check**: Render pings `GET /health` every 60s
4. **Auto-Deploy**: Trigger on git push to `main` branch
5. **Logs**: Structured JSON logs with correlation IDs (accessible via Render dashboard)
6. **Monitoring**: Sentry for errors, Prometheus metrics (future: `/metrics` endpoint)

**Estimated Deployment Time**: 10 minutes (first deployment), <5 minutes (subsequent)

---

## Success Metrics (from Spec)

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| SC-001: Zero hallucinations | 100% traceability | Automated fact-checking vs ground-truth Q&A |
| SC-002: Context override accuracy | 100% selected-text only | Verify `no_search_performed: true` in logs |
| SC-003: API latency (p95) | <500ms | Load testing with 100 concurrent users |
| SC-004: RAG factuality | ≥95% | Ground-truth Q&A dataset evaluation |
| SC-005: Ingestion speed | 1000+ chunks in <5min | Timing POST /embed with full book |
| SC-006: Citation completeness | 100% valid citations | Verify `citations` array in all responses |
| SC-007: Out-of-scope transparency | 100% | Test with 100 out-of-distribution queries |
| SC-008: Frontend integration ready | Clean JSON | Validate with example React component |
| SC-009: Concurrent query handling | 100 concurrent users | Load testing (no degradation) |
| SC-010: OpenAPI documentation | 100% coverage | Swagger UI validates all endpoints |

---

## Next Steps

1. **Review and approve this plan** (`specs/001-rag-chatbot/plan.md`)
2. **Run `/sp.tasks`** to generate atomic task breakdown (`specs/001-rag-chatbot/tasks.md`)
3. **Begin implementation** (TDD: red-green-refactor cycle)
4. **Run factuality benchmarks** after MVP completion
5. **Deploy to staging** (Render free tier) for integration testing
6. **Create ADR** for Cohere + Qdrant + Neon stack selection (if desired)

---

## Architectural Decision Record (ADR) Suggestions

📋 **Architectural decision detected: Cohere-exclusive AI stack (embeddings, rerank, generation)**
**Impact**: Long-term vendor lock-in to Cohere API; no fallback to OpenAI or Anthropic.
**Alternatives considered**:
- Multi-model (OpenAI embeddings + Cohere rerank): Rejected (Constitution Principle II)
- Anthropic Claude for generation: Rejected (Constitution Principle II)
**Tradeoffs**:
- ✅ Pro: Consistent API, optimized reranking, constitution compliance
- ❌ Con: Vendor lock-in, rate limit dependency, no A/B testing with other models
**Decision**: Accept vendor lock-in as constitution requirement.

**Document reasoning and tradeoffs?** Run `/sp.adr Cohere-Exclusive-AI-Stack`

---

📋 **Architectural decision detected: Dual storage (Qdrant + Neon) instead of single DB**
**Impact**: Two external dependencies (higher failure modes), additional sync logic.
**Alternatives considered**:
- Single Postgres with pgvector: Rejected (vector search performance <100ms not guaranteed)
- Qdrant-only (no SQL): Rejected (complex metadata queries difficult)
**Tradeoffs**:
- ✅ Pro: Qdrant optimized for vector search (<100ms), Neon optimized for relational queries
- ❌ Con: Two connection pools, sync complexity, cross-system consistency risk
**Decision**: Accept dual storage for performance optimization.

**Document reasoning and tradeoffs?** Run `/sp.adr Dual-Storage-Qdrant-Neon`

---

**Implementation Plan Status**: ✅ COMPLETE
**Branch**: `001-rag-chatbot`
**Next Command**: `/sp.tasks` (generate task breakdown)
**Estimated Implementation Time**: 3-5 days (single developer, full-time)

---

**Plan Version**: 1.0.0
**Last Updated**: 2025-12-12
**Approved By**: [Pending Review]
