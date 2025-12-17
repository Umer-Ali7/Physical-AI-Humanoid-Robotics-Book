"""
Text generation service using Cohere API.

Generates grounded responses using retrieved context.
"""

import logging
from typing import List, Dict, Any

import cohere
# from cohere.errors import CohereAPIError

from app.config import settings

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating text using Cohere's generation API."""

    def __init__(self):
        """Initialize Cohere client."""
        self.client = cohere.Client(api_key=settings.cohere_api_key)
        self.model = "command-r-plus"  # Cohere's best model for RAG
        logger.info(f"Initialized GenerationService with model: {self.model}")

    async def generate_response(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        max_words: int = 200,
    ) -> Dict[str, Any]:
        """
        Generate a grounded response using retrieved context.

        Args:
            query: User's question
            retrieved_chunks: List of retrieved document chunks with metadata
            max_words: Maximum words in the response

        Returns:
            Dictionary with 'answer', 'citations', and 'confidence_score'

        Raises:
            CohereAPIError: If API call fails
        """
        try:
            # Format retrieved chunks as context
            context_parts = []
            for idx, chunk in enumerate(retrieved_chunks, 1):
                context_parts.append(
                    f"[Source {idx}] {chunk['text']}\n"
                    f"(From: {chunk['chapter_id']} - {chunk['section_name']})"
                )

            context = "\n\n".join(context_parts)

            # Create the prompt with strict grounding instructions
            system_message = """You are a helpful AI assistant for the Physical AI documentation.

Your role is to answer questions based ONLY on the provided documentation context. Follow these rules strictly:
1. Only use information from the context provided below
2. If the context doesn't contain relevant information, say "I don't have information about that in the documentation"
3. Cite sources by referencing [Source 1], [Source 2], etc.
4. Be concise but comprehensive
5. Never make up information or use external knowledge"""

            user_prompt = f"""Context from documentation:

{context}

User Question: {query}

Answer (cite sources, max {max_words} words):"""

            # Call Cohere's chat API
            response = self.client.chat(
                message=user_prompt,
                preamble=system_message,
                model=self.model,
                temperature=0.3,  # Lower temperature for more focused responses
                max_tokens=max_words * 2,  # Approximate tokens (1 word ≈ 1.5 tokens)
            )

            # Extract answer
            answer = response.text.strip()

            # Build citations from retrieved chunks
            citations = []
            for idx, chunk in enumerate(retrieved_chunks, 1):
                # Check if the source is referenced in the answer
                if f"[Source {idx}]" in answer:
                    citations.append({
                        "chapter_id": chunk["chapter_id"],
                        "section_name": chunk["section_name"],
                        "chunk_id": chunk["chunk_id"],
                        "similarity_score": chunk["score"],
                    })

            # Calculate confidence based on average similarity score
            avg_score = (
                sum(c["similarity_score"] for c in citations) / len(citations)
                if citations
                else 0.0
            )

            logger.info(
                f"Generated response with {len(citations)} citations "
                f"(confidence: {avg_score:.2f})"
            )

            return {
                "answer": answer,
                "citations": citations,
                "confidence_score": avg_score,
                "chunks_used": [c["chunk_id"] for c in retrieved_chunks],
            }

        except Exception as e:
          logger.error(f"Generation failed: {e}")
          raise RuntimeError("Cohere generation failed")



# Singleton instance
_generation_service: GenerationService | None = None


def get_generation_service() -> GenerationService:
    """
    Get singleton generation service instance.

    Returns:
        GenerationService instance
    """
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service
