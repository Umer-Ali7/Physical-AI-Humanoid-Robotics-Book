# AI-Powered RAG Chatbot Constitution

**Project**: Physical AI and Humanoid Robotics textbook with user-selected context querying

## Core Principles

### I. Grounded Reasoning
The chatbot MUST ONLY answer from the provided book content, selected passages, or indexed embeddings. No hallucinations are permitted. Every response must be traceable to source material in the knowledge base.

### II. Cohere-Native Alignment
Responses MUST follow Cohere's generation style—concise, factual, and reasoning-focused. All embeddings and reranking use Cohere models (embed-english-v3.0, Rerank).

### III. Context Prioritization
When a user selects text, that selection becomes the highest-priority context. The agent MUST prioritize selected passages over global search results. User-provided context always wins.

### IV. Transparency
If an answer cannot be derived from book content, the agent MUST explicitly state:
> "This topic isn't mentioned in the book sections I have access to."

Never fabricate information. Make the boundaries of knowledge explicit.

### V. Academic Clarity
Explanations should be digestible for intermediate tech learners (CS and AI background). Use clear, pedagogical language suitable for educational content.

## System Standards

### Retrieval Pipeline
- **Vector Search**: Qdrant vector database
- **Embeddings**: Cohere embed-english-v3.0
- **API Layer**: FastAPI router
- **Agent Framework**: Claude Agent SDK
- **Reranking**: Cohere Rerank model must filter top chunks before final answer generation

### Metadata Store
- **Database**: Neon Serverless Postgres
- **Stored Metadata**: Chapter IDs, reference locations, citation tracing
- **Purpose**: Enable precise source attribution and citation

### Safety Requirements
- Never fabricate chapters, claims, or lines that do not exist in the book
- All answers must be grounded in retrieved text
- No external web browsing allowed
- All information must originate from the book's embedded knowledge base

## Interaction Rules

### Citation Requirements
- Always cite the section/chapter/page from retrieved metadata
- Include source references in every response
- Enable users to verify claims against original text

### Context Handling
- **User-selected text**: Ignore global search and rely ONLY on the selected text
- **No selection**: Use vector search with reranking to find relevant chunks
- **Max context**: 4 chunks, 700 tokens each

### Response Format
- **Default length**: 50–200 words unless user requests long-form
- **Style**: Factual, concise, grounded in source material
- **Out-of-scope queries**: Respond with transparency message (Principle IV)

## Technical Constraints

### Performance Targets
- FastAPI service: <500ms retrieval latency per query
- Vector search: Top-k = 20, rerank to 4
- Embedding dimension: Cohere embed-english-v3.0 native dimensions

### Context Limits
- Retrieval context size: Max 4 chunks
- Chunk size: 700 tokens each
- Total context window: ~2800 tokens maximum

### Integration Requirements
- Chatbot must be embeddable inside published book (web/reader environment)
- Support for text selection events from frontend
- Clean API contract for retrieval and generation

## Success Criteria

The system is considered successful when it achieves:

### Zero Hallucinations
- **Target**: 100% grounding in retrieved text
- **Validation**: All answers must be traceable to source chunks
- **Measurement**: Automated fact-checking against known Q&A pairs

### Context-Matching Accuracy
- **Target**: ≥ 98% accuracy
- **Definition**: When user selects text, response must be based on that exact selection
- **Validation**: Compare response source to selected passage metadata

### Factuality Score
- **Target**: ≥ 95% factuality
- **Measurement**: Human evaluation and automated benchmarks
- **Method**: Comparison against ground-truth book content

### No External Leakage
- **Target**: 0% answers from outside book corpus
- **Validation**: All responses must trace to book embeddings only
- **Test**: Out-of-distribution query dataset should trigger transparency response

### Performance
- **Retrieval latency**: <500ms per query (p95)
- **End-to-end latency**: <2s including generation
- **Embedability**: Successfully integrated into web reader

## Additional Constraints

### Technology Stack
- **Backend**: Python, FastAPI
- **Vector DB**: Qdrant (cloud or self-hosted)
- **SQL DB**: Neon Serverless Postgres
- **Embeddings**: Cohere embed-english-v3.0
- **Reranker**: Cohere Rerank v3
- **Agent**: Claude via Agent SDK
- **Frontend**: Docusaurus-compatible chat widget

### Development Standards
- All API endpoints must include OpenAPI documentation
- All retrieval functions must include logging for debugging
- All responses must include metadata for citation
- Security: No user data stored beyond session; rate limiting required

## Governance

This Constitution is the ultimate source of truth for the RAG chatbot project. All design decisions, implementation tasks, and feature additions MUST align with these principles.

Amendments require:
1. Formal proposal with rationale
2. Impact analysis on retrieval accuracy and user experience
3. Approval by project architect
4. Update to all dependent templates and documentation

All PRs and code reviews must verify compliance with these principles, particularly grounding, transparency, and context prioritization.

**Version**: 2.0.0 | **Ratified**: 2025-12-12 | **Last Amended**: 2025-12-12
