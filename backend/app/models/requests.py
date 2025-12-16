"""Request models for API endpoints."""

from typing import List

from pydantic import BaseModel, Field, field_validator


class Section(BaseModel):
    """Book section with content."""

    section_name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)


class Chapter(BaseModel):
    """Book chapter with sections."""

    chapter_id: str = Field(..., pattern=r"^ch\d{2}$")
    chapter_title: str = Field(..., min_length=1, max_length=200)
    sections: List[Section] = Field(..., min_items=1)


class EmbedRequest(BaseModel):
    """Request for embedding book content."""

    chapters: List[Chapter] = Field(..., min_items=1)


class QueryRequest(BaseModel):
    """Request for standard RAG query."""

    query_text: str = Field(..., min_length=1, max_length=2000)
    max_words: int = Field(default=200, ge=50, le=500)

    @field_validator("query_text")
    @classmethod
    def validate_token_count(cls, v: str) -> str:
        """Validate query doesn't exceed token limit (approximate)."""
        # Approximate: 1 token ≈ 4 characters
        estimated_tokens = len(v) / 4
        if estimated_tokens > 500:
            raise ValueError("Query exceeds 500 tokens")
        return v


class SelectedQueryRequest(BaseModel):
    """Request for selected-text query (context override)."""

    query_text: str = Field(..., min_length=1, max_length=2000)
    selected_text: str = Field(..., min_length=40, max_length=8000)
    max_words: int = Field(default=200, ge=50, le=500)

    @field_validator("selected_text")
    @classmethod
    def validate_selected_text_tokens(cls, v: str) -> str:
        """Validate selected text is within token range."""
        # Approximate: 1 token ≈ 4 characters
        estimated_tokens = len(v) / 4
        if estimated_tokens < 10:
            raise ValueError("Selected text too short (min 10 tokens)")
        if estimated_tokens > 2000:
            raise ValueError("Selected text too long (max 2000 tokens)")
        return v
