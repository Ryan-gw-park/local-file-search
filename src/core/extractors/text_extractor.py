"""
Local Finder X v2.0 - Text and Markdown Extractor

Extracts content from plain text and Markdown files.
"""

import re
from typing import List, Dict, Any

from .base import BaseExtractor, ExtractorResult, register_extractor


@register_extractor
class TextExtractor(BaseExtractor):
    """Extractor for plain text files."""
    
    SUPPORTED_EXTENSIONS = [".txt", ".text"]
    
    # Encodings to try
    ENCODINGS = ["utf-8", "cp949", "euc-kr", "latin-1"]
    
    def extract(self, file_path: str) -> ExtractorResult:
        """Extract content from a text file."""
        try:
            text = self._read_file(file_path)
            
            if text is None:
                return self._create_error_result(
                    f"Could not read file with any known encoding"
                )
            
            return self._create_success_result(text=text)
            
        except Exception as e:
            return self._create_error_result(f"Error extracting text file: {str(e)}")
    
    def _read_file(self, file_path: str) -> str:
        """Read file with automatic encoding detection."""
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None


@register_extractor
class MarkdownExtractor(BaseExtractor):
    """Extractor for Markdown files with structure parsing."""
    
    SUPPORTED_EXTENSIONS = [".md", ".markdown"]
    
    ENCODINGS = ["utf-8", "cp949", "euc-kr", "latin-1"]
    
    def extract(self, file_path: str) -> ExtractorResult:
        """Extract content from a Markdown file."""
        try:
            text = self._read_file(file_path)
            
            if text is None:
                return self._create_error_result(
                    f"Could not read file with any known encoding"
                )
            
            sections = self._parse_sections(text)
            
            return self._create_success_result(
                text=text,
                sections=sections,
            )
            
        except Exception as e:
            return self._create_error_result(f"Error extracting Markdown: {str(e)}")
    
    def _read_file(self, file_path: str) -> str:
        """Read file with automatic encoding detection."""
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
    
    def _parse_sections(self, text: str) -> List[Dict[str, Any]]:
        """Parse Markdown into sections based on headings."""
        sections = []
        current_section = {"type": "content", "content": []}
        
        # Regex for Markdown headings
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        
        lines = text.split("\n")
        i = 0
        
        while i < len(lines):
            line = lines[i]
            match = heading_pattern.match(line)
            
            if match:
                # Save previous section
                if current_section["content"]:
                    sections.append(current_section)
                
                level = len(match.group(1))
                title = match.group(2).strip()
                
                current_section = {
                    "type": "heading",
                    "level": level,
                    "title": title,
                    "content": [],
                }
            else:
                if line.strip():
                    current_section["content"].append(line)
            
            i += 1
        
        # Add last section
        if current_section["content"] or current_section.get("title"):
            sections.append(current_section)
        
        return sections


__all__ = ["TextExtractor", "MarkdownExtractor"]
