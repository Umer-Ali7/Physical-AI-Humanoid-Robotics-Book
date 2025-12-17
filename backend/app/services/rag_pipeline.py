"""
RAG (Retrieval-Augmented Generation) pipeline service.

Orchestrates the full RAG flow: query → embed → retrieve → generate.
"""

import logging
from typing import Dict, Any

from app.services.retrieval import get_retrieval_service
from app.services.generation import get_generation_service

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG pipeline that combines retrieval and generation.

    Flow:
    1. User query → Embedding
    2. Embedding → Semantic search in Qdrant
    3. Retrieved chunks + query → LLM generation
    4. Response with citations
    """

    def __init__(self):
        """Initialize RAG pipeline with required services."""
        self.retrieval_service = get_retrieval_service()
        self.generation_service = get_generation_service()
        logger.info("Initialized RAGPipeline")

    async def process_query(
        self,
        query_text: str,
        max_words: int = 200,
        top_k: int = 3,
        score_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.

        Args:
            query_text: User's question
            max_words: Maximum words in response (default: 200)
            top_k: Number of chunks to retrieve (default: 3)
            score_threshold: Minimum similarity score (default: 0.7)

        Returns:
            Dictionary with:
                - answer: Generated response text
                - citations: List of source citations
                - confidence_score: Overall confidence (0-1)
                - chunks_used: List of chunk IDs used
                - no_results_found: Boolean flag

        Raises:
            Exception: If pipeline fails
        """
        try:
            logger.info(f"Processing query: {query_text[:100]}...")

            # Step 1: Retrieve relevant chunks
            retrieved_chunks = await self.retrieval_service.search(
                query=query_text,
                top_k=top_k,
                score_threshold=score_threshold,
            )

            # Check if any relevant chunks were found
            if not retrieved_chunks:
                logger.warning("No relevant chunks found for query")
                return {
                    "answer": (
                        "I couldn't find information about that in the documentation. "
                        "Please try rephrasing your question or consult the full documentation."
                    ),
                    "citations": [],
                    "confidence_score": 0.0,
                    "chunks_used": [],
                    "no_results_found": True,
                }

            # Step 2: Generate response using retrieved context
            generation_result = await self.generation_service.generate_response(
                query=query_text,
                retrieved_chunks=retrieved_chunks,
                max_words=max_words,
            )

            # Step 3: Return complete result
            result = {
                "answer": generation_result["answer"],
                "citations": generation_result["citations"],
                "confidence_score": generation_result["confidence_score"],
                "chunks_used": generation_result["chunks_used"],
                "no_results_found": False,
            }

            logger.info(
                f"RAG pipeline completed: {len(result['citations'])} citations, "
                f"confidence={result['confidence_score']:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            raise


# Singleton instance
_rag_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Get singleton RAG pipeline instance.

    Returns:
        RAGPipeline instance
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
