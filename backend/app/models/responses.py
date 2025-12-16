"""Response models for API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmbedResponse(BaseModel):
    """Response for book content embedding."""

    status: str = Field(default="success")
    total_chunks_created: int = Field(..., ge=0)
    total_chapters_processed: int = Field(..., ge=1)
    ingestion_time_seconds: float = Field(..., ge=0)


class ChunkReference(BaseModel):
    """Citation metadata for a retrieved chunk."""

    chapter_id: str
    section_name: str
    chunk_id: str  # UUID as string
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    """Response for RAG query (standard or selected-text mode)."""

    answer: str
    citations: List[ChunkReference] = Field(default_factory=list)
    chunks_used: List[str] = Field(default_factory=list)  # List of chunk_ids
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    no_search_performed: bool = Field(default=False)
    source: Optional[str] = Field(default=None)  # "user_selection" for selected-query
    selected_text_length: Optional[int] = Field(default=None)  # Token count


class HealthResponse(BaseModel):
    """Response for health check endpoint."""

    status: str  # "healthy" | "degraded" | "unhealthy"
    qdrant_connected: bool
    neon_connected: bool
    total_chunks_indexed: int = Field(..., ge=0)
    total_chapters: int = Field(..., ge=0)
    uptime_seconds: float = Field(..., ge=0)
    error: Optional[str] = Field(default=None)


class ErrorResponse(BaseModel):
    """Structured error response."""

    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
