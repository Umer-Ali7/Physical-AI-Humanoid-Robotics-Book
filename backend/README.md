# RAG Chatbot - AI-Native Textbook Assistant

AI-powered Retrieval-Augmented Generation (RAG) chatbot for Physical AI and Humanoid Robotics textbook with grounded retrieval, zero hallucinations, and user-selected-text mode.

## Features

- **Grounded Retrieval**: All answers traceable to book content with citations
- **Zero Hallucinations**: Explicit transparency when information not available in book
- **User-Selected Text Mode**: Context override for precise question answering
- **Cohere-Powered**: Uses embed-english-v3.0, Rerank v3, and Command-R-Plus
- **Dual Storage**: Qdrant vector database + Neon Postgres for metadata

## Quick Start

For detailed setup instructions, see [Quick Start Guide](../specs/001-rag-chatbot/quickstart.md)

### Prerequisites

- Python 3.11+
- uv package manager
- Cohere API key
- Qdrant Cloud account (free tier)
- Neon Serverless Postgres account (free tier)

### Installation

```bash
# Install dependencies
uv sync

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize databases
psql $NEON_DB_URL -f app/db/migrations/001_initial_schema.sql
python scripts/init_qdrant.py

# Start server
uvicorn app.main:app --reload
```

### API Endpoints

- `GET /api/v1/health` - System health check
- `POST /api/v1/embed` - Ingest book content
- `POST /api/v1/query` - Standard RAG query
- `POST /api/v1/selected-query` - Selected-text mode

### Documentation

- [Feature Specification](../specs/001-rag-chatbot/spec.md)
- [Implementation Plan](../specs/001-rag-chatbot/plan.md)
- [Data Model](../specs/001-rag-chatbot/data-model.md)
- [API Contracts](../specs/001-rag-chatbot/contracts/openapi.yaml)
- [Tasks Breakdown](../specs/001-rag-chatbot/tasks.md)

### Interactive API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

**Tech Stack**: Python 3.11, FastAPI, Cohere, Qdrant, Neon Postgres
**Performance**: <500ms p95 latency for queries
**Constitution**: Zero hallucinations, grounded reasoning, context prioritization

## License

MIT
