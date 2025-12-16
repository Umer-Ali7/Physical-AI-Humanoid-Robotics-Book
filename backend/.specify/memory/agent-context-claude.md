# Agent Context: Claude Code

**Project**: RAG Chatbot (Physical AI Textbook)
**Last Updated**: 2025-12-12
**Agent Type**: Claude Sonnet 4.5

## Technology Stack

### Backend Framework
- **Python 3.11+**: Primary language with type hints
- **FastAPI 0.100+**: Async web framework with auto OpenAPI generation
- **Pydantic v2**: Request/response validation and settings management
- **uvicorn**: ASGI server for FastAPI

### Vector Database
- **Qdrant Cloud**: Free tier (1GB storage)
- **Collection**: `book_chunks` with 1024-dim vectors (Cohere embed-english-v3.0)
- **Distance Metric**: Cosine similarity
- **Client**: `qdrant-client` Python SDK

### SQL Database
- **Neon Serverless Postgres**: Free tier (0.5GB storage)
- **Driver**: psycopg3 with async connection pooling
- **Schema**: `chapters` and `chunks` tables with foreign key constraints

### AI Services (Cohere)
- **Embeddings**: Cohere embed-english-v3.0 (1024 dimensions)
- **Reranking**: Cohere Rerank v3 (refines top_k=4 to top_n=3)
- **Generation**: Cohere Command-R-Plus (grounded answer generation)
- **Client**: Cohere Python SDK v5+ with async support

### Package Management
- **uv**: Fast Python package manager (10-100x faster than pip)
- **pyproject.toml**: Project metadata and dependencies
- **uv.lock**: Locked dependency versions

### Development Tools
- **pytest + pytest-asyncio**: Async testing framework
- **ruff**: Fast Python linter
- **mypy**: Static type checker
- **black**: Code formatter
- **isort**: Import sorter

### Deployment
- **Docker**: Containerization (python:3.11-slim base)
- **Render/Railway/Fly.io**: Recommended platforms (free tier available)
- **Environment Variables**: Managed via Pydantic Settings

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Pydantic Settings (env vars)
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
│   ├── unit/
│   ├── integration/
│   └── benchmarks/
├── specs/
│   └── 001-rag-chatbot/
│       ├── spec.md
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── quickstart.md
│       └── contracts/
├── pyproject.toml
├── .env.example
└── README.md
```

## Key Design Patterns

### Dependency Injection
FastAPI dependency injection for database clients and services:
```python
from fastapi import Depends

async def get_qdrant_client() -> QdrantClient:
    return qdrant_client_singleton

@app.post("/query")
async def query(request: QueryRequest, client: QdrantClient = Depends(get_qdrant_client)):
    # ...
```

### Service Layer Pattern
Business logic isolated in service modules:
- `embeddings.py`: Chunking + embedding logic
- `retrieval.py`: Vector search + rerank orchestration
- `generation.py`: Answer generation with grounded context
- `ingestion.py`: End-to-end book content ingestion

### Repository Pattern (Minimal)
Database access abstracted via client singletons:
- `qdrant_client.py`: Manages Qdrant connection lifecycle
- `neon_client.py`: Manages Postgres connection pool

### Circuit Breaker (Future)
Planned for external service calls (Cohere, Qdrant) to prevent cascading failures.

## Configuration Management

### Environment Variables (via Pydantic Settings)
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cohere_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    qdrant_cluster_id: str
    neon_db_url: str
    log_level: str = "INFO"
    max_concurrent_requests: int = 100
    rate_limit_per_minute: int = 100

    class Config:
        env_file = ".env"
```

### Secrets Management
- **Local**: `.env` file (never committed to git)
- **Production**: Platform environment variables (Render/Railway dashboard)
- **Logging**: API keys masked in logs (replace with `***`)

## API Design Principles

### RESTful Conventions
- **Resource**: Chapters, chunks, queries
- **Methods**: GET (read), POST (create/query)
- **Versioning**: URL-based (`/api/v1/*`)

### Request/Response Format
- **Content-Type**: `application/json`
- **Validation**: Automatic via Pydantic models
- **Errors**: Structured JSON (`ErrorResponse` model)

### Error Handling
- **400 Bad Request**: Schema validation failures
- **429 Too Many Requests**: Rate limiting (app + Cohere API)
- **503 Service Unavailable**: External service failures (Qdrant, Neon)

## Testing Strategy

### Unit Tests
- **Scope**: Individual functions (chunking, token counting, validation)
- **Mocking**: External APIs (Cohere, Qdrant) via `pytest-mock`
- **Coverage Target**: 80%+

### Integration Tests
- **Scope**: End-to-end API tests (TestClient)
- **Database**: Test containers (Testcontainers-Python) or mocked clients
- **Fixtures**: Sample book data, ground-truth Q&A pairs

### Benchmarks
- **Factuality**: Zero hallucination validation (100% traceability)
- **Context Override**: Selected-text accuracy (98% threshold)
- **Out-of-Scope**: Transparency message validation (100%)

## Constitution Compliance

All implementation must align with `.specify/memory/constitution.md`:

### Principle I: Grounded Reasoning
- **Enforcement**: All answers traceable to retrieved chunks
- **Implementation**: `generation.py` includes chunk_ids in every response
- **Testing**: Automated fact-checking against ground-truth Q&A

### Principle II: Cohere-Native Alignment
- **Enforcement**: Cohere models for all AI operations
- **Implementation**: embed-english-v3.0, Rerank v3, Command-R-Plus
- **No Alternatives**: No OpenAI, Anthropic, or other providers

### Principle III: Context Prioritization
- **Enforcement**: User-selected text overrides vector search
- **Implementation**: POST /selected-query skips Qdrant entirely
- **Testing**: Verify `no_search_performed: true` in response

### Principle IV: Transparency
- **Enforcement**: Explicit out-of-scope messages
- **Implementation**: Return "This topic isn't mentioned..." when no chunks found
- **Testing**: Out-of-distribution query dataset

### Principle V: Academic Clarity
- **Enforcement**: Citations in every response
- **Implementation**: `citations` field with chapter_id, section_name, similarity_score
- **Testing**: Verify citation metadata completeness

## Performance Targets

- **POST /query**: <500ms at p95 (retrieval + generation)
- **POST /selected-query**: <300ms (no vector search)
- **POST /embed**: 100 chunks/minute (batch processing)
- **Qdrant search**: <100ms (separate from total latency)
- **Cohere Rerank**: <150ms for 4 chunks

## Known Constraints

### Free Tier Limits
- **Qdrant Cloud**: 1GB storage (~150k chunks)
- **Neon Postgres**: 0.5GB storage (millions of rows)
- **Cohere API**: 100 requests/minute (free tier)

### Technical Limits (Enforced)
- **Chunk Size**: Max 700 tokens
- **Query Length**: Max 500 tokens
- **Selected Text**: 10-2000 tokens
- **Response Length**: 50-500 words (default 200)
- **Retrieval Top-K**: 4 chunks from Qdrant
- **Rerank Top-N**: 3 chunks after Cohere Rerank

## Development Workflow

### Local Development
```bash
# Start server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Lint
ruff check app/

# Type check
mypy app/
```

### Pre-commit Hooks (Future)
- **black**: Code formatting
- **isort**: Import sorting
- **ruff**: Linting
- **mypy**: Type checking

### CI/CD (Future)
- **GitHub Actions**: Lint, test, type-check on every PR
- **Codecov**: Test coverage reporting
- **Schemathesis**: Contract testing from OpenAPI spec

## External API References

### Cohere API
- **Docs**: https://docs.cohere.com/
- **SDK**: https://github.com/cohere-ai/cohere-python
- **Rate Limits**: 100 req/min (free), 10k req/min (production)

### Qdrant
- **Docs**: https://qdrant.tech/documentation/
- **SDK**: https://github.com/qdrant/qdrant-client
- **Collections API**: https://qdrant.tech/documentation/concepts/collections/

### Neon
- **Docs**: https://neon.tech/docs/
- **Connection Pooling**: psycopg3 with AsyncConnectionPool
- **Migrations**: Manual SQL scripts in `app/db/migrations/`

## Common Patterns & Utilities

### Token Counting (Approximation)
```python
def estimate_token_count(text: str) -> int:
    """Approximate token count (1 token ≈ 4 characters)"""
    return len(text) // 4
```

### Chunking with Overlap
```python
def chunk_text(text: str, max_tokens: int = 700, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks, respecting sentence boundaries"""
    # Implementation in app/services/embeddings.py
```

### Deduplication
```python
import hashlib

def content_hash(text: str) -> str:
    """Generate SHA-256 hash for deduplication"""
    return hashlib.sha256(text.encode()).hexdigest()
```

## Troubleshooting Guide

### Issue: Qdrant Connection Timeout
- **Check**: `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
- **Test**: `curl -X GET "$QDRANT_URL/collections" -H "api-key: $QDRANT_API_KEY"`

### Issue: Neon Connection Failure
- **Check**: `NEON_DB_URL` format (must include password)
- **Test**: `psql $NEON_DB_URL -c "SELECT 1;"`

### Issue: Cohere Rate Limit (429)
- **Solution**: Exponential backoff (3 retries), then return error to user
- **Monitoring**: Log all rate limit events for quota planning

---

**Manual Additions Marker Begin**
<!-- Add custom agent context below this line; preserved across agent context updates -->

<!-- Manual Additions Marker End -->

---

**Note**: This file is automatically updated by `/sp.plan` workflow. Manual additions should be placed between the markers above.
