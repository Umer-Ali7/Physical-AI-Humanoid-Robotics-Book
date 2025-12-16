"""
Initialize Qdrant collection for book chunks.

This script creates the book_chunks collection if it doesn't exist.
Run this before starting the application for the first time.
"""

import asyncio
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, ".")

from app.db.qdrant_client import ensure_collection_exists, get_qdrant_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize Qdrant collection."""
    try:
        logger.info("Initializing Qdrant connection...")
        client = await get_qdrant_client()

        logger.info("Ensuring book_chunks collection exists...")
        await ensure_collection_exists()

        logger.info("✅ Qdrant collection initialized successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Qdrant: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
