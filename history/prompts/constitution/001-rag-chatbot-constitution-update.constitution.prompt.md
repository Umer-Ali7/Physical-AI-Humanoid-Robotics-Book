---
id: 001
title: RAG Chatbot Constitution Update
stage: constitution
date: 2025-12-12
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-rag-chatbot
branch: 001-rag-chatbot
user: Administrator
command: /sp.constitution
labels: ["constitution", "rag", "chatbot", "principles", "grounding"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - none
---

## Prompt

/sp.constitution

Project: AI-powered RAG Chatbot for an AI-native textbook with user-selected context querying.

Core principles:
- Grounded reasoning: The chatbot must ONLY answer from the provided book content, selected passages, or indexed embeddings. No hallucinations.
- Cohere-native alignment: Responses must follow Cohere's generation style—concise, factual, and reasoning-focused.
- Context prioritization: When a user selects text, that selection becomes the highest-priority context.
- Transparency: If answer cannot be derived from book content, the agent must explicitly say so.
- Academic clarity: Explanations should be digestible for intermediate tech learners (CS and AI background).

System standards:
- Retrieval pipeline: Qdrant vector search → Cohere embed-english-v3.0 → FastAPI router → Agent SDK.
- Metadata store: Neon Serverless Postgres for chapter IDs, reference locations, and citation tracing.
- Reranking: Cohere Rerank model must filter top chunks before final answer generation.
- Safety: Never fabricate chapters, claims, or lines that do not exist in the book.

Interaction rules:
- Always cite the section/chapter/page from retrieved metadata.
- If user selects text manually, ignore global search and rely ONLY on the selected text.
- Responses must be factual, concise, and grounded in the source material.
- When asked outside book scope, respond with:
  "This topic isn't mentioned in the book sections I have access to."

Constraints:
- Retrieval context size: Max 4 chunks, 700 tokens each.
- Response length: 50–200 words unless user requests long-form.
- No external web browsing allowed. All info must originate from the book's embedded knowledge base.

Success criteria:
- Zero hallucinations (all answers grounded in retrieved text).
- Perfect alignment with selected passage when user highlights text.
- FastAPI service returns <500ms retrieval latency per query.
- Chatbot can be embedded easily inside the published book (web/reader environment).
- Agent passes automated evaluation benchmarks:
  • Factuality ≥ 95%
  • Context-matching accuracy ≥ 98%
  • No answer leakage from outside book corpus

## Response snapshot

Updated the project constitution from generic development principles to RAG chatbot-specific principles:

**Core Principles (5)**:
1. Grounded Reasoning - no hallucinations, all answers traceable to source
2. Cohere-Native Alignment - use Cohere models and generation style
3. Context Prioritization - user-selected text is highest priority
4. Transparency - explicit out-of-scope messages
5. Academic Clarity - intermediate learner-friendly explanations

**System Standards**:
- Retrieval: Qdrant + Cohere embed-english-v3.0 + Cohere Rerank
- Metadata: Neon Postgres for citations
- Safety: zero fabrication, grounded-only responses

**Interaction Rules**:
- Always cite sources
- User text selection overrides global search
- 50-200 word responses (default)

**Technical Constraints**:
- 4 chunks max, 700 tokens each
- <500ms retrieval latency
- Embeddable in web reader

**Success Criteria**:
- 0% hallucinations
- ≥98% context-matching accuracy
- ≥95% factuality
- 0% external leakage

Version: 2.0.0 (major update from generic to RAG-specific)

## Outcome

- ✅ Impact: Established RAG chatbot project principles with grounding, transparency, and academic clarity as core tenets
- 🧪 Tests: No automated tests (documentation change)
- 📁 Files: .specify/memory/constitution.md (updated from v1.0.0 to v2.0.0)
- 🔁 Next prompts: Update dependent templates (plan, spec, tasks) to reference RAG principles; create initial spec for 001-rag-chatbot feature
- 🧠 Reflection: Constitution now provides clear guardrails for RAG development—zero hallucination target, context prioritization, and Cohere-native stack are well-defined

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A (constitution establishment)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate constitution alignment by creating spec.md for 001-rag-chatbot and checking principle references
