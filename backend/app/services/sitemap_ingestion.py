"""
Sitemap-based document ingestion service for loading web content into Qdrant.

Fetches content from a sitemap URL, scrapes pages, chunks text, and stores in vector database.
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import uuid
import asyncio
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from qdrant_client.models import PointStruct

from app.services.embedding import get_embedding_service
from app.db.qdrant_client import get_qdrant_client, COLLECTION_NAME

logger = logging.getLogger(__name__)


class SitemapIngestionService:
    """Service for ingesting documents from sitemap into the vector database."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """
        Initialize sitemap ingestion service.

        Args:
            chunk_size: Maximum tokens per chunk (default: 800)
            chunk_overlap: Overlap between chunks (default: 100)
        """
        self.embedding_service = get_embedding_service()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        logger.info(
            f"Initialized SitemapIngestionService "
            f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
        )

    async def fetch_sitemap_urls(self, sitemap_url: str) -> List[str]:
        """
        Fetch all URLs from a sitemap XML.

        Args:
            sitemap_url: URL to the sitemap.xml file

        Returns:
            List of URLs found in the sitemap

        Raises:
            httpx.HTTPError: If sitemap fetch fails
            ValueError: If sitemap parsing fails
        """
        try:
            logger.info(f"Fetching sitemap from: {sitemap_url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(sitemap_url)
                response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            # Handle namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Extract URLs
            urls = []
            for url_elem in root.findall('.//ns:url/ns:loc', namespace):
                if url_elem.text:
                    urls.append(url_elem.text.strip())

            # Fallback: try without namespace
            if not urls:
                for url_elem in root.findall('.//loc'):
                    if url_elem.text:
                        urls.append(url_elem.text.strip())

            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls

        except ET.ParseError as e:
            logger.error(f"Failed to parse sitemap XML: {e}")
            raise ValueError(f"Invalid sitemap format: {e}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch sitemap: {e}")
            raise

    async def scrape_page_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape main content and metadata from a webpage.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with 'url', 'title', 'content' keys, or None if failed
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Extract title
            title = "Untitled"
            if soup.title and soup.title.string:
                title = soup.title.string.strip()

            # Remove script, style, nav, footer elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            # Try to find main content
            # Look for common content containers
            main_content = None
            content_selectors = [
                'main',
                'article',
                '[role="main"]',
                '.content',
                '.main-content',
                '#content',
                '#main-content',
            ]

            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # Fallback to body if no main content found
            if not main_content:
                main_content = soup.body

            if not main_content:
                logger.warning(f"No content found for {url}")
                return None

            # Extract text
            text = main_content.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            content = '\n'.join(lines)

            if not content:
                logger.warning(f"Empty content for {url}")
                return None

            logger.debug(f"Scraped {url}: {len(content)} chars, title='{title}'")

            return {
                'url': url,
                'title': title,
                'content': content,
            }

        except httpx.HTTPError as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def chunk_text(self, text: str, url: str, title: str) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces suitable for embeddings.

        Uses simple token-based chunking with overlap.

        Args:
            text: Text content to chunk
            url: Source URL
            title: Page title

        Returns:
            List of chunk dictionaries with 'text', 'url', 'title', 'chunk_index'
        """
        # Simple word-based chunking (approximate token count)
        # Assume ~1.3 words per token on average
        words_per_chunk = int(self.chunk_size * 1.3)
        words_overlap = int(self.chunk_overlap * 1.3)

        words = text.split()
        chunks = []

        if not words:
            return chunks

        # If text is shorter than chunk size, return as single chunk
        if len(words) <= words_per_chunk:
            chunks.append({
                'text': text,
                'url': url,
                'title': title,
                'chunk_index': 0,
                'total_chunks': 1,
            })
            return chunks

        # Create overlapping chunks
        chunk_index = 0
        start = 0

        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)

            chunks.append({
                'text': chunk_text,
                'url': url,
                'title': title,
                'chunk_index': chunk_index,
            })

            chunk_index += 1

            # Move start forward by (chunk_size - overlap)
            start += words_per_chunk - words_overlap

            # Prevent infinite loop
            if start <= end - words_per_chunk and end >= len(words):
                break

        # Add total chunks to all chunks
        for chunk in chunks:
            chunk['total_chunks'] = len(chunks)

        logger.debug(f"Created {len(chunks)} chunks from {len(words)} words")
        return chunks

    async def ingest_from_sitemap(
        self,
        sitemap_url: str,
        force_reindex: bool = False,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Ingest all pages from a sitemap into the vector database.

        Args:
            sitemap_url: URL to sitemap.xml
            force_reindex: If True, delete existing collection and reindex all
            batch_size: Number of pages to process concurrently

        Returns:
            Dictionary with ingestion statistics:
                - status: "completed" | "partial" | "failed"
                - pages_processed: number of pages successfully processed
                - pages_failed: number of pages that failed
                - chunks_created: total number of chunks created
                - duration_seconds: time taken
                - errors: list of error messages (max 10)
        """
        start_time = time.time()
        errors = []
        pages_processed = 0
        pages_failed = 0
        total_chunks = 0

        try:
            logger.info(f"Starting sitemap ingestion from: {sitemap_url}")

            # Get Qdrant client
            client = await get_qdrant_client()

            # Handle force reindex
            if force_reindex:
                logger.warning("Force reindex requested - recreating collection")
                try:
                    await client.delete_collection(COLLECTION_NAME)
                    logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
                except Exception as e:
                    logger.warning(f"Failed to delete collection (may not exist): {e}")

                # Recreate collection
                from app.db.qdrant_client import ensure_collection_exists
                await ensure_collection_exists()

            # Fetch URLs from sitemap
            urls = await self.fetch_sitemap_urls(sitemap_url)

            if not urls:
                logger.warning("No URLs found in sitemap")
                return {
                    "status": "completed",
                    "pages_processed": 0,
                    "pages_failed": 0,
                    "chunks_created": 0,
                    "duration_seconds": time.time() - start_time,
                    "errors": ["No URLs found in sitemap"],
                }

            # Process pages in batches
            for i in range(0, len(urls), batch_size):
                batch_urls = urls[i:i + batch_size]
                logger.info(
                    f"Processing batch {i // batch_size + 1}/{(len(urls) + batch_size - 1) // batch_size} "
                    f"({len(batch_urls)} pages)"
                )

                # Scrape pages concurrently
                scrape_tasks = [self.scrape_page_content(url) for url in batch_urls]
                page_data_list = await asyncio.gather(*scrape_tasks, return_exceptions=True)

                # Process each page
                for url, page_data in zip(batch_urls, page_data_list):
                    try:
                        # Handle exceptions from gather
                        if isinstance(page_data, Exception):
                            raise page_data

                        if not page_data:
                            pages_failed += 1
                            error_msg = f"Failed to scrape {url}: No content"
                            logger.warning(error_msg)
                            if len(errors) < 10:
                                errors.append({"url": url, "error": "No content"})
                            continue

                        # Chunk the content
                        chunks = self.chunk_text(
                            text=page_data['content'],
                            url=page_data['url'],
                            title=page_data['title'],
                        )

                        if not chunks:
                            logger.warning(f"No chunks created from {url}")
                            pages_failed += 1
                            continue

                        # Generate embeddings in batch
                        chunk_texts = [chunk['text'] for chunk in chunks]
                        embeddings = await self.embedding_service.generate_embeddings_batch(
                            chunk_texts
                        )

                        # Create Qdrant points
                        points = []
                        for chunk, embedding in zip(chunks, embeddings):
                            point_id = str(uuid.uuid4())
                            points.append(
                                PointStruct(
                                    id=point_id,
                                    vector=embedding,
                                    payload={
                                        "text": chunk["text"],
                                        "url": chunk["url"],
                                        "title": chunk["title"],
                                        "chunk_index": chunk["chunk_index"],
                                        "total_chunks": chunk["total_chunks"],
                                        "source": "sitemap",
                                    },
                                )
                            )

                        # Upsert to Qdrant
                        await client.upsert(
                            collection_name=COLLECTION_NAME,
                            points=points,
                        )

                        pages_processed += 1
                        total_chunks += len(chunks)
                        logger.info(
                            f"Processed {urlparse(url).path}: {len(chunks)} chunks "
                            f"({pages_processed}/{len(urls)} pages)"
                        )

                    except Exception as e:
                        pages_failed += 1
                        error_msg = f"Failed to process {url}: {str(e)}"
                        logger.error(error_msg)
                        if len(errors) < 10:
                            errors.append({"url": url, "error": str(e)})

            # Calculate duration
            duration = time.time() - start_time

            # Determine status
            if pages_processed == 0:
                status = "failed"
            elif pages_failed > 0:
                status = "partial"
            else:
                status = "completed"

            result = {
                "status": status,
                "pages_processed": pages_processed,
                "pages_failed": pages_failed,
                "chunks_created": total_chunks,
                "duration_seconds": round(duration, 2),
                "errors": errors,
            }

            logger.info(
                f"Sitemap ingestion {status}: {pages_processed} pages, "
                f"{pages_failed} failed, {total_chunks} chunks in {duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Sitemap ingestion failed: {e}", exc_info=True)
            raise


# Singleton instance
_sitemap_ingestion_service: Optional[SitemapIngestionService] = None


def get_sitemap_ingestion_service(
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> SitemapIngestionService:
    """
    Get singleton sitemap ingestion service instance.

    Args:
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Overlap between chunks

    Returns:
        SitemapIngestionService instance
    """
    global _sitemap_ingestion_service
    if _sitemap_ingestion_service is None:
        _sitemap_ingestion_service = SitemapIngestionService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    return _sitemap_ingestion_service
