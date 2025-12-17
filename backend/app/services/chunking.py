"""
Document chunking service for markdown files.

Splits markdown documents into semantic chunks for embedding and retrieval.
"""

import logging
import re
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MarkdownChunker:
    """Service for chunking markdown documents."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ):
        """
        Initialize markdown chunker.

        Args:
            chunk_size: Target size for each chunk in characters (default: 1000)
            chunk_overlap: Number of characters to overlap between chunks (default: 200)
            min_chunk_size: Minimum chunk size in characters (default: 100)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        logger.info(
            f"Initialized MarkdownChunker (size={chunk_size}, "
            f"overlap={chunk_overlap}, min={min_chunk_size})"
        )

    def chunk_markdown(
        self,
        content: str,
        file_path: str,
        chapter_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Chunk a markdown document into semantic segments.

        Args:
            content: Markdown content to chunk
            file_path: Path to the source file
            chapter_id: Chapter identifier (e.g., "ch01", "ch02")

        Returns:
            List of chunk dictionaries with:
                - text: chunk content
                - chapter_id: chapter identifier
                - section_name: section heading
                - chunk_index: position in document
                - file_path: source file path
        """
        try:
            # Extract sections from markdown
            sections = self._extract_sections(content)

            # Chunk each section
            all_chunks = []
            chunk_index = 0

            for section in sections:
                section_name = section["heading"]
                section_content = section["content"]

                # Split section into chunks if it's too large
                section_chunks = self._split_text(section_content)

                for chunk_text in section_chunks:
                    # Skip chunks that are too small
                    if len(chunk_text.strip()) < self.min_chunk_size:
                        continue

                    # Add section heading to chunk for context
                    full_chunk_text = f"{section_name}\n\n{chunk_text}"

                    all_chunks.append({
                        "text": full_chunk_text.strip(),
                        "chapter_id": chapter_id,
                        "section_name": section_name,
                        "chunk_index": chunk_index,
                        "file_path": file_path,
                    })
                    chunk_index += 1

            logger.info(
                f"Chunked {file_path}: {len(all_chunks)} chunks from "
                f"{len(sections)} sections"
            )

            return all_chunks

        except Exception as e:
            logger.error(f"Failed to chunk markdown file {file_path}: {e}")
            raise

    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Extract sections from markdown based on headings.

        Args:
            content: Markdown content

        Returns:
            List of dictionaries with 'heading' and 'content'
        """
        # Split by headers (##, ###, etc.)
        # Pattern matches markdown headers (## Header or ### Header)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')

        sections = []
        current_heading = "Introduction"
        current_content = []

        for line in lines:
            header_match = re.match(header_pattern, line)
            if header_match:
                # Save previous section
                if current_content:
                    sections.append({
                        "heading": current_heading,
                        "content": '\n'.join(current_content).strip(),
                    })

                # Start new section
                current_heading = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Add final section
        if current_content:
            sections.append({
                "heading": current_heading,
                "content": '\n'.join(current_content).strip(),
            })

        return sections

    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending near the end of chunk
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n\n')
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())

            # Move start position with overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks


# Singleton instance
_chunker: MarkdownChunker | None = None


def get_markdown_chunker() -> MarkdownChunker:
    """
    Get singleton markdown chunker instance.

    Returns:
        MarkdownChunker instance
    """
    global _chunker
    if _chunker is None:
        _chunker = MarkdownChunker(
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=100,
        )
    return _chunker
