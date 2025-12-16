# Quickstart Guide: RAG Chatbot

**Feature**: 001-rag-chatbot
**Date**: 2025-12-12
**Estimated Setup Time**: 15 minutes

## Overview

This guide will get you from zero to a running RAG chatbot backend in 15 minutes, including:
- Environment setup (Python, dependencies, API keys)
- Database initialization (Qdrant collection, Neon Postgres schema)
- Sample book content ingestion
- Testing all endpoints (health, embed, query, selected-query)

---

## Prerequisites

### Required Accounts
1. **Cohere**: Free API key (https://dashboard.cohere.com/)
2. **Qdrant Cloud**: Free tier cluster (https://cloud.qdrant.io/)
3. **Neon**: Free serverless Postgres (https://console.neon.tech/)

### Local Tools
- **Python 3.11+**: `python --version` (download from https://www.python.org/downloads/)
- **uv**: Fast Python package manager (install: `pip install uv`)
- **Git**: For cloning repository
- **curl or Postman**: For API testing

---

## Step 1: Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

---

## Step 2: Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Copy example template
cp .env.example .env

# Edit .env with your API keys
nano .env  # Or use any text editor
```

**Required environment variables**:
```bash
# Cohere API (get from https://dashboard.cohere.com/)
COHERE_API_KEY=your_cohere_api_key_here

# Qdrant Cloud (get from https://cloud.qdrant.io/)
QDRANT_URL=https://your-cluster-id.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_CLUSTER_ID=your-cluster-id

# Neon Postgres (get from https://console.neon.tech/)
NEON_DB_URL=postgresql://user:password@host.neon.tech/dbname

# Application config (defaults work for local dev)
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=100
RATE_LIMIT_PER_MINUTE=100
```

---

## Step 3: Initialize Databases

### 3.1 Create Neon Postgres Schema

```bash
# Run migration script
psql $NEON_DB_URL -f app/db/migrations/001_initial_schema.sql
```

**Or manually**:
```sql
-- Connect to Neon via psql or Neon console
psql $NEON_DB_URL

-- Create tables
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
    token_count INTEGER NOT NULL CHECK (token_count > 0 AND token_count <= 700),
    embedding_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create indexes
CREATE INDEX idx_chapter_chunks ON chunks(chapter_id);
CREATE INDEX idx_embedding_id ON chunks(embedding_id);
CREATE INDEX idx_created_at ON chunks(created_at DESC);
```

### 3.2 Create Qdrant Collection

Qdrant collection will be created automatically on first `/embed` request, or manually via:

```python
# Python script: scripts/init_qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

client.create_collection(
    collection_name="book_chunks",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)

print("Qdrant collection 'book_chunks' created successfully!")
```

Run script:
```bash
python scripts/init_qdrant.py
```

---

## Step 4: Start FastAPI Server

```bash
# From backend/ directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Step 5: Test Health Endpoint

```bash
curl -X GET http://localhost:8000/api/v1/health
```

**Expected response** (200 OK):
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "neon_connected": true,
  "total_chunks_indexed": 0,
  "total_chapters": 0,
  "uptime_seconds": 5.2
}
```

If `qdrant_connected: false` or `neon_connected: false`, verify `.env` credentials.

---

## Step 6: Ingest Sample Book Content

### 6.1 Create Sample Data File

Create `sample_book.json`:
```json
{
  "chapters": [
    {
      "chapter_id": "ch01",
      "chapter_title": "Introduction to Physical AI",
      "sections": [
        {
          "section_name": "1.1 What is Physical AI?",
          "content": "Physical AI refers to artificial intelligence systems that interact with the physical world through sensors and actuators. Unlike purely digital AI systems that operate on abstract data, physical AI must reason about embodied environments, handle uncertainty from noisy sensors, and execute actions with real-world consequences. This includes robots, autonomous vehicles, drones, and smart manufacturing systems."
        },
        {
          "section_name": "1.2 History of Robotics",
          "content": "The field of robotics emerged in the 1960s with the development of industrial manipulators like the Unimate, which automated repetitive tasks in manufacturing. Early robots were programmed with fixed sequences and lacked adaptability. The integration of AI techniques in the 1980s and 1990s enabled robots to perceive their environment using computer vision and make decisions using planning algorithms. Modern robotics leverages deep learning for perception, reinforcement learning for control, and foundation models for reasoning."
        },
        {
          "section_name": "1.3 Key Challenges",
          "content": "Physical AI faces several unique challenges: (1) Sim-to-real gap - models trained in simulation often fail in real-world deployment due to physics mismatches. (2) Sample efficiency - collecting real-world training data is expensive and time-consuming. (3) Safety and robustness - physical systems must operate reliably in unpredictable environments without causing harm. (4) Embodiment - reasoning about 3D geometry, contact dynamics, and force control requires specialized representations."
        }
      ]
    }
  ]
}
```

### 6.2 Ingest via POST /embed

```bash
curl -X POST http://localhost:8000/api/v1/embed \
  -H "Content-Type: application/json" \
  -d @sample_book.json
```

**Expected response** (200 OK):
```json
{
  "status": "success",
  "total_chunks_created": 3,
  "total_chapters_processed": 1,
  "ingestion_time_seconds": 8.7
}
```

**Note**: Ingestion time depends on Cohere API latency (~2-3s per embedding batch).

---

## Step 7: Test Standard RAG Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What is the sim-to-real gap in robotics?",
    "max_words": 100
  }'
```

**Expected response** (200 OK):
```json
{
  "answer": "The sim-to-real gap refers to the problem where models trained in simulation often fail when deployed in the real world. This happens because simulated physics don't perfectly match real-world dynamics, leading to performance degradation when robots trained in virtual environments encounter actual physical systems.",
  "citations": [
    {
      "chapter_id": "ch01",
      "section_name": "1.3 Key Challenges",
      "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
      "similarity_score": 0.94
    }
  ],
  "chunks_used": ["550e8400-e29b-41d4-a716-446655440000"],
  "confidence_score": 0.91,
  "no_search_performed": false
}
```

---

## Step 8: Test Selected-Text Query (Context Override)

```bash
curl -X POST http://localhost:8000/api/v1/selected-query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Summarize this in one sentence",
    "selected_text": "The field of robotics emerged in the 1960s with the development of industrial manipulators like the Unimate, which automated repetitive tasks in manufacturing. Early robots were programmed with fixed sequences and lacked adaptability.",
    "max_words": 50
  }'
```

**Expected response** (200 OK):
```json
{
  "answer": "Robotics began in the 1960s with industrial robots like Unimate that automated manufacturing tasks using fixed, non-adaptive programs.",
  "citations": [],
  "chunks_used": [],
  "confidence_score": 0.96,
  "no_search_performed": true,
  "source": "user_selection",
  "selected_text_length": 32
}
```

**Verification**: Notice `no_search_performed: true` and `source: "user_selection"` — this confirms vector search was skipped (Constitution Principle III: Context Prioritization).

---

## Step 9: Test Out-of-Scope Query (Transparency)

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What is quantum computing?",
    "max_words": 100
  }'
```

**Expected response** (200 OK):
```json
{
  "answer": "This topic isn't mentioned in the book sections I have access to.",
  "citations": [],
  "chunks_used": [],
  "confidence_score": 0.0,
  "no_search_performed": false
}
```

**Verification**: This confirms zero hallucination (Constitution Principle I: Grounded Reasoning) and transparency (Principle IV).

---

## Step 10: View Interactive API Documentation

### Swagger UI
Open in browser:
```
http://localhost:8000/docs
```

Features:
- Try out all endpoints interactively
- View request/response schemas
- See example payloads
- Execute test requests from browser

### Redoc (Alternative)
```
http://localhost:8000/redoc
```

Features:
- Clean, searchable documentation
- OpenAPI spec download
- Mobile-friendly layout

---

## Common Issues & Troubleshooting

### Issue 1: `qdrant_connected: false`
**Cause**: Invalid Qdrant URL or API key
**Solution**:
```bash
# Test Qdrant connection manually
curl -X GET "$QDRANT_URL/collections" \
  -H "api-key: $QDRANT_API_KEY"

# Expected: {"result": {"collections": [...]}, "status": "ok"}
```

### Issue 2: `neon_connected: false`
**Cause**: Invalid Neon connection string
**Solution**:
```bash
# Test Neon connection
psql $NEON_DB_URL -c "SELECT 1;"

# Expected:
#  ?column?
# ----------
#         1
```

### Issue 3: Cohere API Rate Limit (429)
**Cause**: Free tier rate limit exceeded (100 req/min)
**Solution**: Wait 60 seconds, or upgrade Cohere plan

### Issue 4: Empty Response from POST /query
**Cause**: No book content indexed
**Solution**: Run Step 6 (ingest sample data)

### Issue 5: Import Errors
**Cause**: Dependencies not installed
**Solution**:
```bash
uv sync --reinstall
```

---

## Next Steps

### Local Development
1. Add more book chapters to `sample_book.json`
2. Test retrieval accuracy with ground-truth Q&A pairs
3. Experiment with `max_words` parameter (50-500)
4. Monitor logs: `tail -f app.log`

### Production Deployment
1. Deploy to Render/Railway/Fly.io (see `specs/001-rag-chatbot/research.md` Section 9)
2. Configure environment variables in platform dashboard
3. Enable health check endpoint: `GET /health`
4. Set up monitoring (Sentry, Prometheus)

### Testing
```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run factuality benchmarks
pytest tests/benchmarks/test_grounding.py -v
```

### Frontend Integration
See `specs/001-rag-chatbot/spec.md` Section "Implementation Notes" for example React integration:

```javascript
// Example: Query RAG chatbot from frontend
async function queryRagChatbot(question) {
  const response = await fetch('http://localhost:8000/api/v1/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      query_text: question,
      max_words: 150
    })
  });

  const data = await response.json();
  return data; // { answer, citations, chunks_used, confidence_score }
}
```

---

## Verification Checklist

- [ ] Health endpoint returns `status: "healthy"`
- [ ] Qdrant collection `book_chunks` exists (1024-dim vectors)
- [ ] Neon Postgres has `chapters` and `chunks` tables
- [ ] Sample book content ingested successfully (3 chunks)
- [ ] Standard query returns answer with citations
- [ ] Selected-text query returns answer with `no_search_performed: true`
- [ ] Out-of-scope query returns transparency message
- [ ] Swagger UI accessible at `/docs`

---

## Support & Resources

- **Specification**: `specs/001-rag-chatbot/spec.md`
- **Data Model**: `specs/001-rag-chatbot/data-model.md`
- **API Contracts**: `specs/001-rag-chatbot/contracts/openapi.yaml`
- **Research**: `specs/001-rag-chatbot/research.md`
- **Constitution**: `.specify/memory/constitution.md`

---

**Total Setup Time**: 15 minutes (assuming accounts already created)

**Next Step**: Review `specs/001-rag-chatbot/plan.md` for full implementation plan
