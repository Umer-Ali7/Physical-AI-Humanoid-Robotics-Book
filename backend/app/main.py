"""
FastAPI application for RAG Chatbot.

Provides grounded question answering for Physical AI textbook with:
- Standard RAG mode (vector search + rerank + generate)
- Selected-text mode (context override)
- Zero hallucination guarantee
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import close_neon_pool, close_qdrant_client, get_neon_pool, get_qdrant_client
from app.models.responses import ErrorResponse

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Application startup time for uptime tracking
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting RAG Chatbot API")
    logger.info(f"Configuration: {settings.get_masked_config()}")

    try:
        # Initialize database connections
        await get_qdrant_client()
        await get_neon_pool()
        logger.info("All database connections initialized")
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAG Chatbot API")
    await close_qdrant_client()
    await close_neon_pool()
    logger.info("All connections closed")


# Create FastAPI application
app = FastAPI(
    title="RAG Chatbot API",
    description=(
        "AI-native RAG chatbot for Physical AI textbook. "
        "Features grounded retrieval, zero hallucinations, and user-selected-text mode."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (allow localhost for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware with correlation IDs
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests with correlation ID and timing."""
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{time.time()}")
    start_time = time.time()

    logger.info(
        f"[{correlation_id}] {request.method} {request.url.path} - Started",
        extra={"correlation_id": correlation_id},
    )

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"[{correlation_id}] {request.method} {request.url.path} - "
        f"Completed in {duration:.3f}s with status {response.status_code}",
        extra={"correlation_id": correlation_id, "duration": duration},
    )

    response.headers["X-Correlation-ID"] = correlation_id
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Convert unhandled exceptions to structured error responses."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"error": str(exc)},
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


# Simple health check endpoint (full health check will be added in Phase 4)
@app.get("/api/v1/health", tags=["health"])
async def health_check():
    """Quick health check endpoint."""
    uptime = time.time() - app_start_time
    return {
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
