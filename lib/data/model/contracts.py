"""app.models.contracts - Attribute and State Management Contracts

Defines ABC interfaces for managing model attributes and state stacks.

Origin:
    Converted from PHP HTTPStack v2 Core/Model contracts.
    
Changelog:
    - 2026-01-30: Converted from PHP. Defines contracts for attribute and state management.

Usage:
    from app.models.contracts import Attributes, AttributeState
    
    class MyModel(Attributes, AttributeState):
        # Implement get, set, has, remove, clear, count, set_all, get_all
        # Implement push_state, pop_state, get_state
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Attributes(ABC):
    """Contract for managing model attributes (get/set/has/remove/clear).
    
    Implementations must provide simple key-value attribute storage and retrieval.
    """
    
    @abstractmethod
    def get(self, key: str) -> Any:
        """Get the value of a key."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set the value of a key."""
        pass
    
    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a key exists."""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all attributes."""
        pass
    
    @abstractmethod
    def remove(self, key: str) -> None:
        """Remove a key."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all attributes."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get count of attributes."""
        pass
    
    @abstractmethod
    def set_all(self, data: Dict[str, Any]) -> None:
        """Set multiple attributes at once."""
        pass


class AttributeState(ABC):
    """Contract for managing attribute state stack (push/pop/get)."""
    
    @abstractmethod
    def push_state(self, restore_point: str) -> Any:
        """Push current state onto the stack with a named restore point."""
        pass
    
    @abstractmethod
    def pop_state(self) -> Dict[str, Any]:
        """Pop the last state from the stack."""
        pass
    
    @abstractmethod
    def get_state(self, restore_point: str) -> Optional[Dict[str, Any]]:
        """Get a specific state by restore point name."""
        pass
