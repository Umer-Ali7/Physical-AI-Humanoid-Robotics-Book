"""
Standalone script for ingesting content from a sitemap.

Usage:
    python scripts/ingest_sitemap.py --sitemap-url https://example.com/sitemap.xml

Optional arguments:
    --force-reindex     Delete existing collection and reindex
    --batch-size N      Number of pages to process concurrently (default: 10)
    --chunk-size N      Maximum tokens per chunk (default: 800)
    --chunk-overlap N   Overlap between chunks (default: 100)
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.sitemap_ingestion import get_sitemap_ingestion_service
from app.db.qdrant_client import get_qdrant_client
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(
        description="Ingest content from a sitemap into Qdrant vector database"
    )
    parser.add_argument(
        "--sitemap-url",
        type=str,
        default="https://physical-ai-humanoid-robotics-book-ebon.vercel.app/sitemap.xml",
        help="URL to sitemap.xml file",
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="Delete existing collection and reindex all pages",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of pages to process concurrently (default: 10)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Maximum tokens per chunk (default: 800)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Overlap between chunks in tokens (default: 100)",
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("SITEMAP INGESTION SCRIPT")
    logger.info("=" * 80)
    logger.info(f"Sitemap URL: {args.sitemap_url}")
    logger.info(f"Force reindex: {args.force_reindex}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Chunk size: {args.chunk_size}")
    logger.info(f"Chunk overlap: {args.chunk_overlap}")
    logger.info("=" * 80)

    try:
        # Initialize Qdrant client
        logger.info("Initializing Qdrant client...")
        await get_qdrant_client()

        # Get ingestion service
        logger.info("Initializing sitemap ingestion service...")
        ingestion_service = get_sitemap_ingestion_service(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )

        # Run ingestion
        logger.info("Starting ingestion...")
        result = await ingestion_service.ingest_from_sitemap(
            sitemap_url=args.sitemap_url,
            force_reindex=args.force_reindex,
            batch_size=args.batch_size,
        )

        # Print results
        logger.info("=" * 80)
        logger.info("INGESTION COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Status: {result['status'].upper()}")
        logger.info(f"Pages processed: {result['pages_processed']}")
        logger.info(f"Pages failed: {result['pages_failed']}")
        logger.info(f"Chunks created: {result['chunks_created']}")
        logger.info(f"Duration: {result['duration_seconds']:.2f} seconds")

        if result.get("errors"):
            logger.warning(f"Errors encountered: {len(result['errors'])}")
            for error in result["errors"][:5]:  # Show first 5 errors
                logger.warning(f"  - {error['url']}: {error['error']}")
            if len(result["errors"]) > 5:
                logger.warning(f"  ... and {len(result['errors']) - 5} more errors")

        logger.info("=" * 80)

        # Exit with appropriate code
        if result["status"] == "failed":
            sys.exit(1)
        elif result["status"] == "partial":
            sys.exit(2)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Ingestion failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
