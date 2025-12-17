# Sitemap Ingestion Guide

This guide explains how to use the sitemap-based document ingestion system to load web content into your Qdrant vector database.

## Overview

The ingestion system:
1. Fetches all URLs from a sitemap.xml file
2. Scrapes the main content from each webpage
3. Chunks the text into smaller pieces (500-1000 tokens per chunk)
4. Generates embeddings using Cohere's `embed-english-v3.0` model
5. Stores chunks with embeddings in Qdrant's `book_chunks` collection

## Features

- **Async/Concurrent Processing**: Process multiple pages in parallel for faster ingestion
- **Smart Chunking**: Configurable chunk size with overlap to preserve context
- **Error Handling**: Continue processing even if some pages fail
- **Comprehensive Logging**: Track progress and identify issues
- **Flexible Input**: Works with any sitemap.xml URL

## Usage Methods

### Method 1: Standalone Script (Recommended for initial setup)

```bash
cd backend
python scripts/ingest_sitemap.py --sitemap-url https://physical-ai-humanoid-robotics-book-ebon.vercel.app/sitemap.xml
```

**Options:**
```bash
--sitemap-url URL        # URL to sitemap.xml (required)
--force-reindex          # Delete existing collection and reindex
--batch-size N           # Pages to process concurrently (default: 10)
--chunk-size N           # Max tokens per chunk (default: 800)
--chunk-overlap N        # Overlap between chunks (default: 100)
```

**Example with custom settings:**
```bash
python scripts/ingest_sitemap.py \
  --sitemap-url https://physical-ai-humanoid-robotics-book-ebon.vercel.app/sitemap.xml \
  --batch-size 15 \
  --chunk-size 1000 \
  --chunk-overlap 150 \
  --force-reindex
```

### Method 2: FastAPI Endpoint

Send a POST request to `/api/v1/ingest/sitemap`:

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/sitemap" \
  -H "Content-Type: application/json" \
  -H "X-Admin-API-Key: your-admin-key" \
  -d '{
    "sitemap_url": "https://physical-ai-humanoid-robotics-book-ebon.vercel.app/sitemap.xml",
    "force_reindex": false,
    "batch_size": 10,
    "chunk_size": 800,
    "chunk_overlap": 100
  }'
```

**Python example:**
```python
import requests

url = "http://localhost:8000/api/v1/ingest/sitemap"
headers = {
    "Content-Type": "application/json",
    "X-Admin-API-Key": "your-admin-key"  # Optional in dev mode
}
data = {
    "sitemap_url": "https://physical-ai-humanoid-robotics-book-ebon.vercel.app/sitemap.xml",
    "force_reindex": False,
    "batch_size": 10,
    "chunk_size": 800,
    "chunk_overlap": 100
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Method 3: Python Code

```python
import asyncio
from app.services.sitemap_ingestion import get_sitemap_ingestion_service
from app.db.qdrant_client import get_qdrant_client

async def main():
    # Initialize Qdrant
    await get_qdrant_client()

    # Get ingestion service
    service = get_sitemap_ingestion_service(
        chunk_size=800,
        chunk_overlap=100
    )

    # Run ingestion
    result = await service.ingest_from_sitemap(
        sitemap_url="https://physical-ai-humanoid-robotics-book-ebon.vercel.app/sitemap.xml",
        force_reindex=False,
        batch_size=10
    )

    print(f"Status: {result['status']}")
    print(f"Pages processed: {result['pages_processed']}")
    print(f"Chunks created: {result['chunks_created']}")
    print(f"Duration: {result['duration_seconds']}s")

asyncio.run(main())
```

## Configuration

### Environment Variables

Required environment variables (in `.env` file):

```bash
# Cohere API (for embeddings)
COHERE_API_KEY=your-cohere-api-key

# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_CLUSTER_ID=your-cluster-id

# Optional: Admin API key for ingestion endpoint
ADMIN_API_KEY=your-admin-key
```

### Chunking Parameters

- **chunk_size** (default: 800): Maximum tokens per chunk
  - Smaller chunks: More precise retrieval, but may lose context
  - Larger chunks: More context, but less precise retrieval
  - Recommended: 500-1000 tokens

- **chunk_overlap** (default: 100): Overlap between chunks
  - Prevents important information from being split
  - Recommended: 10-20% of chunk_size

### Batch Processing

- **batch_size** (default: 10): Number of pages to process concurrently
  - Higher values: Faster ingestion, more memory/API usage
  - Lower values: Slower but more stable
  - Recommended: 5-15 for most use cases

## Response Format

### Success Response

```json
{
  "status": "completed",
  "pages_processed": 45,
  "pages_failed": 0,
  "chunks_created": 450,
  "duration_seconds": 123.45,
  "errors": []
}
```

### Partial Success Response

```json
{
  "status": "partial",
  "pages_processed": 40,
  "pages_failed": 5,
  "chunks_created": 400,
  "duration_seconds": 120.0,
  "errors": [
    {"url": "https://example.com/page1", "error": "Connection timeout"},
    {"url": "https://example.com/page2", "error": "No content found"}
  ]
}
```

### Error Response

```json
{
  "error_code": "INVALID_REQUEST",
  "message": "Invalid sitemap format: not well-formed XML",
  "details": {}
}
```

## Monitoring Progress

The system provides detailed logging at each step:

```
INFO - Fetching sitemap from: https://example.com/sitemap.xml
INFO - Found 45 URLs in sitemap
INFO - Processing batch 1/5 (10 pages)
INFO - Processed /docs/intro: 12 chunks (1/45 pages)
INFO - Processed /docs/setup: 8 chunks (2/45 pages)
...
INFO - Sitemap ingestion completed: 45 pages, 0 failed, 450 chunks in 120.00s
```

## Troubleshooting

### Issue: Import errors

**Solution:** Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "No content found" errors

**Cause:** Page content selectors don't match website structure

**Solution:** The scraper tries multiple common selectors (`main`, `article`, `.content`, etc.). If it still fails, pages may have non-standard structure or require JavaScript rendering.

### Issue: High memory usage

**Cause:** Large batch size or many concurrent requests

**Solution:** Reduce `batch_size` to 5-8

### Issue: Rate limiting from target website

**Cause:** Too many concurrent requests

**Solution:**
- Reduce `batch_size` to 2-5
- Add delays between batches (requires code modification)

### Issue: Slow ingestion

**Cause:** Low batch size or slow network

**Solution:**
- Increase `batch_size` to 15-20 (if target server allows)
- Check network connection
- Consider running on server with better bandwidth

## Data Model

Each chunk is stored in Qdrant with:

```python
{
  "id": "uuid-v4",
  "vector": [1024-dimensional embedding],
  "payload": {
    "text": "The actual chunk text content...",
    "url": "https://example.com/page",
    "title": "Page Title",
    "chunk_index": 0,
    "total_chunks": 5,
    "source": "sitemap"
  }
}
```

## Best Practices

1. **Test first**: Run with a small sitemap or `batch_size=1` to test
2. **Monitor logs**: Watch for errors and adjust settings
3. **Use force_reindex sparingly**: Only when you need to completely reset
4. **Chunk size tuning**: Start with defaults, adjust based on retrieval quality
5. **Error handling**: Check `errors` array in response for failed pages

## Next Steps

After ingestion completes:
1. Verify data in Qdrant dashboard
2. Test retrieval with sample queries
3. Monitor search quality and adjust chunk size if needed
4. Set up periodic re-ingestion for updated content
