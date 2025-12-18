"""
Ingestion endpoint for loading documentation into vector database.

Admin-only endpoint for processing and indexing markdown documents or web content.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl

from app.config import settings
from app.models.responses import EmbedResponse, ErrorResponse
from app.services.ingestion import get_ingestion_service
from app.services.sitemap_ingestion import get_sitemap_ingestion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


class IngestRequest(BaseModel):
    """Request model for document ingestion."""

    docs_path: str = Field(
        default="../f-docusaurus/docs",
        description="Path to documentation directory",
    )
    force_reindex: bool = Field(
        default=False,
        description="Delete existing collection and reindex all files",
    )


class SitemapIngestRequest(BaseModel):
    """Request model for sitemap-based ingestion."""

    sitemap_url: str = Field(
        ...,
        description="URL to sitemap.xml file",
        examples=["https://example.com/sitemap.xml"],
    )
    force_reindex: bool = Field(
        default=False,
        description="Delete existing collection and reindex all pages",
    )
    batch_size: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of pages to process concurrently",
    )
    chunk_size: int = Field(
        default=800,
        ge=100,
        le=2000,
        description="Maximum tokens per chunk",
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens",
    )


class IngestResponse(BaseModel):
    """Response model for document ingestion."""

    status: str = Field(..., description="completed | partial | failed")
    files_processed: int = Field(..., ge=0)
    chunks_created: int = Field(..., ge=0, alias="total_chunks_created")
    duration_seconds: float = Field(..., ge=0, alias="ingestion_time_seconds")
    errors: list = Field(default_factory=list)

    class Config:
        populate_by_name = True


def verify_admin_key(x_admin_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verify admin API key from header.

    Args:
        x_admin_api_key: API key from X-Admin-API-Key header

    Returns:
        True if valid

    Raises:
        HTTPException: If key is missing or invalid
    """
    # For development, you might not have ADMIN_API_KEY set
    # In that case, allow access (development mode)
    expected_key = getattr(settings, 'admin_api_key', None)

    if expected_key is None:
        logger.warning("No admin API key configured - allowing access (dev mode)")
        return True

    if not x_admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Admin-API-Key header",
        )

    if x_admin_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    authorized: Optional[str] = Header(default=None, include_in_schema=False, alias="X-Admin-API-Key"),
) -> IngestResponse:
    """
    Ingest documentation files into the vector database.

    This endpoint:
    1. Scans the documentation directory for markdown files
    2. Chunks each file into semantic segments
    3. Generates embeddings using Cohere
    4. Stores chunks in Qdrant vector database

    **Authentication**: Requires X-Admin-API-Key header

    Args:
        request: IngestRequest with docs_path and force_reindex options
        authorized: Admin API key verification (from header)

    Returns:
        IngestResponse with ingestion statistics

    Raises:
        HTTPException: If unauthorized or ingestion fails
    """
    try:
        # Verify admin authentication
        verify_admin_key(authorized)

        logger.info(
            f"Starting ingestion: path={request.docs_path}, "
            f"force_reindex={request.force_reindex}"
        )

        # Get ingestion service
        ingestion_service = get_ingestion_service()

        # Run ingestion
        result = await ingestion_service.ingest_documents(
            docs_path=request.docs_path,
            force_reindex=request.force_reindex,
        )

        # Build response
        response = IngestResponse(
            status=result["status"],
            files_processed=result["files_processed"],
            total_chunks_created=result["chunks_created"],
            ingestion_time_seconds=result["duration_seconds"],
            errors=result.get("errors", []),
        )

        # Return appropriate status code
        if result["status"] == "failed":
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response.model_dump(),
            )
        elif result["status"] == "partial":
            return JSONResponse(
                status_code=status.HTTP_207_MULTI_STATUS,
                content=response.model_dump(),
            )
        else:
            return response

    except HTTPException:
        # Re-raise auth errors
        raise

    except ValueError as e:
        # Validation errors (e.g., path doesn't exist)
        logger.warning(f"Invalid ingestion request: {e}")
        error_response = ErrorResponse(
            error_code="INVALID_REQUEST",
            message=str(e),
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        error_response = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="Failed to ingest documents. Please try again.",
            details={"error": str(e)},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


class SitemapIngestResponse(BaseModel):
    """Response model for sitemap-based ingestion."""

    status: str = Field(..., description="completed | partial | failed")
    pages_processed: int = Field(..., ge=0)
    pages_failed: int = Field(..., ge=0)
    chunks_created: int = Field(..., ge=0)
    duration_seconds: float = Field(..., ge=0)
    errors: list = Field(default_factory=list)


@router.post("/ingest/sitemap", response_model=SitemapIngestResponse)
async def ingest_from_sitemap(
    request: SitemapIngestRequest,
    authorized: Optional[str] = Header(default=None, include_in_schema=False, alias="X-Admin-API-Key"),
) -> SitemapIngestResponse:
    """
    Ingest web pages from a sitemap into the vector database.

    This endpoint:
    1. Fetches all URLs from the provided sitemap.xml
    2. Scrapes the main content from each page
    3. Chunks the text into semantic segments
    4. Generates embeddings using Cohere
    5. Stores chunks in Qdrant vector database

    **Authentication**: Requires X-Admin-API-Key header

    Args:
        request: SitemapIngestRequest with sitemap URL and options
        authorized: Admin API key verification (from header)

    Returns:
        SitemapIngestResponse with ingestion statistics

    Raises:
        HTTPException: If unauthorized or ingestion fails
    """
    try:
        # Verify admin authentication
        verify_admin_key(authorized)

        logger.info(
            f"Starting sitemap ingestion: url={request.sitemap_url}, "
            f"force_reindex={request.force_reindex}, "
            f"batch_size={request.batch_size}, "
            f"chunk_size={request.chunk_size}"
        )

        # Get ingestion service with custom chunk settings
        ingestion_service = get_sitemap_ingestion_service(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

        # Run ingestion
        result = await ingestion_service.ingest_from_sitemap(
            sitemap_url=request.sitemap_url,
            force_reindex=request.force_reindex,
            batch_size=request.batch_size,
        )

        # Build response
        response = SitemapIngestResponse(
            status=result["status"],
            pages_processed=result["pages_processed"],
            pages_failed=result["pages_failed"],
            chunks_created=result["chunks_created"],
            duration_seconds=result["duration_seconds"],
            errors=result.get("errors", []),
        )

        # Return appropriate status code
        if result["status"] == "failed":
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response.model_dump(),
            )
        elif result["status"] == "partial":
            return JSONResponse(
                status_code=status.HTTP_207_MULTI_STATUS,
                content=response.model_dump(),
            )
        else:
            return response

    except HTTPException:
        # Re-raise auth errors
        raise

    except ValueError as e:
        # Validation errors (e.g., invalid sitemap URL)
        logger.warning(f"Invalid sitemap ingestion request: {e}")
        error_response = ErrorResponse(
            error_code="INVALID_REQUEST",
            message=str(e),
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Sitemap ingestion failed: {e}", exc_info=True)
        error_response = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="Failed to ingest sitemap. Please try again.",
            details={"error": str(e)},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
