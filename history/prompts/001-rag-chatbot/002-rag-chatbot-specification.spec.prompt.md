---
id: 002
title: RAG Chatbot Specification Update
stage: spec
date: 2025-12-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-rag-chatbot
branch: 001-rag-chatbot
user: Administrator
command: /sp.specify
labels: ["spec", "rag", "chatbot", "cohere", "qdrant", "neon", "fastapi"]
links:
  spec: ../specs/001-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-rag-chatbot/spec.md
tests:
  - none
---

## Prompt

/sp.specify

Project: RAG Chatbot (Cohere + FastAPI + Qdrant + Neon)

Key Components:
- Cohere LLM + embedding models
- FastAPI backend serving retrieval + generation endpoints
- Qdrant Cloud (Free Tier) for vector embeddings
- Neon Serverless Postgres for metadata + chunk mapping
- spec-kit-plus + claude-code CLI for full code generation

Functional Requirements:
1. Embed full book content into Qdrant using Cohere embeddings (embed-english-v3.0).
2. Store metadata (chapter_id, section_name, chunk_ids, token_count) in Neon Postgres.
3. Provide two retrieval modes:
   - Standard RAG retrieval (top-k = 4)
   - User-selected-text RAG (context override)
4. Use Cohere Rerank before sending final chunks to generator model.
5. Expose the following FastAPI routes:
   - POST /embed → Store embeddings + metadata
   - POST /query → Perform RAG answer
   - POST /selected-query → Only use provided selected text
   - GET /health → Ping test
6. Agent must follow Constitution rules:
   - No hallucinations
   - Only answer from retrieved content
   - Cite chapter/section
7. Output must be clean JSON for easy embedding inside the book.

Technology Constraints:
- Vector DB: Qdrant Cloud
- Metadata DB: Neon Serverless Postgres
- Models: Cohere generate + Cohere rerank + Cohere embedding
- Max chunk size: 700 tokens
- Retrieval top_k: 4
- Rerank top_n: 3
- Response max_length: 200 words unless requested

Environment Variables (Use placeholders in code):
- QDRANT_API_KEY = "<QDRANT_API_KEY>"
- QDRANT_URL = "<QDRANT_URL>"
- QDRANT_CLUSTER_ID = "<CLUSTER_ID>"
- NEON_DB_URL = "<NEON_DB_URL>"
- COHERE_API_KEY = "<COHERE_API_KEY>"

Code Expectations:
- Auto-generate complete folder structure
- Include DB migrations
- Fully typed Python (FastAPI + Pydantic)
- Connection pooling for Postgres

Success Criteria:
- Answers grounded strictly in book data
- Context override works flawlessly for selected-text mode
- API latency under 500ms for retrieval
- RAG pipeline passes factuality benchmark ≥95%
- Ready for embedding inside the published book (React/Next.js or ePub webview)

## Response snapshot

Updated specification for RAG Chatbot (v2.0.0) with Cohere + Qdrant + Neon stack:

**4 User Stories (Prioritized P1-P2)**:
1. Standard Question Answering (P1) - Core MVP, vector search + rerank + citations
2. User-Selected Text Mode (P1) - Context override, aligns with Constitution Principle III
3. Book Content Ingestion (P1) - Foundational infrastructure for knowledge base
4. Health Check and Monitoring (P2) - Production reliability, non-blocking for MVP

**20 Functional Requirements (FR-001 to FR-020)**:
- Cohere embed-english-v3.0 for embeddings
- Neon Postgres for metadata (chapter_id, section_name, chunk_id)
- Standard RAG: query → Qdrant (top_k=4) → Cohere Rerank (top_n=3) → generate
- Selected-text mode: bypass search, answer from user text only
- 4 API endpoints: POST /embed, POST /query, POST /selected-query, GET /health
- Zero hallucination enforcement (FR-009), transparency (FR-008), context prioritization (FR-010)

**10 Success Criteria (SC-001 to SC-010)**:
- Zero hallucinations (100% traceability)
- Context override works flawlessly (100% selected-text accuracy)
- <500ms API latency (p95)
- ≥95% factuality benchmark
- Full book indexing in <5 minutes
- 100 concurrent users without degradation

**Non-Functional Requirements**:
- Performance: <500ms query, 100ms Qdrant search, 150ms rerank
- Reliability: Retry logic, graceful degradation, connection pooling
- Security: Environment variables, rate limiting (100 req/min), input validation
- Observability: Structured logs, Prometheus metrics, correlation IDs

**API Contracts**: Full request/response schemas for all 4 endpoints with error codes

**Database Schema**: Neon Postgres tables (chapters, chunks) with indexes

**Constitution Alignment**:
- Principle I: FR-009 (zero hallucinations)
- Principle II: FR-001, FR-006 (Cohere-native)
- Principle III: FR-010, POST /selected-query (context prioritization)
- Principle IV: FR-008 (transparency)
- Principle V: 200-word responses, citations (academic clarity)

**Folder Structure**: Backend layout with FastAPI routers, services, db clients, tests

**Open Questions**: 5 questions for clarification (multi-book support, book size, page numbers, conversation history, rate limit behavior)

## Outcome

- ✅ Impact: Created comprehensive RAG chatbot specification (v2.0.0) with Cohere+Qdrant+Neon stack, replacing Google Gemini from v1.0.0; aligned all requirements with constitution principles
- 🧪 Tests: No automated tests (documentation artifact)
- 📁 Files: specs/001-rag-chatbot/spec.md (updated from v1.0.0 to v2.0.0)
- 🔁 Next prompts: Run /sp.plan for architectural design, then /sp.tasks for implementation breakdown; consider ADR for stack selection (Cohere+Qdrant+Neon)
- 🧠 Reflection: Specification provides clear technical contracts (API, database, folder structure) and constitution alignment, enabling straightforward implementation planning

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A (specification document)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate spec completeness by running /sp.plan and checking for missing technical details or ambiguities
