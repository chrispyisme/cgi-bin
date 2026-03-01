"""app.datasources.contracts - CRUD and Datasource Interfaces

Defines ABC contracts for data persistence operations.

Origin:
    Converted from PHP HTTPStack v2 Core/Datasource contracts.
    
Changelog:
    - 2026-01-30: Converted from PHP. Defines CRUD and Datasource contracts.
    - 2026-01-30: Updated CRUD signatures to use unified query format:
        * update(query: Dict) instead of update(where, payload)
        * delete(query: Dict) instead of delete(where, params)
        * Format: {"collection": [WHERE_conditions + UPDATE_values]}

Usage:
    from app.datasources.contracts import CrudInterface, DatasourceInterface
    from app.datasources.abstract import AbstractDatasource
    
    class CustomDatasource(AbstractDatasource):
        def create(self, payload, params=None):
            # Implement
        
        def read(self, query=None, filter_=None):
            # Implement
        
        def update(self, where, payload):
            # Implement
        
        def delete(self, where, params=None):
            # Implement
        
        def push(self, attributes):
            # Save all data
        
        def pull(self):
            # Load all data
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CrudInterface(ABC):
    """Contract for CRUD operations.
    
    Implementations provide Create, Read, Update, Delete operations
    on records in a specific storage backend (file, database, API, etc).
    """
    
    @abstractmethod
    def create(self, payload: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new record."""
        pass
    
    @abstractmethod
    def read(self, query: Optional[Dict[str, Any]] = None, filter: Optional[Dict[str, Any]] = None) -> Any:
        """Read records matching query."""
        pass
    
    @abstractmethod
    def update(self, payload: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> bool:
        """Update records using unified format: {"collection": {WHERE + updates}}."""
        pass
    
    @abstractmethod
    def delete(self, query: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> bool:
        """Delete records using unified format: {"collection": {WHERE}}."""
        pass


class DatasourceInterface(ABC):
    """Contract for push/pull operations."""
    
    @abstractmethod
    def push(self, attributes: Dict[str, Any]) -> None:
        """Save data to the datasource."""
        pass
    
    @abstractmethod
    def pull(self) -> Dict[str, Any]:
        """Load data from the datasource."""
        pass
    
    @abstractmethod
    def set_read_only(self, read_only: bool) -> None:
        """Set read-only mode."""
        pass
    
    @abstractmethod
    def is_read_only(self) -> bool:
        """Check if datasource is read-only."""
        pass
