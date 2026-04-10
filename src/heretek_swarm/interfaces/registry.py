"""Provider registry interface for lazy resolution.

This module provides the abstract registry interface that enables
lazy loading of providers and breaks circular dependencies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from .providers import LLMProviderInterface, EmbeddingProviderInterface


class ProviderRegistryInterface(ABC):
    """Abstract registry for provider management.
    
    This interface defines how providers are registered and retrieved,
    enabling loose coupling between the API layer and provider implementations.
    """
    
    @abstractmethod
    def get_llm_provider(self, name: str) -> Optional[LLMProviderInterface]:
        """Get an LLM provider by name.
        
        Args:
            name: Provider name identifier
            
        Returns:
            LLM provider instance or None if not found
        """
        pass
    
    @abstractmethod
    def get_embedding_provider(self, name: str) -> Optional[EmbeddingProviderInterface]:
        """Get an embedding provider by name.
        
        Args:
            name: Provider name identifier
            
        Returns:
            Embedding provider instance or None if not found
        """
        pass
    
    @abstractmethod
    def list_llm_providers(self) -> List[str]:
        """List available LLM provider names.
        
        Returns:
            List of available LLM provider identifiers
        """
        pass
    
    @abstractmethod
    def list_embedding_providers(self) -> List[str]:
        """List available embedding provider names.
        
        Returns:
            List of available embedding provider identifiers
        """
        pass
    
    @abstractmethod
    def register_llm_provider(self, name: str, provider_class: Type[LLMProviderInterface]) -> None:
        """Register an LLM provider class.
        
        Args:
            name: Provider identifier
            provider_class: Provider class implementing LLMProviderInterface
        """
        pass
    
    @abstractmethod
    def register_embedding_provider(self, name: str, provider_class: Type[EmbeddingProviderInterface]) -> None:
        """Register an embedding provider class.
        
        Args:
            name: Provider identifier
            provider_class: Provider class implementing EmbeddingProviderInterface
        """
        pass
    
    @abstractmethod
    def get_provider_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get provider information.
        
        Args:
            name: Provider name
            
        Returns:
            Provider info dict or None if not found
        """
        pass