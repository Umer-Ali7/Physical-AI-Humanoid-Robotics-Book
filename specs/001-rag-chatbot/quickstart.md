# Quickstart Guide: RAG Documentation Chatbot

**Feature**: 001-rag-chatbot
**Date**: 2025-12-10
**Audience**: Developers setting up the RAG chatbot locally

## Overview

This guide walks you through setting up the RAG-powered documentation chatbot development environment. You'll configure both the FastAPI backend and Docusaurus frontend, run the initial documentation ingestion, and test the chat functionality.

**Time to Complete**: ~30 minutes

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed
- **Git** (already configured in this repo)
- **Qdrant Cloud account** (free tier sufficient for MVP)
- **Google Gemini API key** (free tier available)

## Architecture Quick Reference

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Docusaurus     │  HTTP   │  FastAPI         │  GRPC   │  Qdrant Cloud   │
│  Frontend       │────────>│  Backend         │────────>│  Vector DB      │
│  (port 3000)    │         │  (port 8000)     │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      │ HTTP
                                      ▼
                            ┌──────────────────┐
                            │  Google Gemini   │
                            │  API             │
                            └──────────────────┘
```

## Part 1: Backend Setup (FastAPI)

### Step 1: Create Backend Directory Structure

```bash
# From repo root
mkdir -p backend/src/{models,services,api}
mkdir -p backend/tests/{unit,integration}
cd backend
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Step 3: Install Dependencies

Create `backend/requirements.txt`:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
qdrant-client==1.7.3
google-generativeai==0.3.2
python-dotenv==1.0.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Development dependencies
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

Install:

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create `backend/.env` (DO NOT COMMIT THIS FILE):

```bash
# Qdrant Cloud Configuration
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Application Configuration
DOCS_PATH=../f-docusaurus/docs
CORS_ORIGINS=http://localhost:3000
ADMIN_API_KEY=change_this_in_production

# Optional: Adjust these if needed
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=3
```

**Getting API Keys**:

- **Qdrant**: Sign up at https://cloud.qdrant.io/, create a cluster, copy URL and API key
- **Gemini**: Visit https://makersuite.google.com/app/apikey, create an API key

Create `backend/.env.example` (SAFE TO COMMIT):

```bash
# Copy this to .env and fill in your actual values
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
DOCS_PATH=../f-docusaurus/docs
CORS_ORIGINS=http://localhost:3000
ADMIN_API_KEY=change_me
```

### Step 5: Verify Backend Structure

Your `backend/` directory should look like:

```
backend/
├── src/
│   ├── __init__.py (create empty file)
│   ├── main.py (create later)
│   ├── config.py (create later)
│   ├── models/
│   │   └── __init__.py (create empty file)
│   ├── services/
│   │   └── __init__.py (create empty file)
│   └── api/
│       └── __init__.py (create empty file)
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       └── __init__.py
├── requirements.txt
├── .env (do not commit!)
└── .env.example
```

Create empty `__init__.py` files:

```bash
# From backend/
touch src/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/api/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

### Step 6: Create Minimal FastAPI App (Placeholder)

Create `backend/src/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="RAG Documentation Chatbot API",
    version="1.0.0",
    description="Backend API for Physical AI documentation chatbot"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type", "X-Admin-API-Key"],
)

@app.get("/")
async def root():
    return {"message": "RAG Chatbot API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# TODO: Add /chat and /ingest endpoints (implementation phase)
```

### Step 7: Run Backend

```bash
# From backend/ directory
uvicorn src.main:app --reload --port 8000
```

Visit http://localhost:8000 - you should see:
```json
{"message": "RAG Chatbot API is running", "status": "ok"}
```

Visit http://localhost:8000/docs for auto-generated API documentation (Swagger UI).

**Keep this terminal running.**

---

## Part 2: Frontend Setup (Docusaurus)

### Step 1: Navigate to Docusaurus Directory

```bash
# Open a NEW terminal (keep backend running)
cd f-docusaurus
```

### Step 2: Install Frontend Dependencies

```bash
npm install
```

### Step 3: Create ChatWidget Component Structure

```bash
# From f-docusaurus/
mkdir -p src/components/ChatWidget
mkdir -p src/services
mkdir -p __tests__/components
```

### Step 4: Create Placeholder ChatWidget Component

Create `f-docusaurus/src/components/ChatWidget/index.tsx`:

```typescript
import React, { useState } from 'react';

export default function ChatWidget(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      zIndex: 9999
    }}>
      {isOpen && (
        <div style={{
          width: '400px',
          height: '500px',
          backgroundColor: 'white',
          border: '1px solid #ccc',
          borderRadius: '10px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          display: 'flex',
          flexDirection: 'column',
          marginBottom: '10px'
        }}>
          <div style={{ padding: '10px', borderBottom: '1px solid #ccc' }}>
            <strong>Documentation Chat</strong>
            <button
              onClick={() => setIsOpen(false)}
              style={{ float: 'right', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>
          <div style={{ flex: 1, padding: '10px', overflowY: 'auto' }}>
            <p>Chat coming soon! (Placeholder component)</p>
          </div>
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          fontSize: '24px',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}
      >
        💬
      </button>
    </div>
  );
}
```

### Step 5: Add ChatWidget to Global Layout

**Option A: Using Docusaurus swizzle (recommended)**

```bash
npm run swizzle @docusaurus/theme-classic Layout -- --wrap
```

This creates `src/theme/Layout/index.tsx`. Edit it:

```typescript
import React from 'react';
import Layout from '@theme-original/Layout';
import ChatWidget from '@site/src/components/ChatWidget';

export default function LayoutWrapper(props) {
  return (
    <>
      <Layout {...props} />
      <ChatWidget />
    </>
  );
}
```

**Option B: Manual override (alternative)**

Create `f-docusaurus/src/theme/Layout/index.tsx` manually if swizzle doesn't work.

### Step 6: Run Frontend

```bash
# From f-docusaurus/
npm start
```

Visit http://localhost:3000 - you should see:
- Docusaurus site loads normally
- Floating chat button (💬) in bottom-right corner
- Clicking button opens placeholder chat window

**Keep this terminal running.**

---

## Part 3: Test Integration

### Step 1: Verify Backend-Frontend Communication

In your browser console (F12), try:

```javascript
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log);
```

Expected output: `{status: "healthy"}`

If you see CORS errors, verify:
1. Backend `.env` has `CORS_ORIGINS=http://localhost:3000`
2. Backend is running on port 8000
3. Frontend is running on port 3000

### Step 2: Prepare for Ingestion (Once Implemented)

Once the `/ingest` endpoint is implemented, you'll run:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-Admin-API-Key: change_this_in_production" \
  -d '{"docs_path": "../f-docusaurus/docs", "force_reindex": false}'
```

Expected: Processing ~50-100 markdown files → ~500-2000 chunks in Qdrant

### Step 3: Test Chat Endpoint (Once Implemented)

Once the `/chat` endpoint is implemented:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a ROS 2 node?"}'
```

Expected: JSON response with `reply` field and optional `citations` array.

---

## Part 4: Verify Qdrant Connection

### Test Qdrant Connectivity

Create a quick test script `backend/test_qdrant.py`:

```python
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

try:
    collections = client.get_collections()
    print("✅ Qdrant connected successfully!")
    print(f"Existing collections: {[c.name for c in collections.collections]}")
except Exception as e:
    print(f"❌ Qdrant connection failed: {e}")
```

Run:
```bash
python backend/test_qdrant.py
```

### Test Gemini API

Create `backend/test_gemini.py`:

```python
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    # Test embedding
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="Test embedding"
    )
    print(f"✅ Gemini embedding API works! Dimension: {len(result['embedding'])}")

    # Test generation
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello!")
    print(f"✅ Gemini generation API works! Response: {response.text[:50]}...")

except Exception as e:
    print(f"❌ Gemini API failed: {e}")
```

Run:
```bash
python backend/test_gemini.py
```

---

## Part 5: Development Workflow

### Running Both Services

**Terminal 1 (Backend)**:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn src.main:app --reload --port 8000
```

**Terminal 2 (Frontend)**:
```bash
cd f-docusaurus
npm start
```

### Making Changes

- **Backend changes**: FastAPI auto-reloads on file save
- **Frontend changes**: Docusaurus auto-reloads on file save
- **Environment changes**: Restart the affected service

### Running Tests (Once Implemented)

**Backend tests**:
```bash
cd backend
pytest tests/unit -v
pytest tests/integration -v
```

**Frontend tests**:
```bash
cd f-docusaurus
npm test
```

---

## Next Steps

Now that your development environment is set up:

1. **Implement Backend Services** (tasks from `/sp.tasks`):
   - `services/embedding.py` - Gemini embedding generation
   - `services/vectordb.py` - Qdrant client wrapper
   - `services/ingestion.py` - Markdown chunking and ingestion
   - `services/generation.py` - RAG response generation
   - `api/chat.py` - `/chat` endpoint
   - `api/ingest.py` - `/ingest` endpoint

2. **Implement Frontend Components**:
   - `ChatButton.tsx` - Styled floating button
   - `ChatWindow.tsx` - Chat conversation UI
   - `MessageList.tsx` - Message display with citations
   - `MessageInput.tsx` - Text input with send button
   - `services/chatApi.ts` - API client

3. **Run Ingestion**:
   - Call `/ingest` endpoint to populate Qdrant
   - Verify chunks in Qdrant dashboard

4. **Test End-to-End**:
   - Ask questions via chat widget
   - Verify responses are grounded in docs
   - Check citations link to correct pages

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Check dependencies: `pip list | grep fastapi`
- Check .env file exists and has all required variables

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Clear cache: `npm run clear` then `npm start`
- Check for port conflicts (port 3000 already in use)

### CORS errors
- Verify `CORS_ORIGINS=http://localhost:3000` in backend `.env`
- Restart backend after changing `.env`
- Check browser console for exact error

### Qdrant connection fails
- Verify URL format: `https://your-cluster.qdrant.io` (https, no trailing slash)
- Check API key is correct (copy from Qdrant Cloud dashboard)
- Test with `backend/test_qdrant.py`

### Gemini API fails
- Verify API key from https://makersuite.google.com/app/apikey
- Check quota/billing status in Google AI Studio
- Test with `backend/test_gemini.py`

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Docusaurus Docs**: https://docusaurus.io/docs
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **Gemini API Docs**: https://ai.google.dev/docs
- **API Contract**: See `specs/001-rag-chatbot/contracts/api.yaml`
- **Data Model**: See `specs/001-rag-chatbot/data-model.md`
- **Research**: See `specs/001-rag-chatbot/research.md`

## Questions?

Refer to:
- Feature spec: `specs/001-rag-chatbot/spec.md`
- Implementation plan: `specs/001-rag-chatbot/plan.md`
- Tasks (once generated): `specs/001-rag-chatbot/tasks.md`
