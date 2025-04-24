"""
Interfaces for dependency injection in the Kubernetes AI Operations Agent.

This module defines abstract interfaces that components should implement
to allow proper dependency injection and decoupling between components.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, TypeVar, Generic


T = TypeVar('T')


class MCPServerProvider(ABC):
    """Interface for components that provide MCP server instances."""
    
    @abstractmethod
    async def __aenter__(self) -> 'MCPServerProvider':
        """Initialize the MCP server provider."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up the MCP server provider."""
        pass
    
    @abstractmethod
    def get_servers(self) -> List[Any]:
        """Get all available MCP servers."""
        pass
    
    @abstractmethod
    def get_server(self, name: str) -> Any:
        """Get a specific MCP server by name."""
        pass


class SessionStorage(Generic[T], ABC):
    """Interface for session storage mechanisms."""
    
    @abstractmethod
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get a value from the session storage."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: T) -> None:
        """Set a value in the session storage."""
        pass


class OpenAIClientFactory(ABC):
    """Interface for creating OpenAI clients."""
    
    @abstractmethod
    def create_client(self) -> Any:
        """Create and configure an OpenAI client."""
        pass

    @abstractmethod
    def configure_defaults(self) -> None:
        """Configure default settings for OpenAI client."""
        pass