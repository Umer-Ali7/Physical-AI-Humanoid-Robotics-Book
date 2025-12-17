"""
Document ingestion service for loading content into Qdrant.

Orchestrates the full ingestion pipeline: scan → parse → chunk → embed → store.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

from qdrant_client.models import PointStruct

from app.services.chunking import get_markdown_chunker
from app.services.embedding import get_embedding_service
from app.db.qdrant_client import get_qdrant_client, COLLECTION_NAME

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting documents into the vector database."""

    def __init__(self):
        """Initialize ingestion service."""
        self.chunker = get_markdown_chunker()
        self.embedding_service = get_embedding_service()
        logger.info("Initialized IngestionService")

    async def ingest_documents(
        self,
        docs_path: str,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest all markdown documents from a directory.

        Args:
            docs_path: Path to documentation directory
            force_reindex: If True, delete existing collection and reindex all

        Returns:
            Dictionary with ingestion statistics:
                - status: "completed" | "partial" | "failed"
                - files_processed: number of files successfully processed
                - chunks_created: total number of chunks created
                - duration_seconds: time taken
                - errors: list of error messages
        """
        start_time = time.time()
        errors = []
        files_processed = 0
        total_chunks = 0

        try:
            logger.info(f"Starting ingestion from: {docs_path}")

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

            # Scan for markdown files
            docs_dir = Path(docs_path)
            if not docs_dir.exists():
                raise ValueError(f"Documentation path not found: {docs_path}")

            markdown_files = list(docs_dir.rglob("*.md"))
            logger.info(f"Found {len(markdown_files)} markdown files")

            if not markdown_files:
                logger.warning(f"No markdown files found in {docs_path}")
                return {
                    "status": "completed",
                    "files_processed": 0,
                    "chunks_created": 0,
                    "duration_seconds": time.time() - start_time,
                    "errors": ["No markdown files found"],
                }

            # Process each file
            for file_path in markdown_files:
                try:
                    # Extract chapter ID from filename or path
                    chapter_id = self._extract_chapter_id(file_path)

                    # Read file content
                    content = file_path.read_text(encoding='utf-8')

                    # Chunk the document
                    chunks = self.chunker.chunk_markdown(
                        content=content,
                        file_path=str(file_path.relative_to(docs_dir)),
                        chapter_id=chapter_id,
                    )

                    if not chunks:
                        logger.warning(f"No chunks created from {file_path}")
                        continue

                    # Generate embeddings in batches
                    chunk_texts = [chunk["text"] for chunk in chunks]
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
                                    "chapter_id": chunk["chapter_id"],
                                    "section_name": chunk["section_name"],
                                    "chunk_index": chunk["chunk_index"],
                                    "file_path": chunk["file_path"],
                                },
                            )
                        )

                    # Upsert to Qdrant
                    await client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=points,
                    )

                    files_processed += 1
                    total_chunks += len(chunks)
                    logger.info(
                        f"Processed {file_path.name}: {len(chunks)} chunks "
                        f"({files_processed}/{len(markdown_files)} files)"
                    )

                except Exception as e:
                    error_msg = f"Failed to process {file_path}: {str(e)}"
                    logger.error(error_msg)
                    errors.append({
                        "file": str(file_path),
                        "error": str(e),
                    })

            # Calculate duration
            duration = time.time() - start_time

            # Determine status
            if files_processed == 0:
                status = "failed"
            elif errors:
                status = "partial"
            else:
                status = "completed"

            result = {
                "status": status,
                "files_processed": files_processed,
                "chunks_created": total_chunks,
                "duration_seconds": round(duration, 2),
                "errors": errors,
            }

            logger.info(
                f"Ingestion {status}: {files_processed} files, "
                f"{total_chunks} chunks in {duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            raise

    def _extract_chapter_id(self, file_path: Path) -> str:
        """
        Extract chapter ID from file path.

        Args:
            file_path: Path to markdown file

        Returns:
            Chapter ID (e.g., "ch01", "ch02", or "general")
        """
        # Try to extract chapter number from filename or parent directory
        file_name = file_path.stem.lower()

        # Check for chapter pattern in filename (e.g., "01-intro.md" or "chapter-01.md")
        import re
        chapter_match = re.search(r'(?:chapter[-_]?|ch)?(\d+)', file_name)
        if chapter_match:
            chapter_num = chapter_match.group(1).zfill(2)
            return f"ch{chapter_num}"

        # Check parent directory
        parent_name = file_path.parent.name.lower()
        chapter_match = re.search(r'(?:chapter[-_]?|ch)?(\d+)', parent_name)
        if chapter_match:
            chapter_num = chapter_match.group(1).zfill(2)
            return f"ch{chapter_num}"

        # Default to using file stem
        return file_name[:20]  # Limit length


# Singleton instance
_ingestion_service: IngestionService | None = None


def get_ingestion_service() -> IngestionService:
    """
    Get singleton ingestion service instance.

    Returns:
        IngestionService instance
    """
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service
