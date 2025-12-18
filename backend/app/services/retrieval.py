"""
Retrieval service for semantic search using Qdrant.

Performs vector similarity search on embedded document chunks.
"""

import logging
from typing import List, Dict, Any

from qdrant_client.models import ScoredPoint

from app.db.qdrant_client import get_qdrant_client, COLLECTION_NAME
from app.services.embedding import get_embedding_service

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for semantic search and retrieval."""

    def __init__(self):
        """Initialize retrieval service."""
        self.embedding_service = get_embedding_service()
        logger.info("Initialized RetrievalService")

    async def search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.3,  # Lowered from 0.7 to allow more results
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search for relevant chunks.

        Args:
            query: User's search query
            top_k: Number of top results to return (default: 3)
            score_threshold: Minimum similarity score (default: 0.7)

        Returns:
            List of dictionaries containing:
                - text: chunk content
                - chapter_id: chapter identifier
                - section_name: section title
                - chunk_id: unique chunk ID
                - score: similarity score (0-1)

        Raises:
            Exception: If search fails
        """
        try:
            # Generate query embedding
            query_vector = await self.embedding_service.generate_embedding(query)

            # Get Qdrant client
            client = await get_qdrant_client()

            # Search for similar chunks using Qdrant query_points
            from qdrant_client.models import PointIdsList, Filter, FieldCondition, SearchParams

            search_results = await client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
            )

            # Format results - query_points returns QueryResponse with points attribute
            chunks = []
            # Handle both query_points (returns QueryResponse) and search (returns list)
            points = search_results.points if hasattr(search_results, 'points') else search_results

            for result in points:
                # Each result is a ScoredPoint
                chunks.append({
                    "text": result.payload.get("text", ""),
                    "chapter_id": result.payload.get("chapter_id", ""),
                    "section_name": result.payload.get("section_name", ""),
                    "chunk_id": str(result.id),
                    "score": result.score,
                })

            logger.info(
                f"Retrieved {len(chunks)} chunks for query (top_k={top_k}, "
                f"threshold={score_threshold})"
            )

            return chunks

        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            raise


# Singleton instance
_retrieval_service: RetrievalService | None = None


def get_retrieval_service() -> RetrievalService:
    """
    Get singleton retrieval service instance.

    Returns:
        RetrievalService instance
    """
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
