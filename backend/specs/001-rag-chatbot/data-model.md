# Data Model: RAG Chatbot

**Feature**: 001-rag-chatbot
**Date**: 2025-12-12
**Status**: Complete

## Overview

This document defines the complete data model for the RAG chatbot system, including database schemas (Neon Postgres), vector database structure (Qdrant), and application-level entities (Pydantic models).

---

## 1. Database Schema (Neon Postgres)

### 1.1 `chapters` Table

Stores chapter-level metadata for the book.

```sql
CREATE TABLE chapters (
    chapter_id VARCHAR(50) PRIMARY KEY,
    chapter_title TEXT NOT NULL,
    total_chunks INTEGER DEFAULT 0,
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_chapters_ingestion ON chapters(ingestion_timestamp DESC);
```

**Columns**:
- `chapter_id` (VARCHAR(50), PK): Unique identifier (e.g., "ch01", "ch02")
- `chapter_title` (TEXT, NOT NULL): Human-readable title (e.g., "Introduction to AI")
- `total_chunks` (INTEGER, DEFAULT 0): Count of chunks in this chapter (updated on ingestion)
- `ingestion_timestamp` (TIMESTAMP, DEFAULT NOW()): When chapter was indexed
- `metadata` (JSONB, DEFAULT '{}'): Extensible metadata (e.g., author, version, tags)

**Constraints**:
- Primary key: `chapter_id`
- No cascading deletes (handled by foreign keys in `chunks`)

**Validation Rules**:
- `chapter_id`: Must match pattern `^ch\d{2}$` (enforced in application layer)
- `chapter_title`: Non-empty string, max 200 characters
- `total_chunks`: Non-negative integer

---

### 1.2 `chunks` Table

Stores individual text chunks with embeddings and metadata.

```sql
CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id VARCHAR(50) NOT NULL REFERENCES chapters(chapter_id) ON DELETE CASCADE,
    section_name TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL CHECK (token_count > 0 AND token_count <= 700),
    embedding_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_chapter_chunks ON chunks(chapter_id);
CREATE INDEX idx_embedding_id ON chunks(embedding_id);
CREATE INDEX idx_created_at ON chunks(created_at DESC);
CREATE INDEX idx_token_count ON chunks(token_count);
```

**Columns**:
- `chunk_id` (UUID, PK): Unique identifier (auto-generated)
- `chapter_id` (VARCHAR(50), FK): References `chapters.chapter_id`
- `section_name` (TEXT, NOT NULL): Section identifier (e.g., "1.1 What is AI?")
- `content` (TEXT, NOT NULL): Full chunk text (raw, not preprocessed)
- `token_count` (INTEGER, NOT NULL): Number of tokens (validated 1-700)
- `embedding_id` (TEXT, NOT NULL, UNIQUE): Qdrant point ID (for cross-referencing)
- `created_at` (TIMESTAMP, DEFAULT NOW()): Chunk creation timestamp
- `metadata` (JSONB, DEFAULT '{}'): Extensible metadata (e.g., overlap_with, page_range)

**Constraints**:
- Primary key: `chunk_id`
- Foreign key: `chapter_id` → `chapters.chapter_id` (ON DELETE CASCADE)
- Unique: `embedding_id` (ensures 1:1 mapping with Qdrant points)
- Check: `token_count BETWEEN 1 AND 700`

**Validation Rules**:
- `section_name`: Non-empty string, max 100 characters
- `content`: Non-empty string, max 10,000 characters
- `embedding_id`: Non-empty string, matches UUID format

**Relationships**:
- Many-to-One: `chunks.chapter_id` → `chapters.chapter_id`
- When a chapter is deleted, all associated chunks are cascade-deleted

---

### 1.3 Database Triggers

**Update `total_chunks` on chunk insertion**:
```sql
CREATE OR REPLACE FUNCTION update_chapter_chunk_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chapters
    SET total_chunks = (
        SELECT COUNT(*) FROM chunks WHERE chapter_id = NEW.chapter_id
    )
    WHERE chapter_id = NEW.chapter_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_chunk_count
AFTER INSERT OR DELETE ON chunks
FOR EACH ROW
EXECUTE FUNCTION update_chapter_chunk_count();
```

---

## 2. Vector Database Schema (Qdrant)

### 2.1 Collection: `book_chunks`

Stores vector embeddings for all book chunks.

**Configuration**:
```python
from qdrant_client.models import Distance, VectorParams

collection_config = {
    "name": "book_chunks",
    "vectors": VectorParams(
        size=1024,  # Cohere embed-english-v3.0 dimensions
        distance=Distance.COSINE
    )
}
```

**Point Structure**:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",  // UUID (matches chunks.embedding_id)
    "vector": [0.12, -0.34, 0.56, ...],  // 1024-dim float array
    "payload": {
        "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
        "chapter_id": "ch01",
        "section_name": "1.1 What is AI?",
        "content": "Artificial Intelligence (AI) refers to...",
        "token_count": 650,
        "created_at": "2025-12-12T10:30:00Z"
    }
}
```

**Payload Fields**:
- `chunk_id` (string, UUID): Maps to `chunks.chunk_id` in Postgres
- `chapter_id` (string): For filtering by chapter
- `section_name` (string): For citation generation
- `content` (string): Full chunk text (stored for retrieval without DB query)
- `token_count` (integer): For debugging and validation
- `created_at` (string, ISO 8601): Timestamp for sorting/filtering

**Indexes**:
- Automatic HNSW index on vector field (configured by Qdrant)
- Payload indexes on `chapter_id` and `section_name` for filtering

**Distance Metric**: Cosine (standard for normalized embeddings)

---

## 3. Application-Level Entities (Pydantic Models)

### 3.1 Request Models (`app/models/requests.py`)

**EmbedRequest** (POST /embed)
```python
from pydantic import BaseModel, Field, field_validator
from typing import List

class Section(BaseModel):
    section_name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)

class Chapter(BaseModel):
    chapter_id: str = Field(..., pattern=r"^ch\d{2}$")
    chapter_title: str = Field(..., min_length=1, max_length=200)
    sections: List[Section] = Field(..., min_items=1)

class EmbedRequest(BaseModel):
    chapters: List[Chapter] = Field(..., min_items=1)
```

**QueryRequest** (POST /query)
```python
class QueryRequest(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=2000)
    max_words: int = Field(default=200, ge=50, le=500)

    @field_validator("query_text")
    def validate_token_count(cls, v):
        # Approximate token count (1 token ≈ 4 chars)
        if len(v) / 4 > 500:
            raise ValueError("Query exceeds 500 tokens")
        return v
```

**SelectedQueryRequest** (POST /selected-query)
```python
class SelectedQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=2000)
    selected_text: str = Field(..., min_length=40, max_length=8000)  # ~10-2000 tokens
    max_words: int = Field(default=200, ge=50, le=500)

    @field_validator("selected_text")
    def validate_selected_text_tokens(cls, v):
        token_count = len(v) / 4  # Approximation
        if token_count < 10:
            raise ValueError("Selected text too short (min 10 tokens)")
        if token_count > 2000:
            raise ValueError("Selected text too long (max 2000 tokens)")
        return v
```

---

### 3.2 Response Models (`app/models/responses.py`)

**EmbedResponse** (POST /embed)
```python
class EmbedResponse(BaseModel):
    status: str = Field(default="success")
    total_chunks_created: int = Field(..., ge=0)
    total_chapters_processed: int = Field(..., ge=1)
    ingestion_time_seconds: float = Field(..., ge=0)
```

**ChunkReference** (Citation metadata)
```python
class ChunkReference(BaseModel):
    chapter_id: str
    section_name: str
    chunk_id: str  # UUID as string
    similarity_score: float = Field(..., ge=0.0, le=1.0)
```

**QueryResponse** (POST /query, POST /selected-query)
```python
from typing import List, Optional

class QueryResponse(BaseModel):
    answer: str
    citations: List[ChunkReference] = Field(default_factory=list)
    chunks_used: List[str] = Field(default_factory=list)  # List of chunk_ids
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    no_search_performed: bool = Field(default=False)
    source: Optional[str] = Field(default=None)  # "user_selection" for selected-query
    selected_text_length: Optional[int] = Field(default=None)  # Token count
```

**HealthResponse** (GET /health)
```python
class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    qdrant_connected: bool
    neon_connected: bool
    total_chunks_indexed: int = Field(..., ge=0)
    total_chapters: int = Field(..., ge=0)
    uptime_seconds: float = Field(..., ge=0)
```

**ErrorResponse** (All error scenarios)
```python
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    error_code: str  # E.g., "QDRANT_UNAVAILABLE", "INVALID_REQUEST"
    message: str
    details: Optional[Dict[str, Any]] = Field(default=None)
    timestamp: str  # ISO 8601 timestamp
```

---

## 4. Entity Relationships

### 4.1 Database Relationships (Postgres)

```
chapters (1) ──< (M) chunks
   PK: chapter_id         FK: chapter_id
```

- **One-to-Many**: One chapter has many chunks
- **Cascade Delete**: Deleting a chapter deletes all associated chunks
- **Referential Integrity**: Enforced via foreign key constraint

---

### 4.2 Cross-System Relationships

```
Postgres chunks.embedding_id (1:1) Qdrant point.id
```

- **One-to-One**: Each Postgres chunk maps to exactly one Qdrant point
- **Enforced By**: Unique constraint on `chunks.embedding_id` + point ID matching
- **Synchronization**: Managed by ingestion service (atomic transactions)

---

### 4.3 Application-Level Relationships

```
QueryRequest → Qdrant Search → ChunkReference[] → QueryResponse
SelectedQueryRequest → (skip Qdrant) → QueryResponse
EmbedRequest → Postgres INSERT + Qdrant UPSERT → EmbedResponse
```

---

## 5. Data Validation Rules

### 5.1 Database-Level Validation (Postgres Constraints)

| Field | Rule |
|-------|------|
| `chapters.chapter_id` | VARCHAR(50), PRIMARY KEY |
| `chapters.chapter_title` | TEXT, NOT NULL |
| `chunks.chunk_id` | UUID, PRIMARY KEY |
| `chunks.chapter_id` | FK → chapters.chapter_id, NOT NULL |
| `chunks.token_count` | CHECK (1 <= token_count <= 700) |
| `chunks.embedding_id` | TEXT, UNIQUE, NOT NULL |

---

### 5.2 Application-Level Validation (Pydantic)

| Field | Rule |
|-------|------|
| `EmbedRequest.chapters` | min_items=1 |
| `Chapter.chapter_id` | Pattern: `^ch\d{2}$` |
| `Chapter.chapter_title` | min_length=1, max_length=200 |
| `QueryRequest.query_text` | min_length=1, max 500 tokens |
| `QueryRequest.max_words` | 50 <= max_words <= 500 |
| `SelectedQueryRequest.selected_text` | 10 <= tokens <= 2000 |

---

### 5.3 Business Logic Validation (Service Layer)

| Rule | Enforcement |
|------|-------------|
| Chunk overlap calculation | `embeddings.py` chunking logic |
| Deduplication (content hash) | `ingestion.py` before DB insert |
| Similarity threshold (0.7) | `retrieval.py` vector search filter |
| Citation traceability | `generation.py` includes chunk_ids in response |

---

## 6. State Transitions

### 6.1 Chunk Lifecycle

```
1. [Non-existent]
   ↓ (POST /embed called)
2. [Chunking] → Text split into overlapping segments
   ↓
3. [Embedding] → Cohere embed-english-v3.0 generates vector
   ↓
4. [Storage] → Postgres INSERT + Qdrant UPSERT (atomic)
   ↓
5. [Indexed] → Available for retrieval
   ↓ (DELETE chapter)
6. [Deleted] → Cascade delete from Postgres + manual Qdrant delete
```

**Atomic Operations**:
- Step 4 uses database transaction: If Qdrant upsert fails, Postgres INSERT is rolled back

---

### 6.2 Query Lifecycle (Standard Mode)

```
1. [Received] → POST /query validated
   ↓
2. [Embedding] → Query text embedded via Cohere
   ↓
3. [Vector Search] → Qdrant returns top_k=4 chunks
   ↓
4. [Reranking] → Cohere Rerank refines to top_n=3
   ↓
5. [Metadata Fetch] → Postgres query for chapter_id, section_name
   ↓
6. [Generation] → Cohere Command-R-Plus generates answer
   ↓
7. [Response] → QueryResponse with answer + citations
```

---

### 6.3 Query Lifecycle (Selected-Text Mode)

```
1. [Received] → POST /selected-query validated
   ↓
2. [Validation] → Check selected_text length (10-2000 tokens)
   ↓
3. [Generation] → Cohere Command-R-Plus with selected_text as context
   ↓
4. [Response] → QueryResponse (source="user_selection", no_search_performed=true)
```

---

## 7. Sample Data

### 7.1 Sample Chapter (Postgres)

```sql
INSERT INTO chapters (chapter_id, chapter_title, total_chunks, metadata)
VALUES (
    'ch01',
    'Introduction to Physical AI',
    15,
    '{"author": "Dr. Jane Smith", "version": "1.0", "tags": ["fundamentals", "overview"]}'::jsonb
);
```

---

### 7.2 Sample Chunk (Postgres)

```sql
INSERT INTO chunks (chunk_id, chapter_id, section_name, content, token_count, embedding_id, metadata)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'ch01',
    '1.1 What is Physical AI?',
    'Physical AI refers to artificial intelligence systems that interact with the physical world through sensors and actuators...',
    142,
    '550e8400-e29b-41d4-a716-446655440000',
    '{"overlap_with": null, "page_range": "1-2"}'::jsonb
);
```

---

### 7.3 Sample Qdrant Point

```python
from qdrant_client.models import PointStruct

point = PointStruct(
    id="550e8400-e29b-41d4-a716-446655440000",
    vector=[0.123, -0.456, 0.789, ...],  # 1024 dimensions
    payload={
        "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
        "chapter_id": "ch01",
        "section_name": "1.1 What is Physical AI?",
        "content": "Physical AI refers to artificial intelligence systems...",
        "token_count": 142,
        "created_at": "2025-12-12T10:30:00Z"
    }
)
```

---

## 8. Indexes and Performance

### 8.1 Postgres Indexes

| Index | Purpose | Type |
|-------|---------|------|
| `idx_chapter_chunks` | Speed up chunk lookups by chapter | B-tree on `chunks.chapter_id` |
| `idx_embedding_id` | Fast reverse lookup from Qdrant ID | B-tree on `chunks.embedding_id` |
| `idx_created_at` | Time-based queries (recent chunks) | B-tree DESC on `chunks.created_at` |
| `idx_token_count` | Filter chunks by size | B-tree on `chunks.token_count` |

**Estimated Query Performance**:
- Lookup chunk by `embedding_id`: O(log n), <5ms for 10k rows
- Fetch all chunks for chapter: O(log n + k), <10ms for 100 chunks

---

### 8.2 Qdrant Indexes

| Index | Purpose | Configuration |
|-------|---------|---------------|
| HNSW vector index | Approximate nearest neighbor search | M=16, ef_construct=100 |
| Payload index: `chapter_id` | Filter by chapter | Keyword index |
| Payload index: `section_name` | Filter by section | Keyword index |

**Estimated Query Performance**:
- Vector search (top_k=4): <100ms for 100k points
- Filtered search (chapter_id): <50ms for 10k points per chapter

---

## 9. Data Integrity Guarantees

### 9.1 Cross-System Consistency

**Guarantee**: Every Postgres chunk has a corresponding Qdrant point, and vice versa.

**Enforcement**:
1. Ingestion uses two-phase approach:
   - Insert into Postgres (within transaction)
   - Upsert into Qdrant
   - If Qdrant fails, rollback Postgres transaction
2. Health check validates counts: `SELECT COUNT(*) FROM chunks` == Qdrant collection size
3. Periodic reconciliation job (future): Detect and fix orphaned records

---

### 9.2 Deduplication

**Guarantee**: No duplicate chunks (same content) stored.

**Enforcement**:
- Content hash (SHA-256) computed before insertion
- Check for existing hash in `chunks.metadata->>'content_hash'`
- Skip insertion if duplicate found
- Log warning: "Duplicate chunk detected for chapter {chapter_id}"

---

## 10. Migration Strategy

### 10.1 Initial Schema Deployment

```bash
# Run migration script
psql $NEON_DB_URL -f backend/app/db/migrations/001_initial_schema.sql
```

**Migration File**: `backend/app/db/migrations/001_initial_schema.sql`
- Creates `chapters` table
- Creates `chunks` table
- Creates indexes
- Creates triggers

---

### 10.2 Future Schema Changes

**Process**:
1. Create new migration file (e.g., `002_add_page_numbers.sql`)
2. Test migration on staging database
3. Apply to production with rollback plan
4. Update Pydantic models to match new schema

**Example Future Migration**:
```sql
-- 002_add_page_numbers.sql
ALTER TABLE chunks
ADD COLUMN page_number INTEGER;

CREATE INDEX idx_page_number ON chunks(page_number);
```

---

## Summary

This data model provides:
- **Referential integrity** between Postgres and Qdrant
- **Validation at all layers** (DB constraints, Pydantic, business logic)
- **Performance optimization** via strategic indexing
- **Extensibility** via JSONB metadata fields
- **Type safety** via Pydantic models

All entities align with functional requirements (FR-001 to FR-020) and constitution principles (I-V).

---

**Next Step**: Generate API contracts (Phase 1)
