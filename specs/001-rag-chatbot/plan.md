# Claude Code Project Implementation Plan: RAG-Powered Documentation Chatbot

**Branch**: `001-rag-chatbot` | **Date**: 2025-12-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-rag-chatbot/spec.md`

## Summary

This feature implements a Retrieval-Augmented Generation (RAG) chatbot for the Physical AI documentation site. Users will interact with a floating chat widget on the Docusaurus frontend that communicates with a Python FastAPI backend. The backend orchestrates between markdown documentation files, Qdrant Cloud vector database for semantic search, and Google Gemini API for embeddings and text generation. The system enables users to ask natural language questions and receive accurate, citation-backed answers grounded solely in the documentation content.

**Primary Technical Approach**:
- **Client-Server Architecture**: Docusaurus (React) frontend with REST API communication to FastAPI backend
- **RAG Pipeline**: Document ingestion → chunk & embed → store in Qdrant → retrieve relevant chunks → generate answer with Gemini
- **Phase Implementation**: P1 (core Q&A) → P2 (citations + ingestion) → P3 (conversation context)

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/React (frontend via Docusaurus)
**Primary Dependencies**:
- Backend: `fastapi`, `uvicorn`, `qdrant-client`, `google-generativeai`, `python-dotenv`
- Frontend: Existing Docusaurus 3.x with React components
**Storage**: Qdrant Cloud (vector database for document embeddings and metadata)
**Testing**: pytest (backend unit/integration tests), Jest/React Testing Library (frontend component tests)
**Target Platform**:
- Backend: Linux/Windows server (FastAPI with uvicorn ASGI server)
- Frontend: Modern web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (backend + frontend)
**Performance Goals**:
- <10 seconds response time for 95% of queries
- Support 50+ concurrent users
- Process 50-100 markdown files in <15 minutes during ingestion
**Constraints**:
- English-only MVP
- Session-scoped conversation history (resets on page navigation)
- Responses must be grounded in documentation only (no external knowledge)
- API keys must be environment variables (not hardcoded)
**Scale/Scope**:
- ~50-100 documentation markdown files
- Estimated 50-100 concurrent users at launch
- Single Qdrant collection with ~500-2000 chunks (depending on doc size)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Clarity and Simplicity
- **Status**: PASS
- **Rationale**: Architecture is straightforward client-server with clear separation of concerns. Backend handles RAG pipeline, frontend handles UI. No unnecessary abstractions.

### ✅ II. Test-Driven Development (TDD)
- **Status**: PASS
- **Rationale**: Plan includes pytest for backend (API endpoints, embedding logic, retrieval) and Jest for frontend (component rendering, API calls). TDD cycle will be enforced in tasks.

### ✅ III. Incremental Development
- **Status**: PASS
- **Rationale**: Feature is decomposed into independently deliverable priorities (P1: core Q&A, P2: citations + ingestion, P3: conversation context). Each can be deployed separately.

### ✅ IV. Code Quality
- **Status**: PASS
- **Rationale**: Python backend will follow PEP 8, FastAPI best practices. Frontend follows React/TypeScript conventions. Code reviews required before merge.

### ✅ V. Security by Design
- **Status**: PASS
- **Rationale**: API keys stored in environment variables. CORS configured for specific frontend origin. No user authentication required for MVP (public documentation), but ingestion endpoint will be admin-only or IP-restricted. Input validation on query length to prevent abuse.

### ✅ Additional Constraints
- **Status**: PASS
- **Rationale**: Cloud-native approach using Qdrant Cloud (managed service) and stateless FastAPI backend (horizontally scalable). Technology choices (FastAPI, Qdrant, Gemini) align with modern cloud-native principles.

### ✅ Development Workflow
- **Status**: PASS
- **Rationale**: All changes will go through PR review. CI checks (linting, tests) will run on backend and frontend before merge.

**Overall Gate Status**: ✅ **PASSED** - Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-rag-chatbot/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── api.yaml         # OpenAPI spec for /chat and /ingest endpoints
│   └── events.md        # Frontend-backend interaction events (optional)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Backend API
backend/
├── src/
│   ├── main.py                 # FastAPI app entry point, CORS config
│   ├── config.py               # Environment variable loading (.env)
│   ├── models/
│   │   ├── request.py          # ChatRequest, IngestRequest Pydantic models
│   │   └── response.py         # ChatResponse, IngestResponse Pydantic models
│   ├── services/
│   │   ├── embedding.py        # Gemini embedding generation
│   │   ├── vectordb.py         # Qdrant client wrapper (upsert, search)
│   │   ├── ingestion.py        # Markdown file processing, chunking
│   │   └── generation.py       # Gemini text generation (RAG prompting)
│   └── api/
│       ├── chat.py             # POST /chat endpoint
│       └── ingest.py           # POST /ingest endpoint
├── tests/
│   ├── unit/
│   │   ├── test_embedding.py
│   │   ├── test_chunking.py
│   │   └── test_generation.py
│   └── integration/
│       ├── test_chat_api.py
│       └── test_ingest_api.py
├── requirements.txt
├── .env.example
└── README.md

# Frontend (Docusaurus integration)
f-docusaurus/
├── src/
│   ├── components/
│   │   └── ChatWidget/
│   │       ├── index.tsx           # Main chat widget component
│   │       ├── ChatButton.tsx      # Floating button
│   │       ├── ChatWindow.tsx      # Chat conversation window
│   │       ├── MessageList.tsx     # Message history display
│   │       ├── MessageInput.tsx    # Input field with send button
│   │       ├── Citation.tsx        # Source citation display (P2)
│   │       ├── styles.module.css   # Component styles
│   │       └── types.ts            # TypeScript interfaces
│   ├── theme/
│   │   └── Layout/
│   │       └── index.tsx           # Docusaurus layout override to add ChatWidget globally
│   └── services/
│       └── chatApi.ts              # API client for /chat endpoint
├── __tests__/
│   └── components/
│       └── ChatWidget.test.tsx
└── docusaurus.config.ts            # No changes needed (global layout handles widget)
```

**Structure Decision**: Selected **Option 2: Web application** structure with separate `backend/` and `frontend/` directories. The backend is a standalone FastAPI service, and the frontend integrates into the existing Docusaurus site (`f-docusaurus/`). This separation enables independent deployment, testing, and scaling of backend vs frontend components.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. All principles pass.*

## Phase 0: Research & Unknowns

### Research Tasks

1. **RAG Chunking Strategies**:
   - **Question**: What's the optimal chunk size and overlap for Docusaurus markdown documentation to balance context vs retrieval precision?
   - **Research Areas**: Semantic chunking vs fixed-size chunking, handling code blocks and tables, preserving section headers for context

2. **Gemini Embedding Best Practices**:
   - **Question**: Which Gemini embedding model (`embedding-001` vs others) is best for technical documentation retrieval, and what are the optimal embedding parameters?
   - **Research Areas**: Model dimensions, cost vs quality tradeoffs, batch processing limits

3. **Qdrant Collection Schema**:
   - **Question**: How should the Qdrant collection be structured for optimal retrieval (vector dimensions, payload schema, indexing strategy)?
   - **Research Areas**: Collection configuration, payload fields for citations, filtering strategies

4. **RAG Prompt Engineering**:
   - **Question**: What prompt template structure ensures accurate, grounded responses with minimal hallucination?
   - **Research Areas**: System instructions, context formatting, citation instructions, handling "I don't know" cases

5. **Frontend State Management**:
   - **Question**: Should conversation history be managed in React component state, Context API, or external state library (e.g., Zustand)?
   - **Research Areas**: React best practices for chat widgets, session persistence options, performance considerations

6. **CORS and Deployment**:
   - **Question**: What's the recommended deployment architecture for FastAPI + Docusaurus (same domain vs subdomain vs separate domains)?
   - **Research Areas**: CORS configuration, reverse proxy patterns, security implications

### Research Output

*Research findings will be documented in `research.md` with decisions, rationale, and alternatives considered.*

## Phase 1: Design Artifacts

### Artifacts to Generate

1. **`data-model.md`**: Entity definitions and relationships
   - User Query
   - Chat Message
   - Documentation Chunk
   - Conversation Session
   - Source Citation

2. **`contracts/api.yaml`**: OpenAPI specification for:
   - `POST /chat` endpoint (request/response schemas)
   - `POST /ingest` endpoint (request/response schemas)
   - Error response schemas

3. **`quickstart.md`**: Developer setup guide
   - Backend setup (Python venv, install dependencies, configure `.env`)
   - Frontend setup (integrate ChatWidget into Docusaurus)
   - Running ingestion
   - Testing the chat endpoint

### Design Decisions (Post-Research)

*Will be populated after Phase 0 research completion.*

## Phase 2: Task Breakdown

*This phase is handled by the `/sp.tasks` command, not `/sp.plan`. The task list will be generated based on the design artifacts from Phase 1.*

**Expected Task Categories**:
- Backend: API endpoint implementation (chat, ingest)
- Backend: RAG pipeline services (embedding, retrieval, generation)
- Backend: Testing (unit tests for services, integration tests for endpoints)
- Frontend: ChatWidget component development
- Frontend: API integration and error handling
- Frontend: Testing (component tests, E2E tests)
- Deployment: Environment setup, CORS configuration, deployment scripts
- Documentation: API documentation, developer guides

## Notes

- **Technology Constraints**: Per spec requirements, this plan uses Python/FastAPI backend, Qdrant Cloud vector DB, and Google Gemini API (non-negotiable).
- **MVP Scope**: Focus on P1 (core Q&A) first, then P2 (citations + ingestion), then P3 (conversation context). Each priority is independently deployable.
- **Security**: API keys must never be committed. Use `.env` file locally and environment variables in production. Ingestion endpoint should be protected (IP whitelist or admin token).
- **Future Enhancements**: After MVP, consider adding feedback buttons (thumbs up/down), conversation export, analytics integration, and multi-language support.
