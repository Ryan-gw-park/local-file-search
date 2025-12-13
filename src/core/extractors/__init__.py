"""
Local Finder X v2.0 - Content Extractors

Extractors for different file types.
"""

from .base import ExtractorResult, BaseExtractor, get_extractor_for_file
from .word_extractor import WordExtractor
from .excel_extractor import ExcelExtractor
from .ppt_extractor import PowerPointExtractor
from .pdf_extractor import PDFExtractor
from .text_extractor import TextExtractor, MarkdownExtractor


__all__ = [
    "ExtractorResult",
    "BaseExtractor",
    "get_extractor_for_file",
    "WordExtractor",
    "ExcelExtractor",
    "PowerPointExtractor",
    "PDFExtractor",
    "TextExtractor",
    "MarkdownExtractor",
]
