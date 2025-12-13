"""
Local Finder X v2.0 - Tokenizer

Korean (Kiwi) and English tokenization for BM25.
"""

import re
from typing import List, Optional

try:
    from kiwipiepy import Kiwi
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False
    Kiwi = None


# =============================================================================
# Singleton Kiwi Instance
# =============================================================================

_kiwi_instance: Optional[Kiwi] = None


def _get_kiwi() -> Optional[Kiwi]:
    """Get or create singleton Kiwi instance."""
    global _kiwi_instance
    if not KIWI_AVAILABLE:
        return None
    if _kiwi_instance is None:
        _kiwi_instance = Kiwi()
    return _kiwi_instance


# =============================================================================
# Tokenization Functions
# =============================================================================

# Korean character ranges
KOREAN_PATTERN = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\ud7b0-\ud7ff]")

# English word pattern
ENGLISH_PATTERN = re.compile(r"[a-zA-Z]+")

# Number pattern
NUMBER_PATTERN = re.compile(r"\d+")


def is_korean_text(text: str) -> bool:
    """Check if text contains Korean characters."""
    return bool(KOREAN_PATTERN.search(text))


def tokenize_korean(text: str) -> List[str]:
    """
    Tokenize Korean text using Kiwi.
    
    Args:
        text: Text to tokenize.
    
    Returns:
        List of tokens.
    """
    kiwi = _get_kiwi()
    if kiwi is None:
        # Fallback to simple whitespace tokenization
        return tokenize_simple(text)
    
    tokens = []
    
    try:
        result = kiwi.tokenize(text)
        for token in result:
            form = token.form.strip()
            # Filter by POS tags (keep nouns, verbs, adjectives)
            # N: Nouns, V: Verbs, MA: Adverbs, XR: Roots
            if token.tag.startswith(("N", "V", "MA", "XR")):
                if len(form) >= 2:  # Skip single characters
                    tokens.append(form.lower())
    except Exception:
        # Fallback on error
        return tokenize_simple(text)
    
    return tokens


def tokenize_english(text: str) -> List[str]:
    """
    Simple English tokenization.
    
    Args:
        text: Text to tokenize.
    
    Returns:
        List of tokens.
    """
    tokens = []
    
    # Find all English words
    words = ENGLISH_PATTERN.findall(text.lower())
    
    for word in words:
        if len(word) >= 2:  # Skip single characters
            tokens.append(word)
    
    return tokens


def tokenize_simple(text: str) -> List[str]:
    """
    Simple whitespace/punctuation-based tokenization.
    
    Args:
        text: Text to tokenize.
    
    Returns:
        List of tokens.
    """
    # Split on whitespace and punctuation
    tokens = re.split(r"[\s\.,!?;:\"\'()\[\]{}<>]+", text.lower())
    
    # Filter tokens
    return [t for t in tokens if len(t) >= 2]


def tokenize(text: str) -> List[str]:
    """
    Smart tokenization that handles both Korean and English.
    
    Args:
        text: Text to tokenize.
    
    Returns:
        List of tokens.
    """
    if not text.strip():
        return []
    
    tokens = []
    
    # Tokenize Korean if present
    if is_korean_text(text):
        korean_tokens = tokenize_korean(text)
        tokens.extend(korean_tokens)
    
    # Always tokenize English words
    english_tokens = tokenize_english(text)
    tokens.extend(english_tokens)
    
    # Add numbers as tokens (for document numbers, dates, etc.)
    numbers = NUMBER_PATTERN.findall(text)
    tokens.extend(numbers)
    
    # Deduplicate while preserving order
    seen = set()
    unique_tokens = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    
    return unique_tokens


def tokenize_query(query: str) -> List[str]:
    """
    Tokenize a search query.
    
    Same as tokenize() but may have different preprocessing.
    
    Args:
        query: Search query.
    
    Returns:
        List of tokens.
    """
    return tokenize(query)


__all__ = [
    "KIWI_AVAILABLE",
    "is_korean_text",
    "tokenize_korean",
    "tokenize_english",
    "tokenize_simple",
    "tokenize",
    "tokenize_query",
]
