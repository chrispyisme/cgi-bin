"""app.models.model - AbstractModel with State Management

Provides attribute storage, state stack management, and datasource integration.

Origin:
    Converted from PHP HTTPStack v2 Core/Model AbstractModel.
    
Changelog:
    - 2026-01-30: Converted from PHP. Implements AbstractModel with state management.

Usage:
    from app.models.model import AbstractModel
    from app.datasources.json_datasource import JsonDatasource
    
    class User(AbstractModel):
        def get_name(self):
            return self.get('name')
    
    ds = JsonDatasource('/tmp/users.json')
    user = User(ds, {'id': 1, 'name': 'Alice'})
    user.set('name', 'Alice Smith')  # Auto-pushes state
    user.push()  # Save to datasource
    user.pull()  # Refresh from datasource
    user.pop_state()  # Undo last mutation

Key Features:
    - Automatic state snapshots on mutations (set, remove, set_all, clear)
    - Named state restore points with push_state/pop_state
    - Datasource integration for load (pull) and save (push)
    - Extends BaseModel for full attribute management
"""

from typing import Any, Dict, Optional
from .base import BaseModel
from .contracts import AttributeState
from lib.data.source.contracts import CrudInterface


class AbstractModel(BaseModel, AttributeState):
    """Abstract model with state management and datasource integration.
    
    Automatically saves state snapshots when attributes are mutated.
    Integrates with any CrudInterface datasource for persistence.
    
    State Management:
        - Auto-push on: set(), remove(), set_all(), clear()
        - Manual push_state(name) for named snapshots
        - pop_state() to undo and restore last mutation
        - get_state(name) to retrieve named state snapshot
    
    Datasource Integration:
        - pull() loads all data from datasource
        - push() saves all data to datasource
    """
    
    def __init__(self, datasource: CrudInterface, data: Optional[Dict[str, Any]] = None):
        """
        Initialize with a datasource and optional data.
        The datasource is a CrudInterface implementation that handles persistence.
        """
        # Initialize state management BEFORE calling super().__init__
        # because super().__init__ may trigger set() which uses _states
        self._states: Dict[str, Dict[str, Any]] = {}  # restore_point -> snapshot
        
        # Read initial data from datasource
        initial_data = datasource.read() if data is None else data
        super().__init__(initial_data)
        
        self.datasource = datasource
    
    def push_state(self, restore_point: str) -> Any:
        """Push current state onto the stack."""
        self._states[restore_point] = self.get_all()
        return f"State pushed: {restore_point}"
    
    def pop_state(self) -> Dict[str, Any]:
        """Pop the last state and restore it."""
        if not self._states:
            return {}
        
        last_key = list(self._states.keys())[-1]
        last_state = self._states[last_key]
        del self._states[last_key]
        
        self.set_all(last_state)
        return last_state
    
    def get_state(self, restore_point: str) -> Optional[Dict[str, Any]]:
        """Get a specific state by restore point."""
        return self._states.get(restore_point)
    
    # Override mutating methods to push state
    def set(self, key: str, value: Any) -> None:
        """Set attribute and push state."""
        self.push_state(f"before_set_{key}")
        super().set(key, value)
    
    def remove(self, key: str) -> None:
        """Remove attribute and push state."""
        self.push_state(f"before_remove_{key}")
        super().remove(key)
    
    def set_all(self, data: Dict[str, Any]) -> None:
        """Set all attributes and push state."""
        self.push_state("before_set_all")
        super().set_all(data)
    
    def clear(self) -> None:
        """Clear all attributes and push state."""
        self.push_state("before_clear")
        super().clear()
    
    # Datasource integration
    def pull(self) -> Dict[str, Any]:
        """Pull data from the datasource."""
        data = self.datasource.pull()
        self.set_all(data)
        return data
    
    def push(self) -> bool:
        """Push model data to the datasource."""
        self.datasource.push(self.get_all())
        return True
