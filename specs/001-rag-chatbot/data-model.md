# Data Model: RAG-Powered Documentation Chatbot

**Date**: 2025-12-10
**Feature**: 001-rag-chatbot
**Purpose**: Define entities, relationships, and validation rules

## Overview

This document defines the data structures used in the RAG chatbot system. The system is stateless on the backend (no persistent user data), with conversation state managed client-side and document data stored in Qdrant vector database.

## Entities

### 1. User Query

**Description**: Represents a question or natural language input submitted by the user through the chat interface.

**Attributes**:
- `query_text` (string, required): The user's question or input
  - **Validation**: 1-500 characters, non-empty after trimming
- `timestamp` (number, required): Unix timestamp when query was submitted
- `session_id` (string, optional): Client-generated UUID for tracking conversation context (P3 feature)

**Relationships**:
- Generates one Chat Message (user message)
- Triggers retrieval of 0-N Documentation Chunks
- Results in one Chat Message (AI response)

**Validation Rules**:
- Query text must be non-empty after trimming whitespace
- Query text length must be 1-500 characters (prevent abuse)
- Timestamp must be valid Unix timestamp (milliseconds)
- Session ID must be valid UUID v4 format if provided

**State Transitions**: N/A (immutable once submitted)

---

### 2. Chat Message

**Description**: Represents a single message in the conversation history, either from the user or the AI assistant.

**Attributes**:
- `id` (string, required): Unique identifier for the message (UUID v4)
- `text` (string, required): The message content
  - User message: original query text
  - AI message: generated response
- `sender` (enum, required): Message source
  - Values: `"user"` | `"ai"`
- `timestamp` (number, required): Unix timestamp when message was created
- `citations` (array of Citation, optional): Source references for AI messages (P2 feature)
  - Empty/null for user messages
  - 0-5 citations for AI messages

**Relationships**:
- Belongs to one Conversation Session
- AI messages reference 0-N Source Citations
- User messages are derived from User Query

**Validation Rules**:
- ID must be unique within conversation
- Text must be non-empty (1-10000 characters)
- Sender must be either "user" or "ai"
- Citations only present when sender is "ai"
- Timestamp must be valid and chronologically ordered within conversation

**State Transitions**: Immutable once created (append-only message history)

---

### 3. Documentation Chunk

**Description**: Represents a segment of documentation content that has been processed and stored in the Qdrant vector database for semantic search.

**Attributes**:
- `id` (string, required): Unique identifier (hash of `file_path + chunk_index`)
- `chunk_text` (string, required): The actual markdown content of the chunk
  - **Validation**: 100-5000 characters
- `embedding_vector` (array of float, required): 768-dimensional embedding from Gemini
  - **Validation**: Exactly 768 float values, L2-normalized
- `file_path` (string, required): Relative path from docs root (e.g., `"docs/intro.md"`)
- `section_title` (string, required): Markdown heading for the section (e.g., `"## Getting Started"`)
- `page_url` (string, required): Docusaurus page URL (e.g., `"/docs/intro"`)
- `chunk_index` (integer, required): Zero-based position within the document
  - **Validation**: >= 0
- `doc_title` (string, required): Document title from frontmatter or first H1

**Relationships**:
- Retrieved by User Query via semantic search
- Referenced in Source Citation (many-to-one)

**Validation Rules**:
- ID must be unique across all chunks
- Chunk text must be valid markdown
- Embedding vector must be exactly 768 dimensions
- File path must exist and be relative to docs root
- Page URL must be valid Docusaurus route
- Chunk index must be non-negative integer
- Section title must match markdown heading format

**State Transitions**:
- Created during ingestion (`POST /ingest`)
- Updated if document content changes (upsert operation)
- Deleted if document is removed (future feature)

---

### 4. Conversation Session

**Description**: Represents a user's chat session, containing the full history of messages exchanged. Managed client-side only (no backend persistence).

**Attributes**:
- `session_id` (string, required): UUID v4 generated on first interaction
- `messages` (array of Chat Message, required): Ordered list of conversation messages
  - **Validation**: 0-100 messages (prevent unbounded growth)
- `created_at` (number, required): Unix timestamp when session started
- `last_activity_at` (number, required): Unix timestamp of last message

**Relationships**:
- Contains 0-N Chat Messages
- Associated with multiple User Queries (one per user message)

**Validation Rules**:
- Session ID must be valid UUID v4
- Messages array must be chronologically ordered by timestamp
- Maximum 100 messages per session (UI limit)
- `last_activity_at` must be >= `created_at`
- Session resets on page navigation (sessionStorage scope)

**State Transitions**:
- Created: When user first opens chat widget
- Updated: On each new message sent or received
- Destroyed: On page navigation/refresh (per MVP spec)

---

### 5. Source Citation

**Description**: Represents a reference to a specific documentation page or section used to generate an AI answer (P2 feature).

**Attributes**:
- `section_title` (string, required): Section heading (e.g., `"Introduction to ROS 2"`)
- `page_url` (string, required): Full Docusaurus URL (e.g., `"/docs/ros2/intro"`)
- `source_number` (integer, required): Citation number in response (1, 2, 3...)
  - **Validation**: 1-5 (matches top-k retrieval)
- `relevance_score` (float, optional): Cosine similarity score from Qdrant search
  - **Validation**: 0.0-1.0

**Relationships**:
- Belongs to one Chat Message (AI message)
- Derived from one Documentation Chunk

**Validation Rules**:
- Section title must be non-empty (from chunk metadata)
- Page URL must be valid Docusaurus route
- Source number must be 1-5 and unique within message
- Relevance score must be between 0.0 and 1.0 if provided

**State Transitions**: Immutable once created with AI message

---

## Entity Relationship Diagram

```
User Query (1) ──> (1) Chat Message [user]
    │
    ├──> (0..N) Documentation Chunk [retrieved]
    │
    └──> (1) Chat Message [AI] ──> (0..5) Source Citation
                                        │
                                        └──> (1) Documentation Chunk

Conversation Session (1) ──> (0..100) Chat Message
```

## Data Flow

### Chat Query Flow (P1)
1. User submits **User Query** via frontend
2. Backend generates embedding for query text
3. Qdrant search retrieves top-k (3-5) **Documentation Chunks**
4. Chunks + query sent to Gemini for generation
5. Response returned as **Chat Message** (AI)
6. Frontend adds both user and AI **Chat Messages** to **Conversation Session**

### Citation Flow (P2)
1. During retrieval, store chunk metadata (section, URL, score)
2. In prompt, number chunks as [Source 1], [Source 2], etc.
3. Parse AI response for citation references
4. Create **Source Citation** objects from chunk metadata
5. Attach citations to **Chat Message**
6. Frontend renders citations as clickable links

### Ingestion Flow (P2)
1. Backend reads markdown files from docs directory
2. For each file, split into chunks (800-1000 tokens)
3. Generate embeddings using Gemini
4. Create **Documentation Chunk** objects
5. Upsert chunks into Qdrant collection
6. Log progress and errors

## Storage Strategy

### Vector Database (Qdrant)
- **Entity**: Documentation Chunk
- **Collection**: `physical_ai_docs` (single collection)
- **Persistence**: Cloud-managed (Qdrant Cloud)

### Client-Side (sessionStorage)
- **Entity**: Conversation Session, Chat Messages
- **Persistence**: Tab-scoped (resets on navigation)
- **Key**: `chatHistory` → JSON serialized messages array

### Backend (In-Memory Only)
- **No persistent state**: Backend is stateless
- **Temporary**: Query processing variables (query embedding, retrieved chunks, prompt)

## Validation Summary

| Entity | Key Validations |
|--------|----------------|
| User Query | 1-500 chars, non-empty, valid timestamp |
| Chat Message | Non-empty text, valid sender enum, chronological order |
| Documentation Chunk | 100-5000 chars, 768-dim vector, valid file path |
| Conversation Session | Max 100 messages, valid UUID, chronological |
| Source Citation | 1-5 source number, valid URL, 0.0-1.0 score |

## Future Considerations

- **User Authentication** (Out of scope for MVP): Would add User entity with auth tokens
- **Persistent Sessions** (P3 enhancement): Would require backend session storage (Redis/PostgreSQL)
- **Feedback Data** (Future): Thumbs up/down would add Rating entity
- **Analytics** (Future): Query logs, popular topics → Analytics Event entity
