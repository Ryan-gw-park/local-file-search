"""
Local Finder X v2.0 - PII Masking

Regex-based PII detection and masking for UI display.
"""

import re
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum


class PIIType(str, Enum):
    """Types of PII that can be detected."""
    SSN = "ssn"
    PHONE = "phone"
    EMAIL = "email"
    CREDIT_CARD = "credit_card"
    RESIDENT_ID = "resident_id"  # Korean resident registration number


# =============================================================================
# PII Patterns
# =============================================================================

PII_PATTERNS: Dict[PIIType, re.Pattern] = {
    # US Social Security Number (XXX-XX-XXXX)
    PIIType.SSN: re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    
    # Phone numbers (various formats)
    PIIType.PHONE: re.compile(
        r"\b(?:\+?82[-.\s]?)?"  # Korean country code
        r"(?:0?1[0-9])[-.\s]?"   # Korean mobile prefix
        r"\d{3,4}[-.\s]?\d{4}\b" # Number
        r"|\b\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}\b"  # General format
    ),
    
    # Email addresses
    PIIType.EMAIL: re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ),
    
    # Credit card numbers (13-19 digits, with optional separators)
    PIIType.CREDIT_CARD: re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{1,4}\b"
    ),
    
    # Korean resident registration number (YYMMDD-XXXXXXX)
    PIIType.RESIDENT_ID: re.compile(
        r"\b\d{6}[-\s]?[1-4]\d{6}\b"
    ),
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PIIMatch:
    """A detected PII match."""
    pii_type: PIIType
    start: int
    end: int
    original: str
    masked: str


# =============================================================================
# PII Functions
# =============================================================================

def detect_pii(text: str) -> List[PIIMatch]:
    """
    Detect PII in text.
    
    Args:
        text: Text to scan for PII.
    
    Returns:
        List of PIIMatch objects.
    """
    matches = []
    
    for pii_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            original = match.group()
            masked = mask_value(original, pii_type)
            
            matches.append(PIIMatch(
                pii_type=pii_type,
                start=match.start(),
                end=match.end(),
                original=original,
                masked=masked,
            ))
    
    # Sort by position
    matches.sort(key=lambda m: m.start)
    
    return matches


def mask_value(value: str, pii_type: PIIType) -> str:
    """
    Mask a PII value.
    
    Args:
        value: Original value.
        pii_type: Type of PII.
    
    Returns:
        Masked value.
    """
    if pii_type == PIIType.EMAIL:
        # Show first 2 chars of local part + domain
        parts = value.split("@")
        if len(parts) == 2:
            local = parts[0][:2] + "***" if len(parts[0]) > 2 else "***"
            return f"{local}@{parts[1]}"
    
    elif pii_type == PIIType.PHONE:
        # Show last 4 digits
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 4:
            return "***-****-" + digits[-4:]
    
    elif pii_type == PIIType.SSN:
        return "***-**-****"
    
    elif pii_type == PIIType.CREDIT_CARD:
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 4:
            return "****-****-****-" + digits[-4:]
    
    elif pii_type == PIIType.RESIDENT_ID:
        return "******-*******"
    
    # Default: replace with asterisks
    return "*" * len(value)


def mask_text(text: str) -> Tuple[str, List[PIIMatch]]:
    """
    Mask all PII in text.
    
    Args:
        text: Text to mask.
    
    Returns:
        Tuple of (masked_text, list of matches).
    """
    matches = detect_pii(text)
    
    if not matches:
        return text, []
    
    # Build masked text
    result = []
    last_end = 0
    
    for match in matches:
        result.append(text[last_end:match.start])
        result.append(match.masked)
        last_end = match.end
    
    result.append(text[last_end:])
    
    return "".join(result), matches


def has_pii(text: str) -> bool:
    """Check if text contains any PII."""
    for pattern in PII_PATTERNS.values():
        if pattern.search(text):
            return True
    return False


def get_pii_summary(text: str) -> Dict[str, int]:
    """Get count of each PII type in text."""
    matches = detect_pii(text)
    summary = {}
    
    for match in matches:
        key = match.pii_type.value
        summary[key] = summary.get(key, 0) + 1
    
    return summary


__all__ = [
    "PIIType",
    "PIIMatch",
    "detect_pii",
    "mask_value",
    "mask_text",
    "has_pii",
    "get_pii_summary",
]
