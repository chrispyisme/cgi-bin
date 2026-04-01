"""app.models.base - BaseModel Implementation

Provides concrete attribute storage and management without state tracking.

Origin:
    Converted from PHP HTTPStack v2 Core/Model BaseModel.
    
Changelog:
    - 2026-01-30: Converted from PHP. Implements BaseModel with attribute storage.

Usage:
    from app.models.base import BaseModel
    
    # Direct usage
    model = BaseModel({'name': 'Alice', 'email': 'alice@example.com'})
    print(model.get('name'))  # 'Alice'
    model.set('email', 'newemail@example.com')
    print(model.get_all())  # {'name': 'Alice', 'email': '...'}
    
    # Or extend for custom behavior
    class UserModel(BaseModel):
        def get_email(self):
            return self.get('email') or ''
"""

from typing import Any, Dict, Optional
from .contracts import Attributes


class BaseModel(Attributes):
    """Base model with attribute storage and manipulation.
    
    Provides dict-backed attribute storage. Does NOT include state management.
    For state management (push/pop), use AbstractModel instead.
    
    Thread-safe for read operations; not thread-safe for writes.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """Initialize with optional data."""
        self._attributes: Dict[str, Any] = {}
        if data:
            self.set_all(data)
    
    def get(self, key: str) -> Any:
        """Get an attribute by key."""
        return self._attributes.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set an attribute."""
        self._attributes[key] = value
    
    def has(self, key: str) -> bool:
        """Check if an attribute exists."""
        return key in self._attributes
    
    def get_all(self) -> Dict[str, Any]:
        """Get all attributes as a dict."""
        return dict(self._attributes)
    
    def remove(self, key: str) -> None:
        """Remove an attribute."""
        if key in self._attributes:
            del self._attributes[key]
    
    def clear(self) -> None:
        """Clear all attributes."""
        self._attributes.clear()
    
    def count(self) -> int:
        """Get count of attributes."""
        return len(self._attributes)
    
    def set_all(self, data: Dict[str, Any]) -> None:
        """Set multiple attributes at once."""
        self._attributes.update(data)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._attributes})"
