# API Contracts

**Feature**: 001-rag-chatbot
**Date**: 2025-12-12

## Overview

This directory contains the formal API contract specifications for the RAG Chatbot backend.

## Files

- **openapi.yaml**: OpenAPI 3.1.0 specification for all REST endpoints
- **README.md**: This file (contract documentation index)

## Contract Sources

All contracts are derived from:
1. **Feature Spec**: `specs/001-rag-chatbot/spec.md` (Functional Requirements FR-011 to FR-020)
2. **Data Model**: `specs/001-rag-chatbot/data-model.md` (Pydantic models)
3. **Constitution**: `.specify/memory/constitution.md` (Principles I-V)

## API Endpoints

### Health Check
- **GET /health**: System health status (Qdrant, Neon connections)

### Ingestion
- **POST /embed**: Ingest book content, chunk, embed, and store

### Query
- **POST /query**: Standard RAG retrieval (vector search + rerank + generate)
- **POST /selected-query**: Context override mode (user-selected text only)

## Viewing the OpenAPI Spec

### Online Swagger Editor
1. Go to https://editor.swagger.io/
2. Upload `openapi.yaml`
3. View interactive documentation

### Local Swagger UI (FastAPI)
Once the FastAPI app is running:
```bash
# Start FastAPI server
uvicorn app.main:app --reload

# Open browser
http://localhost:8000/docs
```

### Using Redoc
```bash
# Open browser
http://localhost:8000/redoc
```

## Contract Validation

### Schema Validation (Pydantic)
All request/response models use Pydantic v2 for automatic validation:
- Type checking
- Min/max length constraints
- Pattern matching (regex)
- Custom validators

### Examples
Every endpoint in `openapi.yaml` includes request/response examples for:
- **Happy path** (200 OK)
- **Validation errors** (400 Bad Request)
- **Service errors** (503 Service Unavailable)
- **Out-of-scope queries** (200 OK with transparency message)

## Testing Against Contracts

### Contract Testing Tools
- **Schemathesis**: Automated property-based testing from OpenAPI spec
- **Dredd**: Contract validation via HTTP requests
- **Postman**: Import OpenAPI spec for manual testing

### Example with Schemathesis
```bash
# Install
pip install schemathesis

# Run contract tests
schemathesis run specs/001-rag-chatbot/contracts/openapi.yaml \
  --base-url http://localhost:8000/api/v1 \
  --hypothesis-max-examples 100
```

## Constitution Alignment

| Endpoint | Constitution Principle | Enforcement |
|----------|----------------------|-------------|
| POST /query | I (Grounded Reasoning) | Returns transparency message if no chunks found |
| POST /selected-query | III (Context Prioritization) | Skips vector search, uses only selected_text |
| All responses | IV (Transparency) | Explicit out-of-scope messages, no hallucinations |
| POST /query | V (Academic Clarity) | Includes citations (chapter_id, section_name) |

## Error Codes

| Code | Meaning | HTTP Status |
|------|---------|-------------|
| INVALID_REQUEST | Schema validation failure | 400 |
| QUERY_TOO_LONG | Query exceeds 500 tokens | 400 |
| SELECTED_TEXT_TOO_SHORT | Selected text <10 tokens | 400 |
| QDRANT_UNAVAILABLE | Vector DB connection failure | 503 |
| NEON_UNAVAILABLE | Postgres connection failure | 503 |
| COHERE_RATE_LIMIT | Cohere API throttling | 429 |
| RATE_LIMIT_EXCEEDED | App-level rate limiting | 429 |

## Versioning

- **Current Version**: v1.0.0
- **API Prefix**: `/api/v1/*`
- **Versioning Strategy**: URL-based (future: `/api/v2/*` for breaking changes)

## Breaking Changes Policy

Breaking changes require:
1. New API version (`/api/v2`)
2. Deprecation notice (60 days minimum)
3. Migration guide for clients

**Non-breaking changes** (backward compatible):
- Adding new optional fields
- Adding new endpoints
- Expanding enums with new values

## Future Enhancements

Planned API extensions (not in MVP):
- **POST /query/stream**: Real-time streaming responses (SSE)
- **GET /chapters**: List all indexed chapters
- **DELETE /chapters/{chapter_id}**: Remove chapter and chunks
- **POST /feedback**: User feedback on answer quality
- **WebSocket /query**: Bidirectional conversation support

## Support

For contract questions or issues:
- Review spec: `specs/001-rag-chatbot/spec.md`
- Check data model: `specs/001-rag-chatbot/data-model.md`
- Consult constitution: `.specify/memory/constitution.md`

---

**Next Step**: Generate quickstart.md (Phase 1)
