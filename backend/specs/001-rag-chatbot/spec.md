# Feature Specification: RAG Chatbot for AI-Native Textbook

**Feature Branch**: `001-rag-chatbot`
**Created**: 2025-12-12
**Status**: Draft
**Input**: User description: "RAG Chatbot (Cohere + FastAPI + Qdrant + Neon) with grounded retrieval, user-selected-text mode, and zero hallucinations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Standard Question Answering from Book Content (Priority: P1)

A student reading the AI textbook wants to ask a question about a concept they don't fully understand. They open the embedded chatbot, type their question, and receive an answer that is grounded in the book's content with citations to the specific chapter/section.

**Why this priority**: This is the core MVP functionality. Without this, the chatbot has no purpose. This delivers immediate value by allowing students to query the book's knowledge base conversationally.

**Independent Test**: Can be fully tested by indexing sample chapters, sending queries via POST /query endpoint, and verifying responses are grounded with proper citations. Delivers value as a standalone Q&A assistant.

**Acceptance Scenarios**:

1. **Given** the book content is indexed in Qdrant, **When** a user asks "What is transfer learning?", **Then** the system retrieves relevant chunks, reranks them, and returns an answer citing the chapter/section where transfer learning is explained
2. **Given** the book content is indexed, **When** a user asks about a topic not covered in the book, **Then** the system responds with "This topic isn't mentioned in the book sections I have access to."
3. **Given** a query is submitted, **When** the RAG pipeline executes, **Then** the response includes metadata fields: answer, citations (chapter_id, section_name, page), chunks_used, confidence_score
4. **Given** multiple relevant sections exist, **When** a query matches them, **Then** the system reranks using Cohere Rerank and returns the top 3 most relevant chunks as context

---

### User Story 2 - User-Selected Text Mode (Context Override) (Priority: P1)

A student is reading a specific paragraph in the book and highlights the text. They click "Ask about this section" and the chatbot answers based ONLY on the selected text, ignoring global search, ensuring perfect alignment with what they're reading.

**Why this priority**: This is a critical differentiator and aligns with Constitution Principle III (Context Prioritization). Without this, the chatbot might give answers from other chapters, confusing the student. This must be in the MVP.

**Independent Test**: Can be fully tested by sending POST /selected-query with user-provided text and verifying the response is grounded ONLY in that text (no vector search performed). Delivers value as a context-aware assistant.

**Acceptance Scenarios**:

1. **Given** a user selects text "Gradient descent is an optimization algorithm...", **When** they ask "How does this algorithm work?", **Then** the system answers using ONLY the selected text as context (no Qdrant search)
2. **Given** the selected text doesn't contain enough information to answer, **When** the user asks a question, **Then** the system responds "The selected passage doesn't contain enough information to answer this question."
3. **Given** selected text is provided, **When** POST /selected-query is called, **Then** the response includes metadata: answer, source="user_selection", selected_text_length, no_search_performed=true

---

### User Story 3 - Book Content Ingestion and Embedding (Priority: P1)

An administrator or automated pipeline needs to ingest the full book content (chapters, sections, paragraphs) into the system. The content is chunked, embedded using Cohere embed-english-v3.0, stored in Qdrant, and metadata is persisted in Neon Postgres.

**Why this priority**: Without ingestion, there's no knowledge base to query. This is foundational infrastructure that must exist before any queries can work.

**Independent Test**: Can be fully tested by calling POST /embed with sample book data, verifying embeddings are stored in Qdrant, metadata is in Postgres, and GET /health confirms system readiness.

**Acceptance Scenarios**:

1. **Given** structured book content (JSON with chapters/sections/paragraphs), **When** POST /embed is called, **Then** content is chunked into max 700-token segments, embedded via Cohere, and stored in Qdrant with unique chunk IDs
2. **Given** embeddings are created, **When** metadata is stored, **Then** Neon Postgres contains: chapter_id, section_name, chunk_id, token_count, embedding_id (Qdrant reference)
3. **Given** ingestion completes, **When** GET /health is called, **Then** response includes: qdrant_status="connected", neon_status="connected", total_chunks_indexed, total_chapters

---

### User Story 4 - Health Check and System Monitoring (Priority: P2)

DevOps or monitoring systems need to verify the RAG chatbot backend is operational. They call GET /health to check Qdrant connection, Neon connection, and API readiness.

**Why this priority**: Important for production reliability but not required for initial MVP testing. Can be added after core retrieval works.

**Independent Test**: Can be fully tested by calling GET /health and verifying status codes and connection checks without requiring full book ingestion.

**Acceptance Scenarios**:

1. **Given** all services are running, **When** GET /health is called, **Then** response returns 200 with status: "healthy", qdrant_connected: true, neon_connected: true
2. **Given** Qdrant is unreachable, **When** GET /health is called, **Then** response returns 503 with status: "degraded", qdrant_connected: false
3. **Given** Neon is unreachable, **When** GET /health is called, **Then** response returns 503 with status: "degraded", neon_connected: false

---

### Edge Cases

- **Empty query**: What happens when a user submits an empty string? System should return 400 Bad Request with clear error message.
- **Very long query**: What happens when a query exceeds reasonable token limits (e.g., >500 tokens)? System should truncate or return 400 with message "Query too long (max 500 tokens)".
- **No relevant chunks found**: What happens when vector search returns no results above similarity threshold? System should respond "This topic isn't mentioned in the book sections I have access to."
- **Selected text too short**: What happens when user selects <10 tokens? System should return error: "Selected text too short to provide meaningful context (min 10 tokens)."
- **Qdrant unavailable during query**: System should return 503 Service Unavailable with message "Vector search temporarily unavailable. Please try again."
- **Cohere API rate limit**: System should implement exponential backoff and return 429 Too Many Requests if retries fail.
- **Malformed book data during ingestion**: System should validate schema and return 400 with specific field errors (e.g., "Missing required field: chapter_id").
- **Duplicate chunk ingestion**: System should deduplicate based on content hash to avoid storing identical chunks multiple times.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST embed book content using Cohere embed-english-v3.0 and store vectors in Qdrant Cloud
- **FR-002**: System MUST store metadata (chapter_id, section_name, chunk_id, token_count) in Neon Serverless Postgres with referential integrity
- **FR-003**: System MUST provide standard RAG retrieval mode: query → Qdrant vector search (top_k=4) → Cohere Rerank (top_n=3) → Cohere generate with citations
- **FR-004**: System MUST provide user-selected-text mode: bypass vector search, use only provided text as context, generate answer with Cohere
- **FR-005**: System MUST chunk book content into max 700-token segments with overlap for context continuity
- **FR-006**: System MUST rerank retrieved chunks using Cohere Rerank v3 before final generation
- **FR-007**: System MUST include citations in every response: chapter_id, section_name, chunk_ids used
- **FR-008**: System MUST respond "This topic isn't mentioned in the book sections I have access to." when no relevant content is found (Constitution Principle IV: Transparency)
- **FR-009**: System MUST refuse to answer questions outside book scope, never hallucinating content (Constitution Principle I: Grounded Reasoning)
- **FR-010**: System MUST prioritize user-selected text over global search when both are provided (Constitution Principle III: Context Prioritization)
- **FR-011**: System MUST expose POST /embed endpoint for book ingestion (accepts JSON with chapters/sections/content)
- **FR-012**: System MUST expose POST /query endpoint for standard RAG retrieval (accepts question, returns answer + citations)
- **FR-013**: System MUST expose POST /selected-query endpoint for context-override mode (accepts question + selected_text)
- **FR-014**: System MUST expose GET /health endpoint for monitoring (returns Qdrant/Neon connection status)
- **FR-015**: System MUST use connection pooling for Neon Postgres to handle concurrent requests efficiently
- **FR-016**: System MUST return responses in clean JSON format for easy frontend integration
- **FR-017**: System MUST implement proper error handling with structured error responses (error_code, message, details)
- **FR-018**: System MUST validate all input schemas using Pydantic models (type safety)
- **FR-019**: System MUST log all queries, retrievals, and errors for debugging and evaluation
- **FR-020**: System MUST limit response length to 200 words by default unless user requests long-form (request param: max_words)

### Key Entities

- **BookChunk**: Represents a segment of book content (max 700 tokens). Attributes: chunk_id (UUID), content (text), token_count (int), chapter_id (str), section_name (str), embedding_id (Qdrant point ID).
- **ChapterMetadata**: Represents a book chapter. Attributes: chapter_id (str), chapter_title (str), section_name (str), total_chunks (int), ingestion_timestamp (datetime).
- **Query**: Represents a user question. Attributes: query_text (str), mode (enum: standard | selected_text), selected_text (optional str), max_words (int, default 200).
- **Response**: Represents a chatbot answer. Attributes: answer (str), citations (list of ChunkReference), chunks_used (list of chunk_ids), confidence_score (float), no_search_performed (bool for selected-text mode).
- **ChunkReference**: Citation metadata. Attributes: chapter_id (str), section_name (str), chunk_id (UUID), similarity_score (float).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System achieves zero hallucinations — 100% of answers must be traceable to retrieved chunks (evaluated via automated fact-checking against known Q&A pairs)
- **SC-002**: Context override works flawlessly — 100% of selected-text queries must be answered using ONLY the provided text (no Qdrant search performed, verified via logs)
- **SC-003**: API retrieval latency <500ms at p95 for POST /query endpoint (measured via load testing with 100 concurrent users)
- **SC-004**: RAG pipeline passes factuality benchmark ≥95% (evaluated against ground-truth Q&A dataset derived from book content)
- **SC-005**: System successfully embeds and indexes full book content (10+ chapters, 1000+ chunks) within 5 minutes via POST /embed
- **SC-006**: All responses include valid citations (chapter_id, section_name) with 100% traceability (verified via automated tests)
- **SC-007**: Out-of-scope queries trigger transparency message 100% of the time (tested with queries about topics not in book)
- **SC-008**: Frontend integration ready — API returns clean JSON compatible with React/Next.js and ePub webview (validated via example frontend implementation)
- **SC-009**: System handles 100 concurrent queries without degradation (verified via load testing)
- **SC-010**: All endpoints include comprehensive OpenAPI documentation (validated via Swagger UI)

## Non-Functional Requirements

### Performance

- **NFR-001**: POST /query endpoint MUST respond within 500ms at p95 under normal load (10 concurrent users)
- **NFR-002**: POST /embed endpoint MUST process 100 chunks per minute during bulk ingestion
- **NFR-003**: Qdrant vector search MUST complete within 100ms (measured separately from end-to-end latency)
- **NFR-004**: Cohere Rerank MUST complete within 150ms for 4 chunks

### Reliability

- **NFR-005**: System MUST implement retry logic with exponential backoff for Cohere API calls (max 3 retries)
- **NFR-006**: System MUST gracefully degrade when Qdrant is unavailable (return 503 with clear error message)
- **NFR-007**: System MUST maintain connection pool health checks for Neon Postgres (reconnect on failure)
- **NFR-008**: System MUST log all errors with structured context (query_id, timestamp, error_type, stack_trace)

### Security

- **NFR-009**: System MUST use environment variables for all API keys (COHERE_API_KEY, QDRANT_API_KEY, NEON_DB_URL)
- **NFR-010**: System MUST never expose raw API keys in logs or error messages
- **NFR-011**: System MUST implement rate limiting (100 requests per minute per IP) to prevent abuse
- **NFR-012**: System MUST validate all input schemas to prevent injection attacks (SQL, prompt injection)

### Observability

- **NFR-013**: System MUST log all queries with metadata: query_text, mode, chunks_retrieved, rerank_scores, generation_time
- **NFR-014**: System MUST expose Prometheus metrics: request_count, latency_histogram, error_rate, qdrant_connection_status
- **NFR-015**: System MUST include correlation IDs in all logs for request tracing

## Technical Constraints

### Technology Stack (Locked)

- **Backend Framework**: Python 3.11+, FastAPI 0.100+
- **Vector Database**: Qdrant Cloud (Free Tier)
- **Metadata Database**: Neon Serverless Postgres
- **Embeddings**: Cohere embed-english-v3.0 (1024 dimensions)
- **Reranker**: Cohere Rerank v3
- **Generator**: Cohere Command model (command-r or command-r-plus)
- **Type Safety**: Pydantic v2 for all request/response models
- **Database Driver**: psycopg3 with connection pooling

### System Limits

- **Chunk Size**: Max 700 tokens per chunk (enforced during ingestion)
- **Retrieval Top-K**: 4 chunks from Qdrant vector search
- **Rerank Top-N**: 3 chunks after Cohere Rerank
- **Response Length**: 200 words default, configurable via request param (max 500 words)
- **Selected Text Mode**: Min 10 tokens, max 2000 tokens for selected_text input
- **Query Length**: Max 500 tokens per query_text

### Environment Variables (Required)

```bash
QDRANT_API_KEY="<QDRANT_API_KEY>"
QDRANT_URL="<QDRANT_URL>"
QDRANT_CLUSTER_ID="<CLUSTER_ID>"
NEON_DB_URL="<NEON_DB_URL>"
COHERE_API_KEY="<COHERE_API_KEY>"
LOG_LEVEL="INFO"
MAX_CONCURRENT_REQUESTS="100"
RATE_LIMIT_PER_MINUTE="100"
```

## API Contracts

### POST /embed

**Purpose**: Ingest book content, chunk it, embed via Cohere, store in Qdrant + Neon

**Request**:
```json
{
  "chapters": [
    {
      "chapter_id": "ch01",
      "chapter_title": "Introduction to AI",
      "sections": [
        {
          "section_name": "1.1 What is AI?",
          "content": "Artificial Intelligence (AI) refers to..."
        }
      ]
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "total_chunks_created": 150,
  "total_chapters_processed": 1,
  "ingestion_time_seconds": 45.2
}
```

**Errors**:
- 400 Bad Request: Invalid schema (missing chapter_id, empty content)
- 500 Internal Server Error: Qdrant or Neon connection failure

---

### POST /query

**Purpose**: Standard RAG retrieval — vector search + rerank + generate with citations

**Request**:
```json
{
  "query_text": "What is transfer learning?",
  "max_words": 150
}
```

**Response** (200 OK):
```json
{
  "answer": "Transfer learning is a technique where a model trained on one task is adapted to a related task...",
  "citations": [
    {
      "chapter_id": "ch05",
      "section_name": "5.3 Transfer Learning",
      "chunk_id": "uuid-1234",
      "similarity_score": 0.92
    }
  ],
  "chunks_used": ["uuid-1234", "uuid-5678"],
  "confidence_score": 0.89,
  "no_search_performed": false
}
```

**Response** (200 OK - Out of Scope):
```json
{
  "answer": "This topic isn't mentioned in the book sections I have access to.",
  "citations": [],
  "chunks_used": [],
  "confidence_score": 0.0,
  "no_search_performed": false
}
```

**Errors**:
- 400 Bad Request: Empty query_text or exceeds 500 tokens
- 503 Service Unavailable: Qdrant or Cohere API unavailable

---

### POST /selected-query

**Purpose**: Context override mode — answer based ONLY on user-selected text

**Request**:
```json
{
  "query_text": "Explain this concept in simple terms",
  "selected_text": "Gradient descent is an optimization algorithm that iteratively adjusts parameters...",
  "max_words": 100
}
```

**Response** (200 OK):
```json
{
  "answer": "Gradient descent works by iteratively adjusting parameters to minimize error...",
  "citations": [],
  "chunks_used": [],
  "confidence_score": 0.95,
  "no_search_performed": true,
  "source": "user_selection",
  "selected_text_length": 85
}
```

**Errors**:
- 400 Bad Request: selected_text too short (<10 tokens) or too long (>2000 tokens)
- 429 Too Many Requests: Cohere API rate limit exceeded

---

### GET /health

**Purpose**: System health check for monitoring

**Response** (200 OK):
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "neon_connected": true,
  "total_chunks_indexed": 1523,
  "total_chapters": 12,
  "uptime_seconds": 3600
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "degraded",
  "qdrant_connected": false,
  "neon_connected": true,
  "error": "Qdrant connection timeout"
}
```

## Implementation Notes

### Folder Structure (Expected)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment variable loading
│   ├── models/
│   │   ├── requests.py         # Pydantic request models
│   │   └── responses.py        # Pydantic response models
│   ├── services/
│   │   ├── embeddings.py       # Cohere embedding logic
│   │   ├── retrieval.py        # Qdrant search + rerank
│   │   ├── generation.py       # Cohere answer generation
│   │   └── ingestion.py        # Book content ingestion
│   ├── db/
│   │   ├── qdrant_client.py    # Qdrant connection
│   │   ├── neon_client.py      # Postgres connection pool
│   │   └── migrations/         # SQL migration scripts
│   └── routers/
│       ├── embed.py            # POST /embed
│       ├── query.py            # POST /query, POST /selected-query
│       └── health.py           # GET /health
├── tests/
│   ├── test_retrieval.py
│   ├── test_ingestion.py
│   └── test_grounding.py
├── pyproject.toml              # Poetry or uv dependencies
└── .env.example                # Example environment variables
```

### Database Schema (Neon Postgres)

```sql
CREATE TABLE chapters (
    chapter_id VARCHAR(50) PRIMARY KEY,
    chapter_title TEXT NOT NULL,
    total_chunks INTEGER DEFAULT 0,
    ingestion_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id VARCHAR(50) REFERENCES chapters(chapter_id) ON DELETE CASCADE,
    section_name TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding_id TEXT NOT NULL,  -- Qdrant point ID
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chapter_chunks ON chunks(chapter_id);
CREATE INDEX idx_embedding_id ON chunks(embedding_id);
```

### Constitution Alignment

This specification strictly follows the project constitution:

- **Principle I (Grounded Reasoning)**: FR-009 enforces zero hallucinations; all answers must trace to retrieved chunks
- **Principle II (Cohere-Native Alignment)**: FR-001, FR-006 mandate Cohere models for embeddings, rerank, and generation
- **Principle III (Context Prioritization)**: FR-010 and POST /selected-query ensure user-selected text overrides global search
- **Principle IV (Transparency)**: FR-008 requires explicit out-of-scope messages
- **Principle V (Academic Clarity)**: Response format (200 words default) and citation requirements support pedagogical use

All success criteria (SC-001 through SC-010) directly map to constitution guarantees.

## Assumptions *(mandatory)*

- The book content is structured as JSON with chapters, sections, and paragraphs
- Qdrant Cloud free tier (1GB storage) is sufficient for initial book size (<1M tokens)
- Cohere API rate limits (100 requests/minute) are sufficient for expected load
- Frontend will handle text selection events and pass selected_text to backend
- Users have modern browsers with JavaScript enabled (React/Next.js or ePub webview)
- Initial load will be moderate (<50 concurrent users), with scalability planned for future
- Conversation history persistence is not required for MVP (stateless queries)
- Admin access for POST /embed can be controlled via API key authentication

## Out of Scope *(mandatory)*

- User authentication and authorization (future feature)
- Multi-language support (English only for MVP)
- Real-time streaming responses (future enhancement)
- Book content versioning (single version for MVP)
- Advanced analytics dashboard (future feature)
- Mobile app (web-only for MVP)
- Custom embedding fine-tuning (use Cohere pretrained)
- On-premise deployment (cloud-only: Qdrant Cloud, Neon)
- Conversation history and follow-up questions (stateless for MVP)
- Voice input or text-to-speech output

## Open Questions

- **Q1**: Should the system support multiple books simultaneously, or is single-book indexing sufficient for MVP?
- **Q2**: What is the expected book size (total tokens)? This affects Qdrant free tier limits (1GB storage).
- **Q3**: Should citations include page numbers, or are chapter_id + section_name sufficient?
- **Q4**: Should the system support follow-up questions with conversation history, or is each query stateless?
- **Q5**: What is the desired behavior when Cohere API is rate-limited during peak usage? Queue requests or reject immediately?

## Dependencies

- **External APIs**: Cohere API (embeddings, rerank, generation), Qdrant Cloud, Neon Serverless Postgres
- **Python Libraries**: FastAPI, Pydantic, psycopg3, qdrant-client, cohere SDK, httpx (for async requests)
- **Infrastructure**: Requires Qdrant Cloud account (free tier), Neon Postgres database (free tier), Cohere API key

## Next Steps

1. **Review and approve this specification**
2. **Run `/sp.plan` to generate architectural design and implementation plan**
3. **Run `/sp.tasks` to break down implementation into testable tasks**
4. **Consider creating ADR for Cohere + Qdrant + Neon stack selection** (significant architectural decision)

---

**Specification Version**: 2.0.0
**Last Updated**: 2025-12-12
**Approved By**: [Pending Review]
