"""
Local Finder X v2.0 - Embedding Model Wrapper

Singleton wrapper for SentenceTransformer with device auto-detection.
Based on Master Plan Phase 3 specifications.
"""

import os
from typing import List, Optional, Union
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


# =============================================================================
# Configuration
# =============================================================================

# Default model - BGE-M3 for multilingual support
DEFAULT_MODEL_NAME = "BAAI/bge-m3"
# Fallback model - smaller, faster
FALLBACK_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Embedding dimension for BGE-M3
EMBEDDING_DIM = 1024


# =============================================================================
# Device Detection
# =============================================================================

def get_best_device() -> str:
    """
    Detect the best available device for inference.
    
    Priority: CUDA > MPS (Apple Silicon) > CPU
    
    Returns:
        Device string ("cuda", "mps", or "cpu").
    """
    if not TORCH_AVAILABLE:
        return "cpu"
    
    # Check CUDA
    if torch.cuda.is_available():
        return "cuda"
    
    # Check MPS (Apple Silicon)
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    
    return "cpu"


# =============================================================================
# Embedding Model Singleton
# =============================================================================

class EmbeddingModel:
    """
    Singleton wrapper for embedding model.
    
    Features:
    - Automatic device detection (CUDA/MPS/CPU)
    - Lazy loading (model loaded on first use)
    - Offline mode support via local_files_only
    """
    
    _instance: Optional["EmbeddingModel"] = None
    
    def __new__(cls) -> "EmbeddingModel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._model: Optional[SentenceTransformer] = None
        self._model_name: Optional[str] = None
        self._device: Optional[str] = None
        self._initialized = True
    
    @property
    def device(self) -> str:
        """Get the current device."""
        if self._device is None:
            self._device = get_best_device()
        return self._device
    
    @property
    def model(self) -> Optional[SentenceTransformer]:
        """Lazy-load the model."""
        if self._model is None:
            self._load_model()
        return self._model
    
    @property
    def model_name(self) -> str:
        """Get the current model name."""
        if self._model_name is None:
            self._model_name = DEFAULT_MODEL_NAME
        return self._model_name
    
    def _load_model(
        self,
        model_name: Optional[str] = None,
        local_files_only: bool = False,
    ) -> None:
        """
        Load the embedding model.
        
        Args:
            model_name: Model name or path. Uses default if None.
            local_files_only: If True, only use cached/local models.
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("Warning: sentence-transformers not installed")
            return
        
        model_name = model_name or DEFAULT_MODEL_NAME
        device = self.device
        
        try:
            print(f"Loading embedding model: {model_name} on {device}")
            
            self._model = SentenceTransformer(
                model_name,
                device=device,
            )
            self._model_name = model_name
            
            print(f"Model loaded successfully")
            
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            
            # Try fallback model
            if model_name != FALLBACK_MODEL_NAME:
                print(f"Trying fallback model: {FALLBACK_MODEL_NAME}")
                try:
                    self._model = SentenceTransformer(
                        FALLBACK_MODEL_NAME,
                        device=device,
                    )
                    self._model_name = FALLBACK_MODEL_NAME
                    print(f"Fallback model loaded successfully")
                except Exception as e2:
                    print(f"Error loading fallback model: {e2}")
                    self._model = None
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        show_progress_bar: bool = False,
    ) -> Optional[np.ndarray]:
        """
        Encode text(s) to embeddings.
        
        Args:
            texts: Single text or list of texts.
            normalize: Whether to normalize embeddings.
            show_progress_bar: Show encoding progress.
        
        Returns:
            NumPy array of embeddings, or None if model not available.
        """
        if self.model is None:
            return None
        
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress_bar,
            )
            return embeddings
        except Exception as e:
            print(f"Error encoding: {e}")
            return None
    
    def encode_query(self, query: str) -> Optional[List[float]]:
        """
        Encode a single query and return as list.
        
        Args:
            query: Search query.
        
        Returns:
            List of floats, or None if failed.
        """
        result = self.encode(query)
        if result is not None:
            return result[0].tolist()
        return None
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self.model is not None:
            return self.model.get_sentence_embedding_dimension()
        return EMBEDDING_DIM
    
    def is_available(self) -> bool:
        """Check if model is available."""
        return self.model is not None


# =============================================================================
# Convenience Functions
# =============================================================================

def get_embedding_model() -> EmbeddingModel:
    """Get the singleton embedding model instance."""
    return EmbeddingModel()


def encode_texts(texts: Union[str, List[str]]) -> Optional[np.ndarray]:
    """Encode texts using the default embedding model."""
    return get_embedding_model().encode(texts)


def encode_query(query: str) -> Optional[List[float]]:
    """Encode a query using the default embedding model."""
    return get_embedding_model().encode_query(query)


__all__ = [
    "TORCH_AVAILABLE",
    "SENTENCE_TRANSFORMERS_AVAILABLE",
    "DEFAULT_MODEL_NAME",
    "FALLBACK_MODEL_NAME",
    "EMBEDDING_DIM",
    "get_best_device",
    "EmbeddingModel",
    "get_embedding_model",
    "encode_texts",
    "encode_query",
]
