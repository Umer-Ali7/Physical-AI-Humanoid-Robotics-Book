"""
Chat endpoint for RAG-powered question answering.

Provides API for users to ask questions and receive grounded answers.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.requests import QueryRequest
from app.models.responses import QueryResponse, ErrorResponse
from app.services.rag_pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=QueryResponse)
async def chat_query(request: QueryRequest) -> QueryResponse:
    """
    Process a chat query and return an AI-generated answer.

    This endpoint performs RAG (Retrieval-Augmented Generation):
    1. Embeds the user's query
    2. Retrieves relevant document chunks from Qdrant
    3. Generates a grounded response using Cohere
    4. Returns answer with source citations

    Args:
        request: QueryRequest with query_text and optional max_words

    Returns:
        QueryResponse with answer, citations, and confidence score

    Raises:
        HTTPException: If query processing fails
    """
    try:
        logger.info(f"Received chat query: {request.query_text[:100]}...")

        # Get RAG pipeline
        rag_pipeline = get_rag_pipeline()

        # Process query through RAG pipeline
        result = await rag_pipeline.process_query(
            query_text=request.query_text,
            max_words=request.max_words,
            top_k=3,  # Retrieve top 3 most relevant chunks
            score_threshold=0.3,  # Lowered from 0.7 to allow more results
        )

        # Build response
        response = QueryResponse(
            answer=result["answer"],
            citations=result["citations"],
            chunks_used=result["chunks_used"],
            confidence_score=result["confidence_score"],
            no_search_performed=False,
            source="standard_rag",
        )

        logger.info(
            f"Chat query processed successfully: "
            f"{len(response.citations)} citations, confidence={response.confidence_score:.2f}"
        )

        return response

    except ValueError as e:
        # Validation errors (e.g., query too long)
        logger.warning(f"Invalid query request: {e}")
        error_response = ErrorResponse(
            error_code="INVALID_REQUEST",
            message=str(e),
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump(),
        )

    except Exception as e:
        # Unexpected errors (database, API, etc.)
        logger.error(f"Chat query failed: {e}", exc_info=True)
        error_response = ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="Failed to process query. Please try again.",
            details={"error": str(e)},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )
