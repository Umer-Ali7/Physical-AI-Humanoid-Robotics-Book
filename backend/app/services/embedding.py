"""
Embedding service using Cohere API.

Generates text embeddings for semantic search and retrieval.
"""

import logging
from typing import List

import cohere
# from cohere.errors import CohereAPIError

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Cohere."""

    def __init__(self):
        """Initialize Cohere client."""
        self.client = cohere.Client(api_key=settings.cohere_api_key)
        self.model = "embed-english-v3.0"  # Cohere's latest embedding model
        logger.info(f"Initialized EmbeddingService with model: {self.model}")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            CohereAPIError: If API call fails
        """
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model,
                input_type="search_query",  # Optimized for search queries
            )
            embedding = response.embeddings[0]
            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding
        except Exception as e:
          logger.error(f"Failed to generate embedding: {e}")
          raise RuntimeError("Cohere embedding failed")


    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            CohereAPIError: If API call fails
        """
        try:
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type="search_document",  # Optimized for documents
            )
            logger.debug(f"Generated {len(response.embeddings)} embeddings in batch")
            return response.embeddings
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise RuntimeError("Cohere batch embedding failed")



# Singleton instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """
    Get singleton embedding service instance.

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
