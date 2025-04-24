"""
Session Manager for Kubernetes Operations Agent.

Provides a ChainlitSessionManager class that handles session-specific data,
with application-level agent lifecycle.
"""

from typing import Any, Dict, List, TypeVar
from interfaces import SessionStorage

T = TypeVar('T')


class ChainlitSessionManager:
    """
    Manages user session resources and state, but not the agent lifecycle
    which is managed at the application level.
    """
    
    def __init__(self, session_storage: SessionStorage[Any]):
        """
        Initialize ChainlitSessionManager with session storage.
        Creates empty collections for session-specific data.
        
        Args:
            session_storage: Implementation of SessionStorage interface
        """
        self._session_storage = session_storage
        
        # Initialize empty collections in storage for session-specific data
        self._session_storage.set("message_history", [])
        self._session_storage.set("tool_steps", {})
    
    def get_message_history(self) -> List[Dict[str, str]]:
        """
        Get the message history, guaranteed not to be None.
        
        Returns:
            The message history list
        """
        return self._session_storage.get("message_history") or []
    
    def get_tool_steps(self) -> Dict[str, Any]:
        """
        Get the tool steps dictionary, guaranteed not to be None.
        
        Returns:
            The tool steps dictionary
        """
        return self._session_storage.get("tool_steps") or {}
    
    def save_message_history(self, message_history: List[Dict[str, str]]) -> None:
        """
        Save the updated message history to the session.
        
        Args:
            message_history: The message history to save
        """
        self._session_storage.set("message_history", message_history)
    
    def save_tool_steps(self, tool_steps: Dict[str, Any]) -> None:
        """
        Save the updated tool steps to the session.
        
        Args:
            tool_steps: The tool steps to save
        """
        self._session_storage.set("tool_steps", tool_steps)
    
    async def cleanup(self) -> None:
        """
        Clean up session-specific resources.
        Since agent and MCP servers are managed at application level,
        we only need to clear session data.
        """
        # Clear session-specific resources
        self._session_storage.set("message_history", [])
        self._session_storage.set("tool_steps", {})