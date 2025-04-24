"""
Chainlit Session Storage Implementation.

Provides a SessionStorage implementation that uses Chainlit's user_session.
"""

from typing import Any, Optional, TypeVar
from interfaces import SessionStorage

T = TypeVar('T')


class ChainlitSessionStorage(SessionStorage[T]):
    """
    Implementation of SessionStorage using Chainlit's user_session.
    """
    
    def __init__(self, user_session: Any):
        """
        Initialize with a Chainlit user_session object.
        
        Args:
            user_session: Chainlit user_session object
        """
        self.user_session = user_session
        
    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get a value from the session storage.
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The stored value or the default
        """
        return self.user_session.get(key, default)
        
    def set(self, key: str, value: T) -> None:
        """
        Set a value in the session storage.
        
        Args:
            key: The key to set
            value: The value to store
        """
        self.user_session.set(key, value)