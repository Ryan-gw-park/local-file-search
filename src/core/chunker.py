"""
Local Finder X v2.0 - Structural Chunker

File-type-specific chunking with location metadata.
Based on Master Plan Phase 3 specifications.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from src.core.file_classifier import FileType, get_file_type
from src.core.extractors import ExtractorResult


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CHUNK_SIZE = 1000  # characters
DEFAULT_CHUNK_OVERLAP = 100  # characters


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Chunk:
    """A single chunk with text and location metadata."""
    text: str
    chunk_index: int
    # Location metadata
    page: Optional[int] = None
    slide: Optional[int] = None
    slide_title: Optional[str] = None
    sheet: Optional[str] = None
    row_range: Optional[str] = None
    header_path: Optional[List[str]] = None
    
    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert to metadata dictionary."""
        return {
            "page": self.page,
            "slide": self.slide,
            "slide_title": self.slide_title,
            "sheet": self.sheet,
            "row_range": self.row_range,
            "header_path": self.header_path,
        }


# =============================================================================
# Chunker Classes
# =============================================================================

class BaseChunker:
    """Base chunker with simple text splitting."""
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Chunk]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Full text to chunk.
            sections: Optional structured sections from extractor.
        
        Returns:
            List of Chunk objects.
        """
        return self._simple_chunk(text)
    
    def _simple_chunk(self, text: str) -> List[Chunk]:
        """Simple character-based chunking with overlap."""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_idx = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at a sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break + 2
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind(".", start, end),
                        text.rfind("!", start, end),
                        text.rfind("?", start, end),
                        text.rfind("。", start, end),  # Korean/Chinese period
                    )
                    if sentence_break > start + self.chunk_size // 2:
                        end = sentence_break + 1
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    chunk_index=chunk_idx,
                ))
                chunk_idx += 1
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks


class PDFChunker(BaseChunker):
    """PDF-specific chunker with page metadata."""
    
    def chunk(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Chunk]:
        """Chunk PDF with page-based sections."""
        if not sections:
            return self._simple_chunk(text)
        
        chunks = []
        chunk_idx = 0
        
        for section in sections:
            if section.get("type") != "page":
                continue
            
            page_num = section.get("page_number", 1)
            page_content = "\n".join(section.get("content", []))
            
            if not page_content.strip():
                continue
            
            # Chunk this page
            page_chunks = self._simple_chunk(page_content)
            for chunk in page_chunks:
                chunk.chunk_index = chunk_idx
                chunk.page = page_num
                chunks.append(chunk)
                chunk_idx += 1
        
        return chunks


class SlideChunker(BaseChunker):
    """PowerPoint-specific chunker with slide metadata."""
    
    def chunk(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Chunk]:
        """Chunk PowerPoint with slide-based sections."""
        if not sections:
            return self._simple_chunk(text)
        
        chunks = []
        chunk_idx = 0
        
        for section in sections:
            if section.get("type") != "slide":
                continue
            
            slide_num = section.get("slide_number", 1)
            slide_title = section.get("title", "")
            slide_content = "\n".join(section.get("content", []))
            
            if not slide_content.strip():
                continue
            
            # Create single chunk per slide (slides are usually short)
            chunks.append(Chunk(
                text=slide_content,
                chunk_index=chunk_idx,
                slide=slide_num,
                slide_title=slide_title,
            ))
            chunk_idx += 1
        
        return chunks


class ExcelChunker(BaseChunker):
    """Excel-specific chunker with sheet metadata."""
    
    def chunk(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Chunk]:
        """Chunk Excel with sheet-based sections."""
        if not sections:
            return self._simple_chunk(text)
        
        chunks = []
        chunk_idx = 0
        
        for section in sections:
            if section.get("type") != "sheet":
                continue
            
            sheet_name = section.get("name", "Sheet")
            sheet_content = "\n".join(section.get("content", []))
            row_count = section.get("row_count", 0)
            
            if not sheet_content.strip():
                continue
            
            # For large sheets, split into chunks
            if len(sheet_content) > self.chunk_size:
                sheet_chunks = self._simple_chunk(sheet_content)
                for chunk in sheet_chunks:
                    chunk.chunk_index = chunk_idx
                    chunk.sheet = sheet_name
                    chunks.append(chunk)
                    chunk_idx += 1
            else:
                chunks.append(Chunk(
                    text=sheet_content,
                    chunk_index=chunk_idx,
                    sheet=sheet_name,
                ))
                chunk_idx += 1
        
        return chunks


class HeadingChunker(BaseChunker):
    """Heading-based chunker for Word and Markdown."""
    
    def chunk(
        self,
        text: str,
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Chunk]:
        """Chunk based on heading structure."""
        if not sections:
            return self._simple_chunk(text)
        
        chunks = []
        chunk_idx = 0
        header_path = []
        
        for section in sections:
            section_type = section.get("type", "")
            
            if section_type == "heading":
                level = section.get("level", 1)
                title = section.get("title", "")
                
                # Update header path
                while len(header_path) >= level:
                    header_path.pop()
                header_path.append(title)
            
            content = section.get("content", [])
            section_text = "\n".join(content)
            
            if not section_text.strip():
                continue
            
            # Chunk this section
            if len(section_text) > self.chunk_size:
                section_chunks = self._simple_chunk(section_text)
                for chunk in section_chunks:
                    chunk.chunk_index = chunk_idx
                    chunk.header_path = list(header_path)
                    chunks.append(chunk)
                    chunk_idx += 1
            else:
                chunks.append(Chunk(
                    text=section_text,
                    chunk_index=chunk_idx,
                    header_path=list(header_path),
                ))
                chunk_idx += 1
        
        return chunks


# =============================================================================
# Main Function
# =============================================================================

def get_chunker_for_file_type(file_type: FileType) -> BaseChunker:
    """Get the appropriate chunker for a file type."""
    if file_type == FileType.PDF:
        return PDFChunker()
    elif file_type == FileType.POWERPOINT:
        return SlideChunker()
    elif file_type == FileType.EXCEL:
        return ExcelChunker()
    elif file_type in {FileType.WORD, FileType.MARKDOWN}:
        return HeadingChunker()
    else:
        return BaseChunker()


def chunk_content(
    file_path: str,
    extractor_result: ExtractorResult,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Chunk]:
    """
    Chunk extracted content using file-type-specific logic.
    
    Args:
        file_path: Path to the file.
        extractor_result: Result from content extraction.
        chunk_size: Maximum chunk size in characters.
        chunk_overlap: Overlap between chunks.
    
    Returns:
        List of Chunk objects.
    """
    file_type = get_file_type(file_path)
    chunker = get_chunker_for_file_type(file_type)
    chunker.chunk_size = chunk_size
    chunker.chunk_overlap = chunk_overlap
    
    return chunker.chunk(
        extractor_result.text,
        extractor_result.sections,
    )


__all__ = [
    "Chunk",
    "BaseChunker",
    "PDFChunker",
    "SlideChunker",
    "ExcelChunker",
    "HeadingChunker",
    "get_chunker_for_file_type",
    "chunk_content",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CHUNK_OVERLAP",
]
