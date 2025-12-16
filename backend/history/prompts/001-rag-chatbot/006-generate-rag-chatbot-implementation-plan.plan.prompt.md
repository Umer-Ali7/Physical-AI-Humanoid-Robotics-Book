---
id: 006
title: Generate RAG Chatbot Implementation Plan
stage: plan
date: 2025-12-12
surface: agent
model: claude-sonnet-4-5
feature: 001-rag-chatbot
branch: 001-rag-chatbot
user: Administrator
command: /sp.plan
labels: ["planning", "architecture", "rag", "cohere", "fastapi", "qdrant", "neon"]
links:
  spec: specs/001-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-rag-chatbot/research.md
  - specs/001-rag-chatbot/data-model.md
  - specs/001-rag-chatbot/contracts/openapi.yaml
  - specs/001-rag-chatbot/contracts/README.md
  - specs/001-rag-chatbot/quickstart.md
  - specs/001-rag-chatbot/plan.md
  - .specify/memory/agent-context-claude.md
tests:
  - Constitution Check (all 5 principles validated)
  - Data model referential integrity verification
  - API contract schema completeness
  - Phase 0 research unknowns resolution
---

## Prompt

User invoked `/sp.plan` to execute the implementation planning workflow for the RAG Chatbot feature (001-rag-chatbot). The workflow includes:

1. **Phase 0 - Research**: Resolve all technical unknowns from the specification (chunking strategy, Cohere API integration, Qdrant architecture, Neon schema, FastAPI structure, RAG pipeline, testing strategy, environment config, deployment, open questions).

2. **Phase 1 - Design & Contracts**: Generate data model (Postgres + Qdrant schemas, Pydantic models), API contracts (OpenAPI 3.1.0 spec), quickstart guide (setup + testing), and update agent context.

3. **Constitution Check**: Validate alignment with all 5 constitution principles (Grounded Reasoning, Cohere-Native Alignment, Context Prioritization, Transparency, Academic Clarity).

4. **Plan Document**: Fill implementation plan template with technical context, project structure, complexity tracking, risk analysis, deployment strategy, and success metrics.

The feature implements a Retrieval-Augmented Generation (RAG) system for a Physical AI textbook with:
- Standard RAG mode (vector search → rerank → generate)
- User-selected-text mode (context override, bypasses vector search)
- Zero hallucination guarantee (all answers traceable or explicit "not in book" message)
- FastAPI backend with 4 endpoints (health, embed, query, selected-query)
- Dual storage: Qdrant (vectors) + Neon Postgres (metadata + citations)

## Response snapshot

Successfully completed all planning phases:

**Phase 0 - Research (research.md)**:
- Resolved chunking strategy: Sliding window with 100-token overlap, sentence-boundary-aware
- Cohere integration: Async client, exponential backoff (3 retries, factor 2)
- Qdrant architecture: Single collection, cosine similarity, batch upsert (100 points)
- Neon schema: Two tables (chapters, chunks), JSONB metadata, foreign key constraints
- FastAPI structure: Layered (routers → services → clients), async I/O
- RAG pipeline: Three-stage (Retrieve → Rerank → Generate), circuit breaker pattern
- Testing: Three-tier (unit, integration, factuality benchmarks)
- Deployment: Docker + Render/Railway/Fly.io
- Open questions: Single-book MVP, 1000-2000 chunks, no page numbers, stateless queries

**Phase 1 - Design & Contracts**:
- **data-model.md**: Complete Postgres schema (chapters, chunks tables with indexes), Qdrant collection config, Pydantic models (request/response), entity relationships, validation rules, state transitions, sample data
- **contracts/openapi.yaml**: Full OpenAPI 3.1.0 spec with 4 endpoints, request/response schemas, validation rules, error codes, examples for all scenarios (success, errors, out-of-scope)
- **contracts/README.md**: Contract documentation, testing tools (Schemathesis), constitution alignment mapping, error codes table
- **quickstart.md**: 10-step setup guide (15 minutes), prerequisites, database initialization, API testing examples, troubleshooting section
- **agent-context-claude.md**: Technology stack summary, project structure, design patterns, configuration management, testing strategy, constitution compliance mapping, performance targets, troubleshooting guide

**Constitution Check**: ✅ ALL PRINCIPLES SATISFIED
- Principle I (Grounded Reasoning): Enforced via chunk_ids traceability, similarity threshold 0.7, transparency fallback
- Principle II (Cohere-Native): All AI operations use Cohere (embed-english-v3.0, Rerank v3, Command-R-Plus)
- Principle III (Context Prioritization): Separate POST /selected-query endpoint bypasses vector search
- Principle IV (Transparency): Hardcoded "not in book" message when no chunks found
- Principle V (Academic Clarity): Citations in every response, 200-word default length

**Plan Document (plan.md)**:
- Technical context: Python 3.11, FastAPI, Cohere, Qdrant, Neon, performance targets (<500ms p95)
- Project structure: Web backend pattern, layered architecture, async I/O
- Complexity tracking: No constitution violations; dual storage justified for performance
- Risk analysis: 5 risks identified (Cohere rate limit, Qdrant exhaustion, Neon pool, hallucination edge cases, selected-text too short) with mitigations
- Deployment strategy: Render recommended, Dockerfile provided, health checks configured
- Success metrics: 10 measurable criteria (SC-001 to SC-010) with validation methods
- ADR suggestions: Cohere-exclusive stack, dual storage (Qdrant + Neon)

## Outcome

- ✅ Impact: Complete architectural plan with all design artifacts generated. Ready for task breakdown (/sp.tasks) and implementation.
- 🧪 Tests: Constitution check validated (5/5 principles satisfied), data model integrity verified, API contract completeness confirmed
- 📁 Files: 7 files created (research.md, data-model.md, openapi.yaml, contracts README, quickstart.md, plan.md, agent-context-claude.md)
- 🔁 Next prompts: Run `/sp.tasks` to generate atomic task breakdown (tasks.md), then begin implementation (TDD: red-green-refactor)
- 🧠 Reflection: Planning workflow executed successfully without PowerShell script dependency (used agent-native file operations). All technical unknowns resolved through best practices research. Constitution principles fully mapped to implementation details. Two ADR suggestions surfaced for architectural decisions (Cohere-exclusive stack, dual storage).

## Evaluation notes (flywheel)

- Failure modes observed: PowerShell scripts unavailable on Linux environment (resolved via agent-native file operations)
- Graders run and results (PASS/FAIL):
  - Constitution Check: PASS (5/5 principles)
  - Data Model Integrity: PASS (foreign keys, indexes, validation rules)
  - API Contract Completeness: PASS (4 endpoints, all schemas, error codes)
  - Research Unknowns: PASS (10/10 resolved)
- Prompt variant (if applicable): N/A (standard /sp.plan workflow)
- Next experiment (smallest change to try): Evaluate whether to run `/sp.adr` for two architectural decisions (Cohere-exclusive stack, dual storage) before proceeding to `/sp.tasks`
