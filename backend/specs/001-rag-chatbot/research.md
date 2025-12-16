# Research Document: RAG Chatbot (Cohere + FastAPI + Qdrant + Neon)

**Feature**: 001-rag-chatbot
**Date**: 2025-12-12
**Status**: Complete

## Overview

This document consolidates research findings for implementing an AI-native RAG chatbot system using Cohere models, FastAPI backend, Qdrant vector database, and Neon Postgres. All technical unknowns from the specification have been resolved through best practices analysis and architectural patterns research.

---

## 1. Chunking Strategy for Book Content

### Decision
**Sliding window chunking with 100-token overlap, respecting sentence boundaries**

### Rationale
- Prevents information loss at chunk boundaries
- Maintains semantic coherence across splits
- Industry standard for RAG systems (LangChain, LlamaIndex)
- Cohere embed-english-v3.0 handles up to 512 tokens efficiently; 700-token chunks are within optimal range

### Implementation Details
```python
# Chunking parameters
MAX_CHUNK_TOKENS = 700
OVERLAP_TOKENS = 100
CHUNKING_METHOD = "sentence_boundary_aware"
```

- Split long sections into overlapping chunks
- Use sentence tokenizer to avoid mid-sentence cuts
- Store chunk relationships (previous/next chunk_id) in metadata for context expansion if needed

### Alternatives Considered
- Hard cutoff at 700 tokens: Rejected due to context loss at boundaries
- No overlap with adjacent chunk references: Rejected due to retrieval complexity
- Dynamic paragraph-based chunking: Rejected due to unpredictable chunk sizes

---

## 2. Cohere API Integration Best Practices

### Decision
**Use Cohere Python SDK v5+ with async client pattern and exponential backoff**

### Rationale
- Official SDK provides built-in retry logic and error handling
- Async support critical for FastAPI non-blocking I/O
- Cohere recommends exponential backoff for rate limit handling
- SDK handles API version management automatically

### Implementation Details
```python
# Dependencies
cohere==5.0.0  # Latest stable SDK

# Client initialization
from cohere import AsyncClient
client = AsyncClient(api_key=os.getenv("COHERE_API_KEY"))

# Retry configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # 1s, 2s, 4s
```

### Key Integration Points
- **Embeddings**: `client.embed()` with model="embed-english-v3.0", input_type="search_document"
- **Rerank**: `client.rerank()` with model="rerank-english-v3.0", top_n=3
- **Generation**: `client.chat()` with model="command-r-plus", grounded context

### Error Handling
- 429 (Rate Limit): Exponential backoff, queue request if retries fail
- 500 (Server Error): Retry with backoff
- 400 (Bad Request): Log and return structured error to user
- Timeout: 30s default, 60s for embedding batches

---

## 3. Qdrant Vector Database Architecture

### Decision
**Qdrant Cloud with single collection, cosine similarity, and payload filtering**

### Rationale
- Qdrant Cloud Free Tier: 1GB storage, sufficient for ~100k chunks
- Cosine similarity: Standard for Cohere embeddings (normalized vectors)
- Payload filtering: Enables chapter/section-based filtering without additional indices
- Managed service: No infrastructure overhead

### Implementation Details
```python
# Collection configuration
COLLECTION_NAME = "book_chunks"
VECTOR_SIZE = 1024  # Cohere embed-english-v3.0 dimensions
DISTANCE_METRIC = "Cosine"

# Search parameters
TOP_K = 4  # Retrieved before rerank
SIMILARITY_THRESHOLD = 0.7  # Filter low-relevance results
```

### Schema Design
```python
# Point payload structure
{
    "chunk_id": "uuid-string",
    "chapter_id": "ch01",
    "section_name": "1.1 Introduction",
    "content": "full chunk text",
    "token_count": 650,
    "created_at": "2025-12-12T10:00:00Z"
}
```

### Best Practices
- Use batch upsert (100 points per batch) for ingestion efficiency
- Enable indexing on payload fields (chapter_id, section_name) for filtering
- Implement health checks via `client.get_collection()` status
- Use unique chunk_id as Qdrant point ID for referential integrity

### Alternatives Considered
- Pinecone: Rejected due to higher cost and vendor lock-in
- Self-hosted Qdrant: Rejected for MVP (infrastructure complexity)
- Weaviate: Rejected due to less mature Python SDK

---

## 4. Neon Postgres Schema Design

### Decision
**Two-table schema with foreign key constraints and JSONB metadata storage**

### Rationale
- Separation of concerns: chapters vs. chunks
- Referential integrity ensures no orphaned chunks
- JSONB for flexible metadata (future extensibility)
- Neon Serverless: Auto-scaling, zero cold start

### Schema
```sql
CREATE TABLE chapters (
    chapter_id VARCHAR(50) PRIMARY KEY,
    chapter_title TEXT NOT NULL,
    total_chunks INTEGER DEFAULT 0,
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id VARCHAR(50) REFERENCES chapters(chapter_id) ON DELETE CASCADE,
    section_name TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding_id TEXT NOT NULL UNIQUE,  -- Qdrant point ID
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_chapter_chunks ON chunks(chapter_id);
CREATE INDEX idx_embedding_id ON chunks(embedding_id);
CREATE INDEX idx_created_at ON chunks(created_at DESC);
```

### Connection Pooling
```python
# psycopg3 async pool
from psycopg_pool import AsyncConnectionPool

pool = AsyncConnectionPool(
    conninfo=os.getenv("NEON_DB_URL"),
    min_size=5,
    max_size=20,
    timeout=30
)
```

### Best Practices
- Use prepared statements to prevent SQL injection
- Transaction boundaries: entire chapter ingestion as single transaction
- Periodic VACUUM ANALYZE for query performance
- Connection pool health checks via `pool.check()`

---

## 5. FastAPI Project Structure

### Decision
**Layered architecture: routers → services → clients, with Pydantic models**

### Rationale
- Clean separation of concerns
- Testable service layer (mocked clients)
- Pydantic v2 for automatic OpenAPI schema generation
- Middleware for logging, error handling, and rate limiting

### Directory Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI app + middleware
│   ├── config.py               # Settings (pydantic-settings)
│   ├── models/
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── services/
│   │   ├── embeddings.py       # Cohere embedding logic
│   │   ├── retrieval.py        # Qdrant search + rerank
│   │   ├── generation.py       # Cohere answer generation
│   │   └── ingestion.py        # Book content ingestion
│   ├── db/
│   │   ├── qdrant_client.py    # Qdrant connection singleton
│   │   ├── neon_client.py      # Postgres pool singleton
│   │   └── migrations/         # SQL migration scripts
│   └── routers/
│       ├── embed.py            # POST /embed
│       ├── query.py            # POST /query, POST /selected-query
│       └── health.py           # GET /health
├── tests/
│   ├── test_retrieval.py
│   ├── test_ingestion.py
│   └── test_grounding.py
├── pyproject.toml              # uv dependencies
├── .env.example
└── README.md
```

### Middleware Stack
```python
# Execution order (top = first executed)
1. CORSMiddleware (cross-origin requests)
2. RequestLoggingMiddleware (correlation ID, timing)
3. RateLimitMiddleware (100 req/min per IP)
4. ErrorHandlingMiddleware (structured JSON errors)
```

### Best Practices
- Use dependency injection for clients (testability)
- Async route handlers for I/O-bound operations
- Structured logging with correlation IDs
- OpenAPI tags for endpoint organization
- Versioned API routes (/api/v1/*)

---

## 6. RAG Pipeline Architecture

### Decision
**Three-stage pipeline: Retrieve → Rerank → Generate, with circuit breaker pattern**

### Rationale
- Standard RAG pattern (Lewis et al., 2020)
- Reranking improves relevance significantly (Cohere Rerank benchmarks)
- Circuit breaker prevents cascading failures
- Separate selected-text mode for context override

### Pipeline Flow

**Standard Mode (POST /query)**
```
User Query
    ↓
[1] Embed query (Cohere embed-english-v3.0)
    ↓
[2] Vector search (Qdrant top_k=4, cosine similarity)
    ↓
[3] Rerank chunks (Cohere Rerank top_n=3)
    ↓
[4] Fetch metadata from Neon (chapter_id, section_name)
    ↓
[5] Generate answer (Cohere Command-R-Plus with grounded context)
    ↓
[6] Return answer + citations
```

**Selected-Text Mode (POST /selected-query)**
```
User Query + Selected Text
    ↓
[1] Skip vector search (no embedding needed)
    ↓
[2] Validate selected_text (10-2000 tokens)
    ↓
[3] Generate answer (Cohere with selected_text as context)
    ↓
[4] Return answer (source="user_selection", no citations)
```

### Error Handling & Fallbacks
- **No chunks found (similarity < 0.7)**: Return transparency message
- **Qdrant unavailable**: 503 Service Unavailable, circuit breaker opens
- **Cohere rate limit**: Queue request, exponential backoff
- **Selected text too short**: 400 Bad Request with clear message

### Performance Optimizations
- Parallel Qdrant + Neon queries where possible
- Cache embeddings for common queries (optional, future)
- Batch processing for ingestion (100 chunks/batch)

---

## 7. Testing Strategy

### Decision
**Three-tier testing: unit, integration, and factuality benchmarks**

### Test Layers

**Unit Tests (pytest + pytest-asyncio)**
- Chunking logic (overlap, sentence boundaries)
- Pydantic model validation
- Utility functions (token counting, deduplication)
- Coverage target: 80%+

**Integration Tests**
- End-to-end API tests (TestClient)
- Qdrant + Neon integration (test containers)
- Cohere API mocking (httpx-mock)
- Test scenarios from spec acceptance criteria

**Factuality Benchmarks**
- Ground-truth Q&A dataset (50+ pairs from book content)
- Zero hallucination validation (100% traceability)
- Context override accuracy (98% threshold)
- Out-of-scope query handling (transparency message)

### Test Data
```
tests/fixtures/
├── sample_book.json        # Minimal book structure
├── ground_truth_qa.json    # Known Q&A pairs
└── out_of_scope_queries.json
```

### CI/CD Integration
- GitHub Actions: lint (ruff), type-check (mypy), test (pytest)
- Pre-commit hooks: formatting (black), import sorting (isort)
- Test coverage reporting (codecov)

---

## 8. Environment Configuration

### Decision
**Pydantic Settings with .env file, strict validation, and secret masking**

### Implementation
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Cohere
    cohere_api_key: str

    # Qdrant
    qdrant_url: str
    qdrant_api_key: str
    qdrant_cluster_id: str

    # Neon
    neon_db_url: str

    # App config
    log_level: str = "INFO"
    max_concurrent_requests: int = 100
    rate_limit_per_minute: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = False
```

### .env.example
```bash
# Cohere API
COHERE_API_KEY=your_cohere_api_key

# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_CLUSTER_ID=your-cluster-id

# Neon Postgres
NEON_DB_URL=postgresql://user:password@host/dbname

# Application
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=100
RATE_LIMIT_PER_MINUTE=100
```

### Security Best Practices
- Never commit .env to git (add to .gitignore)
- Use secret masking in logs (replace API keys with "***")
- Rotate API keys quarterly
- Use environment-specific configs (dev, staging, prod)

---

## 9. Deployment Architecture

### Decision
**Containerized FastAPI on cloud platform (Render/Railway/Fly.io) with managed services**

### Rationale
- Qdrant Cloud + Neon: Zero infrastructure management
- FastAPI container: Portable, scalable, easy rollback
- Platform auto-scaling: Handle traffic spikes
- Health checks: Built into platform (GET /health)

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv (fast Python package manager)
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Platform Choice (Recommendation: Render)
- **Render**: Free tier, auto-deploy from GitHub, built-in health checks
- **Railway**: Developer-friendly, generous free tier
- **Fly.io**: Global edge deployment, low latency

### Monitoring
- **Logs**: Structured JSON logs with correlation IDs
- **Metrics**: Prometheus-compatible endpoint (/metrics)
- **Alerts**: Platform-native uptime monitoring + Sentry for errors

---

## 10. Open Questions Resolution

### Q1: Multiple books support?
**Decision**: Single-book indexing for MVP
- Simplifies implementation (no book_id foreign key)
- Sufficient for initial textbook deployment
- Future: Add `books` table + `book_id` foreign key to chapters

### Q2: Expected book size?
**Decision**: Design for 10-15 chapters, ~1000-2000 chunks (~1.5M tokens)
- Qdrant Free Tier: 1GB storage = ~150k chunks (sufficient)
- Neon Free Tier: 0.5GB storage = millions of rows (sufficient)
- Ingestion time: ~5 minutes (100 chunks/min)

### Q3: Citations with page numbers?
**Decision**: chapter_id + section_name (no page numbers for MVP)
- Page numbers depend on ePub rendering (variable)
- Section names are stable identifiers
- Future: Add page_range to metadata if ePub provides it

### Q4: Conversation history?
**Decision**: Stateless queries for MVP
- Each query is independent (no context retention)
- Simplifies implementation (no session management)
- Future: Add conversation_id + history table for multi-turn dialogue

### Q5: Cohere rate limit behavior?
**Decision**: Exponential backoff (3 retries), then 429 response
- Better UX than queuing (user can retry manually)
- Prevents request pileup during sustained rate limiting
- Future: Implement request queue with user notification

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Backend Framework | FastAPI | 0.100+ | Async support, auto OpenAPI, Pydantic integration |
| Language | Python | 3.11+ | Type hints, async/await, Cohere SDK support |
| Vector Database | Qdrant Cloud | Latest | Free tier, cosine similarity, payload filtering |
| SQL Database | Neon Serverless Postgres | Latest | Auto-scaling, connection pooling, free tier |
| Embeddings | Cohere embed-english-v3.0 | - | 1024 dims, state-of-the-art retrieval |
| Reranker | Cohere Rerank v3 | - | Best-in-class reranking performance |
| Generator | Cohere Command-R-Plus | - | Grounded generation, citation support |
| Package Manager | uv | Latest | 10-100x faster than pip |
| Type Safety | Pydantic | v2 | Request/response validation, settings management |
| Testing | pytest + pytest-asyncio | Latest | Async test support, fixtures |
| Deployment | Docker + Render | - | Containerization, managed platform |

---

## Implementation Phases (Overview)

**Phase 0**: Research (this document) ✅
**Phase 1**: Data models, API contracts, quickstart
**Phase 2**: Task breakdown (not part of /sp.plan)
**Phase 3**: Implementation (TDD, red-green-refactor)
**Phase 4**: Integration testing + benchmarks
**Phase 5**: Deployment + monitoring

---

## References

- Cohere API Documentation: https://docs.cohere.com/
- Qdrant Documentation: https://qdrant.tech/documentation/
- Neon Documentation: https://neon.tech/docs/
- FastAPI Best Practices: https://fastapi.tiangolo.com/
- RAG Paper (Lewis et al., 2020): https://arxiv.org/abs/2005.11401

---

**Document Status**: Complete
**Next Step**: Generate data-model.md (Phase 1)
