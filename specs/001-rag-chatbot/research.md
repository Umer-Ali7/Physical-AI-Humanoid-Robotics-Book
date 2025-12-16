# Research Findings: RAG-Powered Documentation Chatbot

**Date**: 2025-12-10
**Feature**: 001-rag-chatbot
**Purpose**: Resolve technical unknowns and establish best practices for implementation

## 1. RAG Chunking Strategies

**Decision**: Semantic chunking by markdown sections with 800-1000 token chunks and 200 token overlap.

**Rationale**:
- Markdown documentation has natural semantic boundaries (headers, sections)
- 800-1000 tokens balances context (enough for meaningful content) vs precision (specific enough for retrieval)
- 200 token overlap prevents context loss at chunk boundaries
- Preserves code blocks and tables as complete units

**Parameters**:
- **Chunk Size**: 800-1000 tokens (~3200-4000 characters)
- **Overlap**: 200 tokens (~800 characters)
- **Strategy**: Split on markdown headers (##, ###), preserve code blocks and tables intact
- **Metadata**: Include section title, file path, page URL with each chunk

**Alternatives Considered**:
- **Fixed-size chunking (512 tokens)**: Too small, breaks context for technical explanations
- **Larger chunks (2000+ tokens)**: Reduces retrieval precision, may exceed context limits
- **No overlap**: Risks losing context at boundaries, especially for cross-referenced content

**Implementation Notes**:
- Use `langchain.text_splitter.MarkdownTextSplitter` or custom splitter
- Prepend section header to each chunk for context: `# Section Title\n\n[chunk content]`
- Handle code blocks specially: don't split mid-block, preserve language tags
- For tables: keep entire table in one chunk if possible

## 2. Gemini Embedding Best Practices

**Decision**: Use `text-embedding-004` model with 768 dimensions.

**Rationale**:
- `text-embedding-004` is the latest and most capable Gemini embedding model
- 768 dimensions provide good balance of quality and storage/compute efficiency
- Optimized for semantic similarity tasks and retrieval
- Supports up to 2048 input tokens per embedding (sufficient for 1000 token chunks)

**Model Specs**:
- **Model**: `models/text-embedding-004`
- **Dimensions**: 768
- **Max Input Tokens**: 2048
- **Cost**: $0.00001 per 1K characters (very affordable for MVP)
- **Normalization**: Embeddings are already L2-normalized

**Alternatives Considered**:
- **embedding-001**: Older model, lower quality, deprecated
- **text-embedding-004 with higher dimensions**: Unnecessary for documentation retrieval

**Implementation Notes**:
- Use `google.generativeai.embed_content()` with `model="models/text-embedding-004"`
- Batch embeddings in groups of 100 chunks for efficiency
- No additional normalization needed (already normalized)
- Handle rate limits: 1500 requests/minute for embedding API
- Cache embeddings to avoid regenerating for unchanged content

## 3. Qdrant Collection Schema

**Decision**: Single collection with cosine distance metric, 768-dimensional vectors, and rich payload schema.

**Rationale**:
- Cosine similarity is standard for text embeddings (measures semantic similarity)
- 768 dimensions match Gemini text-embedding-004 output
- Payload indexing on `file_path` and `section_title` enables filtering
- Simple single-collection design sufficient for <2000 chunks

**Collection Config**:
```python
{
    "vectors": {
        "size": 768,
        "distance": "Cosine"
    }
}
```

**Payload Schema**:
```python
{
    "chunk_text": str,          # Full markdown chunk content
    "file_path": str,           # Relative path (e.g., "docs/intro.md")
    "section_title": str,       # Section heading (e.g., "## Getting Started")
    "page_url": str,            # Docusaurus page URL (e.g., "/docs/intro")
    "chunk_index": int,         # Position in document (0, 1, 2...)
    "doc_title": str            # Document title from frontmatter
}
```

**Search Parameters**:
- **Top-K**: 3-5 chunks (balance between context richness and token limits)
- **Score Threshold**: 0.7 (cosine similarity, filters out irrelevant results)
- **Payload Return**: Include all fields for citation generation

**Alternatives Considered**:
- **Euclidean distance**: Less suitable for normalized embeddings
- **Separate collections per doc category**: Overengineering for MVP scope

**Implementation Notes**:
- Create collection on first run if doesn't exist
- Use `qdrant_client.upsert()` with unique IDs (hash of file_path + chunk_index)
- Enable payload indexing for faster filtering if needed in future
- Monitor collection size; Qdrant Cloud free tier supports reasonable MVP scale

## 4. RAG Prompt Engineering

**Decision**: Structured prompt with strict grounding instructions and explicit "I don't know" handling.

**Rationale**:
- Clear system instructions reduce hallucination
- Formatting retrieved chunks as numbered sources enables citation
- Explicit instructions to admit ignorance when context insufficient
- Few-shot examples improve response quality

**Prompt Template**:
```python
system_instruction = """You are a helpful AI assistant for the Physical AI & Humanoid Robotics documentation.

Your role is to answer questions based ONLY on the provided documentation context. Follow these rules strictly:
1. Only use information from the context provided below
2. If the context doesn't contain relevant information, say "I don't have information about that in the documentation"
3. Cite sources by referencing [Source 1], [Source 2], etc.
4. Be concise but comprehensive
5. Never make up information or use external knowledge"""

user_prompt = f"""Context from documentation:

[Source 1] {chunk_1_text}
(From: {chunk_1_section} - {chunk_1_url})

[Source 2] {chunk_2_text}
(From: {chunk_2_section} - {chunk_2_url})

[Source 3] {chunk_3_text}
(From: {chunk_3_section} - {chunk_3_url})

User Question: {user_query}

Answer (cite sources):"""
```

**Alternatives Considered**:
- **Single-shot prompting**: Less reliable for grounding behavior
- **Chain-of-thought prompting**: Adds latency, unnecessary for straightforward Q&A

**Implementation Notes**:
- Use Gemini 1.5 Flash for generation (fast, cost-effective)
- Set `temperature=0.3` for more focused, less creative responses
- Monitor token usage: context + query + response should stay under 8K tokens
- Add citation extraction post-processing to format source links

## 5. Frontend State Management

**Decision**: React component local state (`useState`) with sessionStorage for persistence.

**Rationale**:
- Chat widget is self-contained, doesn't need global state
- `useState` is simplest and sufficient for message history and UI state
- `sessionStorage` provides tab-scoped persistence (matches spec requirement)
- Avoids dependency on external state libraries

**State Structure**:
```typescript
// Message interface
interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: number;
  citations?: Citation[];
}

interface Citation {
  section: string;
  url: string;
  sourceNumber: number;
}

// Component state
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [isOpen, setIsOpen] = useState(false);
const [isLoading, setIsLoading] = useState(false);
const [inputValue, setInputValue] = useState('');
```

**Persistence Strategy**:
- On message update: `sessionStorage.setItem('chatHistory', JSON.stringify(messages))`
- On component mount: `const saved = sessionStorage.getItem('chatHistory')`
- Clear on page navigation (per spec: session-scoped)

**Alternatives Considered**:
- **Context API**: Overkill for single component, adds complexity
- **Zustand/Redux**: External dependency, unnecessary for simple widget
- **localStorage**: Would persist across sessions (violates spec)

**Implementation Notes**:
- Use `useEffect` to sync messages to sessionStorage
- Implement debouncing if performance issues arise with long histories
- Add error boundaries for graceful error handling
- Consider React.memo for message components if re-render performance issues

## 6. CORS and Deployment

**Decision**: Development with separate ports + CORS, production with reverse proxy (nginx) on same domain.

**Rationale**:
- Development: FastAPI on localhost:8000, Docusaurus on localhost:3000 with CORS
- Production: Nginx reverse proxy serves both on same domain (eliminates CORS issues)
- Same-domain deployment simplifies security and avoids CORS complexity
- API keys in environment variables (never in code)

**CORS Configuration (Development)**:
```python
# backend/src/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Docusaurus dev server
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)
```

**Deployment Pattern (Production)**:
```nginx
# Nginx reverse proxy config
server {
    listen 80;
    server_name docs.example.com;

    # Frontend (Docusaurus static build)
    location / {
        root /var/www/docusaurus/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Alternatives Considered**:
- **Subdomain (api.docs.example.com)**: Requires CORS, more DNS/SSL complexity
- **Separate domains**: Requires CORS, complicates deployment
- **Serverless (AWS Lambda/Vercel)**: Adds complexity for MVP, defer to future

**Implementation Notes**:
- Use `.env` file for development (not committed)
- Production: Environment variables set in hosting platform
- Protect `/ingest` endpoint: IP whitelist or admin API key header
- Add rate limiting middleware for `/chat` endpoint (e.g., 10 requests/minute per IP)
- Consider adding API versioning (`/api/v1/chat`) for future compatibility

## Summary

All research tasks resolved with clear decisions and implementation guidance. Key takeaways:

1. **Chunking**: 800-1000 tokens, semantic splitting, 200 token overlap
2. **Embeddings**: Gemini text-embedding-004 (768-dim)
3. **Vector DB**: Qdrant with cosine similarity, top-k=3-5
4. **Prompting**: Strict grounding instructions with citation formatting
5. **Frontend State**: React useState + sessionStorage
6. **Deployment**: Nginx reverse proxy for production simplicity

No blockers identified. Ready to proceed to Phase 1 (data model and contracts).
