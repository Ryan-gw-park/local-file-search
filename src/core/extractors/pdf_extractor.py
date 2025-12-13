"""
Local Finder X v2.0 - PDF Extractor

Extracts content from PDF files using PyPDF2.
"""

from typing import List, Dict, Any

from .base import BaseExtractor, ExtractorResult, register_extractor

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    PdfReader = None


@register_extractor
class PDFExtractor(BaseExtractor):
    """Extractor for PDF documents."""
    
    SUPPORTED_EXTENSIONS = [".pdf"]
    
    def extract(self, file_path: str) -> ExtractorResult:
        """Extract content from a PDF file."""
        if not PDF_AVAILABLE:
            return self._create_error_result(
                "PyPDF2 is not installed. Install with: pip install pypdf2"
            )
        
        try:
            reader = PdfReader(file_path)
            
            sections = []
            full_text_parts = []
            
            for page_idx, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        sections.append({
                            "type": "page",
                            "page_number": page_idx,
                            "content": [text.strip()],
                        })
                        
                        full_text_parts.append(f"## Page {page_idx}")
                        full_text_parts.append(text.strip())
                except Exception as e:
                    # Some pages may fail to extract
                    continue
            
            full_text = "\n\n".join(full_text_parts)
            
            metadata = {
                "page_count": len(reader.pages),
            }
            
            # Try to get PDF metadata
            try:
                if reader.metadata:
                    if reader.metadata.author:
                        metadata["author"] = reader.metadata.author
                    if reader.metadata.title:
                        metadata["title"] = reader.metadata.title
                    if reader.metadata.creator:
                        metadata["creator"] = reader.metadata.creator
            except Exception:
                pass
            
            return self._create_success_result(
                text=full_text,
                sections=sections,
                metadata=metadata,
            )
            
        except Exception as e:
            return self._create_error_result(f"Error extracting PDF: {str(e)}")


__all__ = ["PDFExtractor", "PDF_AVAILABLE"]
