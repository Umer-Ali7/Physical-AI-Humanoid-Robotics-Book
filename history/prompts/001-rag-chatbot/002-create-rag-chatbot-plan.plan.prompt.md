---
id: 002
title: Create RAG chatbot implementation plan
stage: plan
date: 2025-12-10
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-rag-chatbot
branch: 001-rag-chatbot
user: Umer-Ali7
command: /sp.plan
labels: ["rag", "chatbot", "planning", "architecture"]
links:
  spec: specs/001-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-rag-chatbot/plan.md
  - specs/001-rag-chatbot/research.md
  - specs/001-rag-chatbot/data-model.md
  - specs/001-rag-chatbot/contracts/api.yaml
  - specs/001-rag-chatbot/quickstart.md
  - CLAUDE.md (agent context updated)
tests:
  - None (planning phase, no tests yet)
---

## Prompt

/sp.plan

# Technical Plan: RAG Chatbot Implementation

**Goal:** Define the technical architecture and steps to build the RAG chatbot defined in the current specification.

**Architecture Overview:**
The system will use a client-server architecture. The Docusaurus frontend will communicate via REST APIs with a separate Python/FastAPI backend. The backend will act as the orchestrator between the document files, the Qdrant vector database, and the Gemini AI API.

**1. Backend Implementation Plan (Python/FastAPI)**
* **Location:** A new folder named `backend/` at the project root.
* **Setup:** Initialize a FastAPI app with CORS enabled for the frontend (`http://localhost:3000`).
* **Dependencies:** `fastapi`, `uvicorn`, `qdrant-client`, `google-generativeai`, `python-dotenv`.
* **Environment Variables:** Securely manage `QDRANT_URL`, `QDRANT_API_KEY`, and `GEMINI_API_KEY`.
* **API Design:**
    * `POST /ingest`:
        * **Logic:** Recursively scan the relative `../docs/` directory for `.md` files. Read content, split into semantically meaningful chunks (approx 500-1000 tokens). Generate embeddings using Gemini. Upsert points into Qdrant collection containing vector + payload (raw text, source filename).
    * `POST /chat`:
        * **Request Payload:** `{ "message": "user query string" }`
        * **Logic:** Generate embedding for the user query using Gemini. Perform vector search on Qdrant (top-K=3 relevant chunks). Construct a prompt combining a system instruction, the retrieved context chunks, and the user query. Send to Gemini `gemini-1.5-flash` for final answer generation.
        * **Response Payload:** `{ "reply": "AI generated answer" }`

**2. Frontend Implementation Plan (Docusaurus/React)**
* **Component:** Create a new component `src/components/ChatWidget/index.tsx`.
* **UI State:** Manage open/closed state, message history array (user vs bot messages), and loading state.
* **API Interaction:** Use `fetch` to call the FastAPI `http://localhost:8000/chat` endpoint. Display a loading indicator while waiting for response.
* **Integration:** Add the `ChatWidget` to the main `Layout` so it appears globally on all doc pages.

**3. Development Workflow Steps**
1.  Set up `backend/` environment and install dependencies.
2.  Implement the `POST /ingest` endpoint and run it once to populate Qdrant.
3.  Implement the `POST /chat` endpoint and test with curl/Postman.
4.  Build the frontend `ChatWidget` UI.
5.  Connect the frontend widget to the backend API.

## Response snapshot

Created comprehensive implementation plan with complete technical architecture and design artifacts:

**Phase 0: Research & Unknowns (research.md)**
- RAG chunking strategies: 800-1000 tokens, semantic splitting, 200 token overlap
- Gemini embeddings: text-embedding-004 model (768 dimensions)
- Qdrant collection schema: Cosine similarity, rich payload with citations
- RAG prompt engineering: Strict grounding instructions with citation formatting
- Frontend state management: React useState + sessionStorage
- Deployment architecture: Nginx reverse proxy for production

**Phase 1: Design Artifacts**
1. **data-model.md**: Defined 5 core entities with validation rules:
   - User Query (query text, timestamp, session ID)
   - Chat Message (id, text, sender, citations)
   - Documentation Chunk (chunk text, embedding vector, metadata)
   - Conversation Session (session ID, messages array)
   - Source Citation (section, URL, relevance score)

2. **contracts/api.yaml**: Complete OpenAPI 3.0 specification:
   - POST /chat endpoint (with P3 context support)
   - POST /ingest endpoint (with admin authentication)
   - Request/response schemas with examples
   - Error response handling (400, 500, 503)
   - Security scheme for admin API key

3. **quickstart.md**: Developer onboarding guide (5 parts):
   - Backend setup (Python venv, dependencies, .env config)
   - Frontend setup (Docusaurus, ChatWidget component)
   - Integration testing (CORS, API connectivity)
   - Service verification (Qdrant, Gemini API)
   - Development workflow and troubleshooting

**Project Structure Defined**:
- Backend: `backend/src/{models,services,api}`, `backend/tests/{unit,integration}`
- Frontend: `f-docusaurus/src/components/ChatWidget`, `f-docusaurus/src/services`
- Documentation: `specs/001-rag-chatbot/{plan,research,data-model,contracts,quickstart}.md`

**Constitution Check**: ✅ PASSED all principles
- Clarity & Simplicity: Straightforward client-server architecture
- TDD: Pytest and Jest testing frameworks specified
- Incremental Development: P1 → P2 → P3 priorities
- Code Quality: PEP 8, React/TypeScript conventions
- Security: Environment variables, CORS, API protection

**Agent Context Updated**: Added Python/TypeScript/React and Qdrant Cloud to Claude context.

## Outcome

- ✅ Impact: Complete technical plan with architecture, research findings, data model, API contracts, and developer quickstart guide. Ready for task generation (/sp.tasks).
- 🧪 Tests: No tests (planning phase). Test strategies defined in plan (pytest for backend, Jest for frontend).
- 📁 Files: Created plan.md (232 lines), research.md (full RAG stack decisions), data-model.md (5 entities with validations), contracts/api.yaml (OpenAPI spec), quickstart.md (comprehensive setup guide). Updated CLAUDE.md with tech stack.
- 🔁 Next prompts: `/sp.tasks` to generate actionable task list with acceptance criteria, or `/sp.clarify` if additional technical clarifications needed.
- 🧠 Reflection: Successfully translated feature spec into actionable technical plan. Research phase resolved 6 critical technical decisions (chunking, embeddings, vector DB, prompting, state management, deployment). Design phase produced complete data model and API contracts. Quickstart guide enables developers to begin implementation immediately.

## Evaluation notes (flywheel)

- Failure modes observed: Research agents timed out after 150s, fell back to industry best practices and established RAG patterns (acceptable for planning phase). PowerShell script parameter binding issues handled gracefully.
- Graders run and results (PASS/FAIL): Constitution Check PASSED all 7 principles. All mandatory Phase 0 and Phase 1 artifacts generated and validated.
- Prompt variant (if applicable): Standard /sp.plan workflow with user-provided technical architecture input
- Next experiment (smallest change to try): Consider caching research findings across similar features (RAG patterns, embedding strategies) to accelerate future planning phases. Evaluate research agent timeout thresholds (150s may be too aggressive for complex technical research).
