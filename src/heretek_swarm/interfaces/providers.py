"""Abstract interfaces for LLM and embedding providers.

This module defines the contracts that provider implementations must follow,
enabling dependency inversion and breaking circular import dependencies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers.
    
    All LLM provider implementations should inherit from this interface
    to ensure consistent API across different backends.
    """
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> Any:
        """Generate a completion from a prompt.
        
        Args:
            prompt: The prompt to complete
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The completion response (format depends on provider)
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Any:
        """Generate a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The chat completion response
        """
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration.
        
        Args:
            config: Provider configuration dictionary
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up provider resources."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name identifier."""
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        pass


class EmbeddingProviderInterface(ABC):
    """Abstract interface for embedding providers.
    
    All embedding provider implementations should inherit from this interface
    to ensure consistent API across different backends.
    """
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding lists
        """
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration.
        
        Args:
            config: Provider configuration dictionary
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up provider resources."""
        pass
    
    @property
    @abstractmethod
    def embedding_dimensions(self) -> int:
        """Return the dimensionality of embeddings."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name identifier."""
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Return whether the provider is initialized."""
        pass