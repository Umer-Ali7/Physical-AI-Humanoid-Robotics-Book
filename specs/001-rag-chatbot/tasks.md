# Claude Code Project Tasks: RAG-Powered Documentation Chatbot

**Input**: Design documents from `/specs/001-rag-chatbot/`
**Prerequisites**: plan.md (technical architecture), spec.md (user stories), research.md (technical decisions), data-model.md (entities), contracts/api.yaml (API spec)

**Tests**: Per the constitution, ALL features require Test-Driven Development. Tests are included in this task list and MUST be written BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

This is a **Web application** with:
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `f-docusaurus/src/`, `f-docusaurus/__tests__/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend directory structure: `backend/src/{models,services,api}`, `backend/tests/{unit,integration}`
- [X] T002 Create frontend component structure: `f-docusaurus/src/components/ChatWidget`, `f-docusaurus/src/services`
- [X] T003 Initialize Python virtual environment in `backend/` and install dependencies from `backend/requirements.txt`
- [X] T004 [P] Create `backend/.env.example` template with all required environment variables (QDRANT_URL, QDRANT_API_KEY, GEMINI_API_KEY, DOCS_PATH, CORS_ORIGINS, ADMIN_API_KEY)
- [X] T005 [P] Create `backend/.gitignore` to exclude `.env`, `venv/`, `__pycache__/`, `.pytest_cache/`
- [X] T006 [P] Configure pytest in `backend/pytest.ini` for unit and integration test discovery
- [X] T007 [P] Configure ESLint and TypeScript for frontend in `f-docusaurus/` (if not already configured)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create `backend/src/config.py` to load environment variables using python-dotenv and pydantic-settings
- [X] T009 Create `backend/src/main.py` FastAPI application with CORS middleware configured for `http://localhost:3000`
- [X] T010 [P] Create Pydantic models in `backend/src/models/request.py`: `ChatRequest`, `IngestRequest`
- [X] T011 [P] Create Pydantic models in `backend/src/models/response.py`: `ChatResponse`, `Citation`, `IngestResponse`, `ErrorResponse`
- [X] T012 Initialize Qdrant client wrapper in `backend/src/services/vectordb.py` with connection testing
- [X] T013 Create Gemini API client wrapper in `backend/src/services/embedding.py` for text-embedding-004 model
- [X] T014 [P] Implement health check endpoint `GET /health` in `backend/src/main.py`
- [X] T015 [P] Implement root endpoint `GET /` in `backend/src/main.py` returning API info
- [X] T016 Create base error handling middleware in `backend/src/main.py` for 400/500/503 responses
- [X] T017 Configure logging infrastructure in `backend/src/main.py` using Python logging module

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ask Documentation Questions (Priority: P1) 🎯 MVP

**Goal**: Users can click a floating chat button, ask a question, and receive an AI-generated answer grounded in documentation within 10 seconds.

**Independent Test**: Open chat widget on any docs page, type "What is a ROS 2 node?", press Enter, and receive a relevant answer from documentation within 10 seconds.

### Tests for User Story 1 ⚠️ RED PHASE

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T018 [P] [US1] Create unit test for embedding service in `backend/tests/unit/test_embedding.py` - test generate_embedding() with sample text
- [X] T019 [P] [US1] Create unit test for Qdrant service in `backend/tests/unit/test_vectordb.py` - test search() with mock vectors
- [X] T020 [P] [US1] Create unit test for generation service in `backend/tests/unit/test_generation.py` - test generate_response() with mock chunks
- [X] T021 [P] [US1] Create integration test for `/chat` endpoint in `backend/tests/integration/test_chat_api.py` - test full query flow
- [X] T022 [P] [US1] Create React component test for ChatWidget in `f-docusaurus/__tests__/components/ChatWidget.test.tsx` - test open/close, message display

### Implementation for User Story 1 - GREEN PHASE

**Backend Services**:

- [X] T023 [P] [US1] Implement `generate_embedding(text: str)` in `backend/app/services/embedding.py` using Cohere embed-english-v3.0
- [X] T024 [P] [US1] Implement `search(query_vector, top_k)` in `backend/app/services/retrieval.py` for Qdrant semantic search
- [X] T025 [US1] Implement `generate_response(chunks, query)` in `backend/app/services/generation.py` using Cohere command-r-plus with strict grounding prompt
- [X] T026 [US1] Implement RAG pipeline orchestration in `backend/app/services/rag_pipeline.py` combining embedding → search → generation

**Backend API**:

- [X] T027 [US1] Implement `POST /chat` endpoint in `backend/app/routers/chat.py` with request validation, RAG pipeline call, and error handling
- [X] T028 [US1] Add `/chat` endpoint to FastAPI router in `backend/app/main.py`
- [X] T029 [US1] Add input validation for query length (1-2000 chars) in `backend/app/models/requests.py` (QueryRequest model)
- [X] T030 [US1] Implement "no results found" handling in `backend/app/services/rag_pipeline.py` when semantic search returns empty or low-score results

**Frontend Components**:

- [X] T031 [P] [US1] Create TypeScript interfaces in `f-docusaurus/src/components/ChatWidget/types.ts`: `ChatMessage`, `ChatWidgetProps`
- [X] T032 [P] [US1] Implement ChatButton component in `f-docusaurus/src/components/ChatWidget/ChatButton.tsx` with floating button styling
- [X] T033 [P] [US1] Implement ChatWindow component in `f-docusaurus/src/components/ChatWidget/ChatWindow.tsx` with header and close button
- [X] T034 [P] [US1] Implement MessageList component in `f-docusaurus/src/components/ChatWidget/MessageList.tsx` for displaying user/AI messages
- [X] T035 [P] [US1] Implement MessageInput component in `f-docusaurus/src/components/ChatWidget/MessageInput.tsx` with text input and send button
- [X] T036 [US1] Implement API client in `f-docusaurus/src/services/chatApi.ts` with `sendMessage(query: string)` function calling `POST /chat`
- [X] T037 [US1] Integrate all components in `f-docusaurus/src/components/ChatWidget/index.tsx` with state management (useState for messages, isOpen, isLoading)
- [X] T038 [US1] Add ChatWidget to global Layout by swizzling `f-docusaurus/src/theme/Layout/index.tsx`
- [X] T039 [US1] Style ChatWidget components in `f-docusaurus/src/components/ChatWidget/styles.module.css` with responsive design
- [X] T040 [US1] Implement loading indicator in MessageList component while waiting for AI response
- [X] T041 [US1] Add error message display in ChatWindow when API call fails (503, 500, 400 errors)

**Session Storage**:

- [ ] T042 [US1] Implement conversation history persistence using sessionStorage in `f-docusaurus/src/components/ChatWidget/index.tsx`
- [ ] T043 [US1] Implement session history restoration on component mount from sessionStorage

**Checkpoint**: At this point, User Story 1 should be fully functional - users can ask questions and get answers from documentation

---

## Phase 4: User Story 2 - View Answer Sources and Citations (Priority: P2)

**Goal**: Users can see source citations with AI answers and click links to navigate to the original documentation pages.

**Independent Test**: Ask a question via chat, receive an answer, and verify that source references (e.g., "[Source 1]") are displayed with clickable links to documentation pages.

### Tests for User Story 2 ⚠️ RED PHASE

- [ ] T044 [P] [US2] Create unit test for citation extraction in `backend/tests/unit/test_citations.py` - test parse_citations() function
- [ ] T045 [P] [US2] Update integration test in `backend/tests/integration/test_chat_api.py` - verify `citations` array in response
- [ ] T046 [P] [US2] Create React component test for Citation component in `f-docusaurus/__tests__/components/Citation.test.tsx`

### Implementation for User Story 2 - GREEN PHASE

**Backend - Citation Logic**:

- [ ] T047 [US2] Update `search()` in `backend/src/services/vectordb.py` to return chunk metadata (section_title, page_url, relevance_score)
- [ ] T048 [US2] Update RAG prompt template in `backend/src/services/generation.py` to include numbered sources [Source 1], [Source 2], [Source 3]
- [ ] T049 [US2] Implement citation extraction logic in `backend/src/services/generation.py` to create `Citation` objects from chunk metadata
- [ ] T050 [US2] Update `/chat` endpoint response in `backend/src/api/chat.py` to include `citations` array in `ChatResponse`

**Frontend - Citation Display**:

- [ ] T051 [P] [US2] Create `Citation` TypeScript interface in `f-docusaurus/src/components/ChatWidget/types.ts`
- [ ] T052 [P] [US2] Implement Citation component in `f-docusaurus/src/components/ChatWidget/Citation.tsx` with clickable link to page_url
- [ ] T053 [US2] Update MessageList component in `f-docusaurus/src/components/ChatWidget/MessageList.tsx` to display citations below AI messages
- [ ] T054 [US2] Style citations in `f-docusaurus/src/components/ChatWidget/styles.module.css` with distinct visual styling
- [ ] T055 [US2] Update `chatApi.ts` to handle `citations` field in API response

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users get answers with verifiable source citations

---

## Phase 5: User Story 3 - Maintain Conversation Context (Priority: P3)

**Goal**: Users can ask follow-up questions that reference previous messages in the same session, and the chatbot understands the context.

**Independent Test**: Ask "What is ROS 2?", receive an answer, then ask "What are its main components?" and verify the answer maintains context from the first question.

### Tests for User Story 3 ⚠️ RED PHASE

- [ ] T056 [P] [US3] Create unit test for context handling in `backend/tests/unit/test_context.py` - test build_context_prompt() function
- [ ] T057 [P] [US3] Update integration test in `backend/tests/integration/test_chat_api.py` - test multi-turn conversation with context

### Implementation for User Story 3 - GREEN PHASE

**Backend - Conversation Context**:

- [ ] T058 [US3] Update `ChatRequest` model in `backend/src/models/request.py` to include optional `session_id` and `context_messages` fields
- [ ] T059 [US3] Implement context-aware prompt building in `backend/src/services/generation.py` - include previous messages in prompt
- [ ] T060 [US3] Update RAG pipeline in `backend/src/services/rag_pipeline.py` to handle conversation history
- [ ] T061 [US3] Update `/chat` endpoint in `backend/src/api/chat.py` to accept and process `context_messages`

**Frontend - Conversation Context**:

- [ ] T062 [US3] Generate UUID session_id on first interaction in `f-docusaurus/src/components/ChatWidget/index.tsx`
- [ ] T063 [US3] Update `chatApi.ts` to send `session_id` and `context_messages` in request payload
- [ ] T064 [US3] Implement conversation history limit (max 100 messages) in ChatWidget state management
- [ ] T065 [US3] Clear conversation history on page navigation (sessionStorage key scoping)

**Checkpoint**: All P1-P3 user stories should now be independently functional - users have full conversational experience

---

## Phase 6: User Story 4 - Re-ingest Documentation Updates (Priority: P2)

**Goal**: Maintainers can trigger a re-ingestion endpoint to process updated documentation files and update the vector database.

**Independent Test**: Update a markdown file in docs, trigger `POST /ingest`, wait for completion, then ask a question about the updated content and verify the answer reflects the new information.

### Tests for User Story 4 ⚠️ RED PHASE

- [ ] T066 [P] [US4] Create unit test for chunking logic in `backend/tests/unit/test_chunking.py` - test split_markdown() function
- [ ] T067 [P] [US4] Create unit test for file scanning in `backend/tests/unit/test_file_scanner.py` - test scan_markdown_files() function
- [ ] T068 [P] [US4] Create integration test for `/ingest` endpoint in `backend/tests/integration/test_ingest_api.py` - test full ingestion flow

### Implementation for User Story 4 - GREEN PHASE

**Backend - Ingestion Services**:

- [X] T069 [P] [US4] Implement markdown file scanner in `backend/app/services/ingestion.py` with file scanning from docs directory
- [X] T070 [P] [US4] Implement semantic chunking logic in `backend/app/services/chunking.py` with `chunk_markdown()` using 1000 char chunks, 200 char overlap
- [X] T071 [US4] Implement batch embedding generation in `backend/app/services/embedding.py` with `generate_embeddings_batch()` using Cohere
- [X] T072 [US4] Qdrant collection initialization already implemented in `backend/app/db/qdrant_client.py` (1024 dimensions for Cohere, cosine distance)
- [X] T073 [US4] Implement chunk upsert logic in `backend/app/services/ingestion.py` using UUID as unique ID
- [X] T074 [US4] Implement ingestion orchestration in `backend/app/services/ingestion.py` combining scan → chunk → embed → upsert with progress logging

**Backend - Ingestion API**:

- [X] T075 [US4] Implement `POST /api/v1/ingest` endpoint in `backend/app/routers/ingest.py` with admin API key authentication (X-Admin-API-Key header)
- [X] T076 [US4] Add `/ingest` endpoint to FastAPI router in `backend/app/main.py`
- [X] T077 [US4] Add request validation for docs_path in `backend/app/routers/ingest.py` (IngestRequest model)
- [X] T078 [US4] Implement progress logging during ingestion (file count, chunk count, duration)
- [X] T079 [US4] Implement error handling for failed files in ingestion with detailed error messages
- [X] T080 [US4] Add force_reindex option to delete existing collection before ingestion

**Checkpoint**: All user stories complete - maintainers can update documentation and users get fresh answers

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T081 [P] Create backend README in `backend/README.md` with setup instructions, API documentation, environment variables
- [ ] T082 [P] Create test verification script `backend/test_qdrant.py` to verify Qdrant connectivity
- [ ] T083 [P] Create test verification script `backend/test_gemini.py` to verify Gemini API connectivity
- [ ] T084 [P] Add rate limiting middleware to `/chat` endpoint (10 requests/minute per IP) using slowapi or custom middleware
- [ ] T085 [P] Add request logging middleware in `backend/src/main.py` for all API calls
- [ ] T086 [P] Implement graceful error messages for all edge cases: no results, service unavailable, invalid query
- [ ] T087 [P] Add dark mode theme support for ChatWidget in `f-docusaurus/src/components/ChatWidget/styles.module.css`
- [ ] T088 [P] Implement responsive design for ChatWidget on mobile devices (breakpoints, touch optimization)
- [ ] T089 [P] Add accessibility features to ChatWidget (ARIA labels, keyboard navigation, focus management)
- [ ] T090 [P] Create deployment documentation in `specs/001-rag-chatbot/deployment.md` with nginx reverse proxy configuration
- [ ] T091 Perform end-to-end testing following `specs/001-rag-chatbot/quickstart.md` validation steps
- [ ] T092 Run full backend test suite: `cd backend && pytest tests/ -v` and ensure all tests pass
- [ ] T093 Run full frontend test suite: `cd f-docusaurus && npm test` and ensure all tests pass
- [ ] T094 Performance testing: Verify <10 second response time for 95% of queries under 50 concurrent users
- [ ] T095 Security audit: Verify no API keys in code, CORS properly configured, admin endpoints protected
- [ ] T096 [P] Code cleanup and refactoring: Remove TODOs, unused imports, commented code
- [ ] T097 [P] Update main project README with RAG chatbot feature documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Core Q&A - MVP foundation
  - User Story 2 (P2): Citations - enhances US1, can start after US1 OR in parallel
  - User Story 3 (P3): Conversation context - enhances US1, can start after US1 OR in parallel
  - User Story 4 (P2): Ingestion - independent infrastructure, can start after Foundational
- **Polish (Phase 7)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **REQUIRED for MVP**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Enhances US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 but independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Completely independent from US1/US2/US3

### Within Each User Story (TDD Cycle)

1. **RED**: Write tests FIRST - ensure they FAIL
2. **GREEN**: Implement code to make tests PASS
3. **REFACTOR**: Clean up code while keeping tests GREEN

Sequence within each story:
- Tests (all parallelizable with [P])
- Models (parallelizable if different entities)
- Services (depend on models)
- API endpoints (depend on services)
- Frontend components (some parallelizable with [P])
- Integration and validation

### Parallel Opportunities

**Setup Phase**:
- T003, T004, T005, T006, T007 can all run in parallel

**Foundational Phase**:
- T010-T011 (models) can run in parallel
- T012-T013 (service setup) can run in parallel
- T014-T017 (endpoints and middleware) can run in parallel

**Once Foundational Completes - Maximum Parallelism**:
- User Story 1, 2, 3, 4 can ALL start in parallel (different team members)
- Within US1: T018-T022 (tests) parallel, T023-T024 (services) parallel, T031-T035 (components) parallel
- Within US2: T044-T046 (tests) parallel, T051-T052 (frontend) parallel
- Within US4: T066-T068 (tests) parallel, T069-T070 (services) parallel

---

## Parallel Example: User Story 1

```bash
# RED Phase - Launch all tests together:
Task: "Create unit test for embedding service in backend/tests/unit/test_embedding.py"
Task: "Create unit test for Qdrant service in backend/tests/unit/test_vectordb.py"
Task: "Create unit test for generation service in backend/tests/unit/test_generation.py"
Task: "Create integration test for /chat endpoint in backend/tests/integration/test_chat_api.py"
Task: "Create React component test for ChatWidget in f-docusaurus/__tests__/components/ChatWidget.test.tsx"

# GREEN Phase - Backend services in parallel:
Task: "Implement generate_embedding(text: str) in backend/src/services/embedding.py"
Task: "Implement search(query_vector, top_k) in backend/src/services/vectordb.py"

# GREEN Phase - Frontend components in parallel:
Task: "Create TypeScript interfaces in f-docusaurus/src/components/ChatWidget/types.ts"
Task: "Implement ChatButton component in f-docusaurus/src/components/ChatWidget/ChatButton.tsx"
Task: "Implement ChatWindow component in f-docusaurus/src/components/ChatWidget/ChatWindow.tsx"
Task: "Implement MessageList component in f-docusaurus/src/components/ChatWidget/MessageList.tsx"
Task: "Implement MessageInput component in f-docusaurus/src/components/ChatWidget/MessageInput.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007) - ~30 min
2. Complete Phase 2: Foundational (T008-T017) - ~2 hours
3. Complete Phase 3: User Story 1 (T018-T043) - ~6-8 hours
4. **STOP and VALIDATE**: Test User Story 1 independently per acceptance criteria
5. Deploy/demo if ready - **You have a working MVP!**

**MVP Scope**: 43 tasks total (Setup + Foundational + US1)
**Estimated Time**: 8-10 hours for full MVP

### Incremental Delivery

1. MVP (US1) → Users can ask questions and get answers ✅
2. Add US2 (Citations) → Users can verify answers with sources ✅
3. Add US4 (Ingestion) → Maintainers can update content ✅
4. Add US3 (Context) → Users get conversational experience ✅
5. Polish phase → Production-ready deployment ✅

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers:

1. **Day 1**: Team completes Setup + Foundational together (T001-T017)
2. **Day 2 onwards** (once Foundational done):
   - **Developer A**: User Story 1 (T018-T043) - Core MVP
   - **Developer B**: User Story 4 (T066-T080) - Ingestion infrastructure
   - **Developer C**: User Story 2 (T044-T055) - Citations (starts after US1 basics done)
3. Stories complete and integrate independently
4. **Final Integration**: User Story 3 (T056-T065) + Polish (T081-T097)

---

## Task Count Summary

- **Setup**: 7 tasks
- **Foundational**: 10 tasks (BLOCKS all stories)
- **User Story 1 (P1 - MVP)**: 26 tasks (5 tests + 21 implementation)
- **User Story 2 (P2)**: 12 tasks (3 tests + 9 implementation)
- **User Story 3 (P3)**: 10 tasks (2 tests + 8 implementation)
- **User Story 4 (P2)**: 15 tasks (3 tests + 12 implementation)
- **Polish**: 17 tasks
- **TOTAL**: 97 tasks

**Parallel Opportunities**: 45+ tasks marked with [P] can run in parallel

**MVP Scope**: 43 tasks (Setup + Foundational + US1)

**Estimated Delivery**:
- MVP (US1): 8-10 hours solo / 4-6 hours with 2 developers
- Full Feature (US1-4): 20-30 hours solo / 10-15 hours with 3 developers
- Production Ready (with Polish): 25-35 hours solo / 12-18 hours with 3 developers

---

## Notes

- **TDD Required**: Per constitution, write tests FIRST (RED), then implement (GREEN), then refactor
- **[P] tasks**: Different files, no dependencies - safe for parallel execution
- **[Story] labels**: Maps tasks to user stories for traceability and independent delivery
- **Each user story is independently completable and testable** - can deploy after any story
- **Verify tests FAIL before implementing** - ensures tests are valid
- **Commit after each task or logical group** - enables easy rollback
- **Stop at any checkpoint to validate story independently** - ensures quality
- **Avoid**: Vague tasks, same-file conflicts, cross-story dependencies that break independence
- **File paths are exact** - no ambiguity about where code belongs
- **MVP = User Story 1** - Delivers core value, enables early user feedback
