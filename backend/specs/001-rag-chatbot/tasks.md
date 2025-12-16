# Implementation Tasks: RAG Chatbot for AI-Native Textbook

**Feature**: 001-rag-chatbot
**Branch**: `001-rag-chatbot`
**Date**: 2025-12-12
**Generated from**: plan.md, spec.md, data-model.md, contracts/openapi.yaml

---

## Overview

This document breaks down the implementation of the RAG Chatbot into atomic, testable tasks organized by user story priority. Each task follows the format:

```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Legend**:
- `[P]` = Parallelizable (can run concurrently with other [P] tasks in same phase)
- `[US#]` = User Story number (US1, US2, US3, US4)
- No label = Sequential task (must complete before next task)

**User Stories** (from spec.md):
- **US1** (P1): Standard Question Answering from Book Content
- **US2** (P1): User-Selected Text Mode (Context Override)
- **US3** (P1): Book Content Ingestion and Embedding
- **US4** (P2): Health Check and System Monitoring

**MVP Scope**: US3 (Ingestion) + US1 (Standard Query) + US4 (Health Check)
**Extended MVP**: Add US2 (Selected-Text Mode)

---

## Phase 1: Project Setup & Infrastructure

**Goal**: Initialize project structure, dependencies, and foundational configuration

### Setup Tasks

- [x] T001 Create project directory structure per plan.md (backend/app/, backend/tests/, backend/scripts/)
- [x] T002 Initialize pyproject.toml with uv package manager and Python 3.11+ requirement
- [x] T003 [P] Add core dependencies to pyproject.toml: FastAPI 0.100+, Pydantic v2, uvicorn, python-dotenv
- [x] T004 [P] Add AI/ML dependencies to pyproject.toml: cohere==5.0.0, qdrant-client, psycopg[binary,pool]
- [x] T005 [P] Add dev dependencies to pyproject.toml: pytest, pytest-asyncio, pytest-mock, ruff, mypy, black
- [ ] T006 Run `uv sync` to install all dependencies and generate uv.lock
- [x] T007 Create .env.example with all required environment variables (COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY, NEON_DB_URL, etc.)
- [x] T008 Create .gitignore (include .env, __pycache__, .pytest_cache, .mypy_cache, .venv/)
- [x] T009 Create README.md with project overview and quick start reference to specs/001-rag-chatbot/quickstart.md

### Configuration Tasks

- [x] T010 Create app/config.py with Pydantic Settings for environment variable validation
- [x] T011 Add Settings model fields in app/config.py: cohere_api_key, qdrant_url, qdrant_api_key, neon_db_url, log_level, max_concurrent_requests, rate_limit_per_minute
- [x] T012 Add settings singleton instance in app/config.py with proper typing and secret masking for logs

**Phase 1 Completion Criteria**:
- ✅ Project structure matches plan.md
- ✅ All dependencies installed via `uv sync`
- ✅ .env.example contains all required variables
- ✅ app/config.py validates environment variables on import

---

## Phase 2: Foundational Components (Blocking Prerequisites)

**Goal**: Implement shared infrastructure needed by all user stories

### Database Connection Tasks

- [ ] T013 Create app/db/__init__.py as package marker
- [ ] T014 Implement Neon Postgres connection pool in app/db/neon_client.py using psycopg AsyncConnectionPool (min_size=5, max_size=20, timeout=30)
- [ ] T015 Add connection pool health check method in app/db/neon_client.py (reconnect on failure)
- [ ] T016 Implement Qdrant client singleton in app/db/qdrant_client.py with connection config (url, api_key from settings)
- [ ] T017 Add Qdrant collection initialization method in app/db/qdrant_client.py (collection_name="book_chunks", vector_size=1024, distance=Cosine)
- [ ] T018 Create app/db/migrations/001_initial_schema.sql with chapters and chunks table definitions per data-model.md
- [ ] T019 Add indexes to 001_initial_schema.sql: idx_chapter_chunks, idx_embedding_id, idx_created_at, idx_chapters_ingestion
- [ ] T020 Add database trigger in 001_initial_schema.sql to auto-update chapters.total_chunks on chunk insert/delete

### Pydantic Models Tasks

- [ ] T021 Create app/models/__init__.py and export all models
- [ ] T022 [P] Implement request models in app/models/requests.py: Section, Chapter, EmbedRequest per data-model.md
- [ ] T023 [P] Implement request models in app/models/requests.py: QueryRequest with query_text validation (max 500 tokens)
- [ ] T024 [P] Implement request models in app/models/requests.py: SelectedQueryRequest with selected_text validation (10-2000 tokens)
- [ ] T025 [P] Implement response models in app/models/responses.py: EmbedResponse, ChunkReference per data-model.md
- [ ] T026 [P] Implement response models in app/models/responses.py: QueryResponse with all fields (answer, citations, chunks_used, confidence_score, no_search_performed, source, selected_text_length)
- [ ] T027 [P] Implement response models in app/models/responses.py: HealthResponse, ErrorResponse

### Utility Functions Tasks

- [ ] T028 [P] Create app/utils/__init__.py
- [ ] T029 [P] Implement token counting utility in app/utils/text.py (estimate_token_count function using 1 token ≈ 4 chars approximation)
- [ ] T030 [P] Implement content hash utility in app/utils/crypto.py (SHA-256 hash for deduplication)
- [ ] T031 [P] Implement chunking utility in app/utils/chunking.py (sliding window with overlap, sentence-boundary-aware per research.md)

### FastAPI Application Setup

- [ ] T032 Create app/main.py with FastAPI() instance and app metadata (title, version, description)
- [ ] T033 Add CORS middleware to app/main.py (allow localhost for development)
- [ ] T034 Add logging middleware to app/main.py (structured JSON logs with correlation IDs)
- [ ] T035 Add error handling middleware to app/main.py (convert exceptions to ErrorResponse format)
- [ ] T036 Add rate limiting middleware to app/main.py (100 requests/minute per IP)
- [ ] T037 Create app routers package: app/routers/__init__.py
- [ ] T038 Include router imports in app/main.py (health, embed, query routers - to be created in user story phases)

**Phase 2 Completion Criteria**:
- ✅ Database clients (Qdrant + Neon) connect successfully
- ✅ All Pydantic models validate correctly (unit tests pass)
- ✅ Chunking utility correctly splits text with 100-token overlap
- ✅ FastAPI app starts without errors (`uvicorn app.main:app`)

---

## Phase 3: User Story 3 - Book Content Ingestion (P1)

**Goal**: Implement POST /embed endpoint for book content ingestion

**Why First**: Without ingestion, there's no knowledge base to query (blocks US1 and US2)

**Independent Test**: Call POST /embed with sample book JSON, verify chunks in Qdrant + metadata in Neon

### US3 Service Layer Tasks

- [ ] T039 [US3] Create app/services/__init__.py
- [ ] T040 [US3] Implement embedding service in app/services/embeddings.py with async Cohere client initialization
- [ ] T041 [US3] Add chunk_text method in app/services/embeddings.py using sliding window (700 tokens, 100 overlap) via app/utils/chunking.py
- [ ] T042 [US3] Add generate_embeddings method in app/services/embeddings.py (batch embedding via Cohere embed-english-v3.0, input_type="search_document")
- [ ] T043 [US3] Add exponential backoff retry logic in app/services/embeddings.py for Cohere API calls (max 3 retries, backoff factor 2)
- [ ] T044 [US3] Implement ingestion service in app/services/ingestion.py with orchestration logic (chunk → embed → store)
- [ ] T045 [US3] Add store_in_qdrant method in app/services/ingestion.py (batch upsert 100 points at a time)
- [ ] T046 [US3] Add store_metadata_in_neon method in app/services/ingestion.py (transactional INSERT into chapters + chunks tables)
- [ ] T047 [US3] Add deduplication logic in app/services/ingestion.py (check content hash before storing)
- [ ] T048 [US3] Add transaction rollback handling in app/services/ingestion.py (rollback Neon if Qdrant fails)

### US3 API Endpoint Tasks

- [ ] T049 [US3] Create app/routers/embed.py with POST /embed endpoint definition
- [ ] T050 [US3] Add request validation in app/routers/embed.py (EmbedRequest model)
- [ ] T051 [US3] Implement endpoint handler in app/routers/embed.py calling ingestion service
- [ ] T052 [US3] Add error handling in app/routers/embed.py (400 for validation errors, 500 for storage failures)
- [ ] T053 [US3] Add response timing in app/routers/embed.py (track ingestion_time_seconds)
- [ ] T054 [US3] Register embed router in app/main.py with /api/v1 prefix

### US3 Integration Testing Tasks

- [ ] T055 [US3] Create tests/integration/test_embed_endpoint.py
- [ ] T056 [US3] Add test case: valid book content ingestion returns 200 with correct chunk count
- [ ] T057 [US3] Add test case: malformed request (missing chapter_id) returns 400 with field error
- [ ] T058 [US3] Add test case: duplicate chunk ingestion skips duplicate (deduplication works)
- [ ] T059 [US3] Add test case: verify chunks stored in Qdrant with correct vector dimensions (1024)
- [ ] T060 [US3] Add test case: verify metadata stored in Neon with foreign key integrity

**Phase 3 Completion Criteria**:
- ✅ POST /embed accepts sample book JSON (3 chapters, 10 sections)
- ✅ Content chunked correctly (700 tokens max, 100 overlap)
- ✅ Embeddings generated via Cohere (1024-dim vectors)
- ✅ Chunks stored in Qdrant (batch upsert successful)
- ✅ Metadata stored in Neon (chapters + chunks tables populated)
- ✅ Deduplication prevents duplicate chunks
- ✅ Integration tests pass (5/5 scenarios)

**Parallel Execution Example** (US3):
- T040-T043 (embeddings.py) can run in parallel with T044-T048 (ingestion.py scaffolding)
- T056-T060 (integration tests) can run in parallel after T055 creates test file

---

## Phase 4: User Story 4 - Health Check (P2)

**Goal**: Implement GET /health endpoint for system monitoring

**Why Before US1/US2**: Enables verification that all services are connected before running queries

**Independent Test**: Call GET /health, verify connection status and chunk counts

### US4 Service Layer Tasks

- [ ] T061 [US4] Create app/services/health.py with health check service
- [ ] T062 [US4] Add check_qdrant_connection method in app/services/health.py (attempt collection info fetch)
- [ ] T063 [US4] Add check_neon_connection method in app/services/health.py (attempt simple SELECT 1 query)
- [ ] T064 [US4] Add get_total_chunks method in app/services/health.py (COUNT(*) from chunks table)
- [ ] T065 [US4] Add get_total_chapters method in app/services/health.py (COUNT(*) from chapters table)
- [ ] T066 [US4] Add get_uptime method in app/services/health.py (track startup time)

### US4 API Endpoint Tasks

- [ ] T067 [US4] Create app/routers/health.py with GET /health endpoint definition
- [ ] T068 [US4] Implement endpoint handler in app/routers/health.py calling health service methods
- [ ] T069 [US4] Add status determination logic in app/routers/health.py (healthy if both connected, degraded if one fails)
- [ ] T070 [US4] Return 200 for healthy, 503 for degraded in app/routers/health.py
- [ ] T071 [US4] Register health router in app/main.py with /api/v1 prefix

### US4 Integration Testing Tasks

- [ ] T072 [US4] Create tests/integration/test_health_endpoint.py
- [ ] T073 [US4] Add test case: all services running returns 200 with status="healthy"
- [ ] T074 [US4] Add test case: Qdrant unreachable returns 503 with qdrant_connected=false
- [ ] T075 [US4] Add test case: Neon unreachable returns 503 with neon_connected=false
- [ ] T076 [US4] Add test case: verify total_chunks_indexed matches database count after ingestion

**Phase 4 Completion Criteria**:
- ✅ GET /health returns connection status for Qdrant + Neon
- ✅ Returns accurate chunk/chapter counts
- ✅ Returns 503 when services degraded
- ✅ Integration tests pass (4/4 scenarios)

**Parallel Execution Example** (US4):
- T062-T066 (health service methods) can all run in parallel
- T073-T076 (integration tests) can run in parallel after T072 creates test file

---

## Phase 5: User Story 1 - Standard RAG Query (P1)

**Goal**: Implement POST /query endpoint for standard RAG retrieval

**Why Core MVP**: This is the primary use case (students asking questions about book content)

**Independent Test**: Ingest sample book, send query, verify grounded answer with citations

**Depends On**: US3 (needs book content indexed), US4 (health check for verification)

### US1 Service Layer Tasks

- [ ] T077 [US1] Create app/services/retrieval.py with retrieval service
- [ ] T078 [US1] Add search_vectors method in app/services/retrieval.py (Qdrant search with top_k=4, cosine similarity)
- [ ] T079 [US1] Add similarity threshold filter in app/services/retrieval.py (filter results < 0.7 similarity)
- [ ] T080 [US1] Add rerank_chunks method in app/services/retrieval.py (Cohere Rerank v3, refine top_k=4 to top_n=3)
- [ ] T081 [US1] Add exponential backoff for Cohere Rerank in app/services/retrieval.py (max 3 retries, backoff factor 2)
- [ ] T082 [US1] Add fetch_chunk_metadata method in app/services/retrieval.py (query Neon for chapter_id, section_name by chunk_ids)
- [ ] T083 [US1] Create app/services/generation.py with generation service
- [ ] T084 [US1] Add generate_answer method in app/services/generation.py (Cohere Command-R-Plus with grounded context)
- [ ] T085 [US1] Add grounded generation prompt template in app/services/generation.py (explicit instruction: only use provided context, cite sources)
- [ ] T086 [US1] Add transparency fallback in app/services/generation.py (return "This topic isn't mentioned..." if no chunks above threshold)
- [ ] T087 [US1] Add citation extraction in app/services/generation.py (build ChunkReference list from retrieved chunks)
- [ ] T088 [US1] Add max_words parameter handling in app/services/generation.py (limit response length 50-500 words)

### US1 API Endpoint Tasks

- [ ] T089 [US1] Create app/routers/query.py with POST /query endpoint definition
- [ ] T090 [US1] Add request validation in app/routers/query.py (QueryRequest model, token count < 500)
- [ ] T091 [US1] Implement query pipeline orchestration in app/routers/query.py: embed query → search → rerank → generate
- [ ] T092 [US1] Add error handling in app/routers/query.py (400 for invalid query, 503 for service failures)
- [ ] T093 [US1] Add confidence score calculation in app/routers/query.py (average similarity of top chunks)
- [ ] T094 [US1] Add query logging in app/routers/query.py (log query_text, chunks_retrieved, response_time)
- [ ] T095 [US1] Register query router in app/main.py with /api/v1 prefix

### US1 Integration Testing Tasks

- [ ] T096 [US1] Create tests/integration/test_query_endpoint.py
- [ ] T097 [US1] Add test case: valid query returns 200 with answer and citations
- [ ] T098 [US1] Add test case: out-of-scope query returns transparency message with empty citations
- [ ] T099 [US1] Add test case: query about indexed content returns confidence_score > 0.7
- [ ] T100 [US1] Add test case: verify top 3 chunks used after reranking (chunks_used length = 3)
- [ ] T101 [US1] Add test case: verify citations include chapter_id, section_name, chunk_id, similarity_score
- [ ] T102 [US1] Add test case: empty query_text returns 400 with validation error
- [ ] T103 [US1] Add test case: query > 500 tokens returns 400 with "Query too long" message

**Phase 5 Completion Criteria**:
- ✅ POST /query processes standard RAG pipeline (embed → search → rerank → generate)
- ✅ Returns grounded answer with citations for in-scope queries
- ✅ Returns transparency message for out-of-scope queries
- ✅ Reranking refines top_k=4 to top_n=3
- ✅ Response includes all metadata fields (answer, citations, chunks_used, confidence_score)
- ✅ Integration tests pass (7/7 scenarios)

**Parallel Execution Example** (US1):
- T077-T082 (retrieval.py) can run in parallel with T083-T088 (generation.py)
- T097-T103 (integration tests) can run in parallel after T096 creates test file

---

## Phase 6: User Story 2 - Selected-Text Mode (P1)

**Goal**: Implement POST /selected-query endpoint for context override

**Why Critical Differentiator**: Aligns with Constitution Principle III (Context Prioritization)

**Independent Test**: Send query with selected_text, verify answer uses ONLY selected text (no Qdrant search)

**Depends On**: US1 (reuses generation service)

### US2 Service Layer Tasks

- [ ] T104 [US2] Add generate_from_selected_text method in app/services/generation.py (bypass retrieval, use selected_text as sole context)
- [ ] T105 [US2] Add selected-text validation in app/services/generation.py (token count 10-2000)
- [ ] T106 [US2] Add insufficient context detection in app/services/generation.py (return "selected passage doesn't contain enough information" if answer confidence low)

### US2 API Endpoint Tasks

- [ ] T107 [US2] Add POST /selected-query endpoint definition in app/routers/query.py
- [ ] T108 [US2] Add request validation in app/routers/query.py (SelectedQueryRequest model)
- [ ] T109 [US2] Implement selected-query handler in app/routers/query.py (skip vector search, call generation service directly)
- [ ] T110 [US2] Add response metadata in app/routers/query.py (no_search_performed=true, source="user_selection", selected_text_length)
- [ ] T111 [US2] Add error handling in app/routers/query.py (400 for text too short/long)

### US2 Integration Testing Tasks

- [ ] T112 [US2] Create tests/integration/test_selected_query_endpoint.py
- [ ] T113 [US2] Add test case: valid selected_text returns answer with no_search_performed=true
- [ ] T114 [US2] Add test case: verify source="user_selection" in response
- [ ] T115 [US2] Add test case: selected_text < 10 tokens returns 400 with "too short" message
- [ ] T116 [US2] Add test case: selected_text > 2000 tokens returns 400 with "too long" message
- [ ] T117 [US2] Add test case: verify Qdrant logs show zero queries during selected-query request
- [ ] T118 [US2] Add test case: insufficient context in selected_text returns appropriate fallback message

**Phase 6 Completion Criteria**:
- ✅ POST /selected-query bypasses vector search entirely
- ✅ Returns answer based ONLY on selected_text
- ✅ Response metadata confirms no_search_performed=true and source="user_selection"
- ✅ Validation rejects selected_text outside 10-2000 token range
- ✅ Integration tests pass (6/6 scenarios)

**Parallel Execution Example** (US2):
- T104-T106 (generation.py extensions) can run in parallel
- T113-T118 (integration tests) can run in parallel after T112 creates test file

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Add production readiness features, documentation, and deployment artifacts

### Documentation Tasks

- [ ] T119 [P] Add docstrings to all service methods in app/services/ (Google-style docstrings)
- [ ] T120 [P] Add type hints to all functions in app/services/ (mypy --strict compliance)
- [ ] T121 [P] Update README.md with quick start instructions and link to quickstart.md
- [ ] T122 [P] Verify OpenAPI documentation is complete at /docs endpoint (all endpoints, schemas, examples)

### Error Handling & Logging Tasks

- [ ] T123 [P] Add structured error responses for all endpoints (use ErrorResponse model consistently)
- [ ] T124 [P] Add correlation IDs to all log entries in logging middleware
- [ ] T125 [P] Add request/response timing metrics in logging middleware
- [ ] T126 [P] Add Cohere API rate limit handling across all services (exponential backoff, return 429 if retries fail)

### Performance & Optimization Tasks

- [ ] T127 Verify Qdrant search completes in <100ms (add performance logging)
- [ ] T128 Verify Cohere Rerank completes in <150ms (add performance logging)
- [ ] T129 Verify end-to-end POST /query latency <500ms at p95 (load testing with 100 concurrent users)
- [ ] T130 Optimize Neon connection pool size based on load testing results

### Deployment Tasks

- [ ] T131 [P] Create Dockerfile with python:3.11-slim base image
- [ ] T132 [P] Add .dockerignore (exclude .env, __pycache__, .pytest_cache, tests/)
- [ ] T133 [P] Create scripts/init_qdrant.py for manual Qdrant collection creation
- [ ] T134 [P] Create scripts/seed_sample_data.py for ingesting sample book content
- [ ] T135 Add deployment instructions to README.md (Docker build, environment variables, platform setup)

### Code Quality Tasks

- [ ] T136 Run ruff linter on all app/ code and fix issues
- [ ] T137 Run mypy type checker on all app/ code and fix issues
- [ ] T138 Run black formatter on all app/ code
- [ ] T139 Add pre-commit hooks configuration (.pre-commit-config.yaml) for ruff, mypy, black

**Phase 7 Completion Criteria**:
- ✅ All code passes linting (ruff), type checking (mypy), formatting (black)
- ✅ All service methods have docstrings and type hints
- ✅ OpenAPI documentation is complete and accurate (/docs endpoint)
- ✅ Performance targets met (<500ms POST /query at p95)
- ✅ Dockerfile builds successfully and runs container
- ✅ Deployment documentation complete

**Parallel Execution Example** (Phase 7):
- T119-T122 (documentation) can all run in parallel
- T123-T126 (error handling) can all run in parallel
- T131-T135 (deployment) can all run in parallel
- T136-T139 (code quality) must run sequentially (fix issues before next tool)

---

## Dependencies & Execution Order

### User Story Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Foundational)
                      ↓
                  Phase 3 (US3: Ingestion) ──┬─→ Phase 4 (US4: Health Check)
                                               │
                                               └─→ Phase 5 (US1: Standard Query) → Phase 6 (US2: Selected-Text)
                                                                                         ↓
                                                                                   Phase 7 (Polish)
```

**Blocking Dependencies**:
- **US3 blocks US1**: Cannot query without indexed content
- **US1 blocks US2**: Selected-query reuses generation service from US1
- **US3 recommended before US4**: Health check more useful after ingestion (shows chunk counts)

**Independent Stories**:
- **US4** is independent (can be implemented in parallel with US1 if US3 is complete)

### Suggested Implementation Order

**MVP (3-5 days)**:
1. Phase 1 + Phase 2 (1 day): Setup + foundational components
2. Phase 3 (US3: Ingestion) (1 day): Enable book content loading
3. Phase 5 (US1: Standard Query) (1-2 days): Core RAG pipeline
4. Phase 4 (US4: Health Check) (0.5 day): Monitoring

**Extended MVP** (add 1 day):
5. Phase 6 (US2: Selected-Text) (1 day): Context override mode

**Production Ready** (add 1 day):
6. Phase 7 (Polish) (1 day): Documentation, deployment, code quality

### Parallel Execution Opportunities

**Phase 2 Foundational**:
- T022-T027 (Pydantic models) can run in parallel (6 files, independent)
- T028-T031 (Utility functions) can run in parallel (4 files, independent)

**Phase 3 (US3)**:
- T040-T043 (embeddings.py) || T044-T048 (ingestion.py scaffolding)
- T056-T060 (integration tests) can run in parallel after T055

**Phase 4 (US4)**:
- T062-T066 (health service methods) can run in parallel (6 methods, independent)
- T073-T076 (integration tests) can run in parallel after T072

**Phase 5 (US1)**:
- T077-T082 (retrieval.py) || T083-T088 (generation.py)
- T097-T103 (integration tests) can run in parallel after T096

**Phase 6 (US2)**:
- T113-T118 (integration tests) can run in parallel after T112

**Phase 7 (Polish)**:
- T119-T122 (documentation) can run in parallel
- T123-T126 (error handling) can run in parallel
- T131-T135 (deployment) can run in parallel

---

## Testing Strategy

**Note**: Integration tests are included for all user stories to verify acceptance criteria. Unit tests for utilities are recommended but not explicitly listed (can be added per TDD workflow).

**Test Coverage Targets**:
- Integration tests: 100% of acceptance scenarios from spec.md
- Unit tests (if added): 80%+ coverage of service layer
- Factuality benchmarks (future): Ground-truth Q&A dataset (95% factuality target)

**Test Data**:
- Sample book JSON (3 chapters, 10 sections) in tests/fixtures/sample_book.json
- Ground-truth Q&A pairs (future) in tests/fixtures/ground_truth_qa.json
- Out-of-scope queries (future) in tests/fixtures/out_of_scope_queries.json

---

## Task Summary

**Total Tasks**: 139

**By Phase**:
- Phase 1 (Setup): 12 tasks
- Phase 2 (Foundational): 26 tasks
- Phase 3 (US3 - Ingestion): 22 tasks
- Phase 4 (US4 - Health Check): 16 tasks
- Phase 5 (US1 - Standard Query): 27 tasks
- Phase 6 (US2 - Selected-Text): 15 tasks
- Phase 7 (Polish): 21 tasks

**By User Story**:
- US3 (Ingestion): 22 tasks
- US4 (Health Check): 16 tasks
- US1 (Standard Query): 27 tasks
- US2 (Selected-Text): 15 tasks
- Setup/Foundational/Polish: 59 tasks

**Parallelizable Tasks**: 48 tasks marked with [P]

**Estimated Effort**:
- MVP (Phases 1-2-3-5-4): 3-5 days (single developer)
- Extended MVP (add Phase 6): +1 day
- Production Ready (add Phase 7): +1 day
- **Total**: 5-7 days (single developer, full-time)

---

## Independent Test Criteria (Per User Story)

### US3 (Ingestion)
✅ **Can be tested independently**: Yes
**Test**: Call POST /embed with sample book JSON (3 chapters, 10 sections)
**Verify**:
- 200 response with total_chunks_created > 0
- Chunks stored in Qdrant (query collection info shows 1024-dim vectors)
- Metadata in Neon (SELECT COUNT(*) FROM chunks > 0)
- GET /health shows total_chunks_indexed matches ingested count

### US4 (Health Check)
✅ **Can be tested independently**: Yes
**Test**: Call GET /health before and after ingestion
**Verify**:
- 200 response with status="healthy"
- qdrant_connected=true, neon_connected=true
- total_chunks_indexed increases after ingestion

### US1 (Standard Query)
✅ **Can be tested independently**: Yes (after US3 ingestion)
**Test**: Ingest sample book, send POST /query with "What is transfer learning?"
**Verify**:
- 200 response with grounded answer
- citations array includes chapter_id, section_name, chunk_id
- chunks_used length = 3 (after reranking)
- confidence_score > 0.7

### US2 (Selected-Text)
✅ **Can be tested independently**: Yes
**Test**: Send POST /selected-query with selected_text and question
**Verify**:
- 200 response with answer
- no_search_performed=true
- source="user_selection"
- Qdrant logs show zero queries during request

---

## Implementation Strategy

**Recommended Approach**: Incremental delivery by user story

1. **Phase 1-2** (Setup + Foundational): Get infrastructure working
2. **Phase 3** (US3): Enable data ingestion → First testable increment
3. **Phase 5** (US1): Add standard query → Second testable increment (core MVP)
4. **Phase 4** (US4): Add health check → Production monitoring ready
5. **Phase 6** (US2): Add selected-text mode → Extended MVP (differentiator)
6. **Phase 7** (Polish): Production hardening

**Validation Gates** (after each phase):
- All integration tests pass for completed user stories
- Manual testing via Swagger UI (/docs) confirms expected behavior
- Performance targets met (query latency, ingestion speed)

---

## Next Steps

1. **Review and approve tasks.md**
2. **Begin Phase 1** (Setup): T001-T012
3. **TDD Workflow** (optional): Write failing tests before implementation (red-green-refactor)
4. **Track Progress**: Mark tasks complete with `[x]` as implemented
5. **Run Integration Tests**: After each user story phase
6. **Manual Testing**: Test all endpoints via Swagger UI (/docs)
7. **Performance Testing**: Verify <500ms latency after US1 complete
8. **Deploy MVP**: After Phases 1-5 complete (US3 + US1 + US4)

---

**Tasks Version**: 1.0.0
**Last Updated**: 2025-12-12
**Ready for Implementation**: ✅ Yes
