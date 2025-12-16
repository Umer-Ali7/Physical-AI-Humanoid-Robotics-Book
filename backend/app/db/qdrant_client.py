"""
Qdrant vector database client management.

Manages connection to Qdrant Cloud and collection initialization.
"""

import logging
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.config import settings

logger = logging.getLogger(__name__)

# Global Qdrant client singleton
_client: Optional[AsyncQdrantClient] = None

COLLECTION_NAME = "book_chunks"
VECTOR_SIZE = 1024  # Cohere embed-english-v3.0 dimensions
DISTANCE_METRIC = Distance.COSINE


async def get_qdrant_client() -> AsyncQdrantClient:
    """
    Get or create the Qdrant client.

    Returns:
        AsyncQdrantClient: Configured Qdrant client

    Raises:
        RuntimeError: If client initialization fails
    """
    global _client

    if _client is None:
        try:
            _client = AsyncQdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30,
            )
            logger.info(f"Qdrant client initialized: {settings.qdrant_url}")

            # Ensure collection exists
            await ensure_collection_exists()

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise RuntimeError(f"Qdrant client initialization failed: {e}")

    return _client


async def ensure_collection_exists() -> None:
    """
    Ensure the book_chunks collection exists in Qdrant.

    Creates the collection if it doesn't exist.
    """
    try:
        client = await get_qdrant_client()

        # Check if collection exists
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if COLLECTION_NAME not in collection_names:
            # Create collection
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=DISTANCE_METRIC),
            )
            logger.info(
                f"Created Qdrant collection '{COLLECTION_NAME}' "
                f"(vector_size={VECTOR_SIZE}, distance={DISTANCE_METRIC.value})"
            )
        else:
            logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists")

    except Exception as e:
        logger.error(f"Failed to ensure collection exists: {e}")
        raise


async def close_qdrant_client() -> None:
    """Close the Qdrant client."""
    global _client

    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Qdrant client closed")


async def check_qdrant_health() -> bool:
    """
    Check if Qdrant connection is healthy.

    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        client = await get_qdrant_client()
        await client.get_collections()
        return True
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return False
