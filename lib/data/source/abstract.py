"""app.datasources.abstract - Base Datasource Class

Provides common functionality for all datasource implementations.

Origin:
    Converted from PHP HTTPStack v2 Core/Datasource AbstractDatasource.
    
Changelog:
    - 2026-01-30: Converted from PHP. Abstract datasource with caching and read-only mode.

Usage:
    from app.datasources.abstract import AbstractDatasource
    
    class MyCustomDatasource(AbstractDatasource):
        def __init__(self, config, read_only=True):
            super().__init__(read_only)
            self.config = config
            self.data_cache = {}
        
        def create(self, payload, params=None):
            if self.is_read_only():
                raise Exception("Read-only datasource")
            # Implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .contracts import CrudInterface, DatasourceInterface
import re  


class AbstractDatasource(CrudInterface, DatasourceInterface, ABC):
    """Abstract base for all datasources.
    
    Provides common features:
        - Read-only mode enforcement (raises on writes)
        - Data caching dict for temporary storage
        - Standardized interface for CRUD + push/pull
    
    All concrete datasource implementations should extend this class
    and implement the abstract CRUD methods.
    """
    
    def __init__(self, read_only: bool = True):
        """Initialize with read-only mode."""
        self.read_only = read_only
        self.data_cache: Dict[str, Any] = {}
    
    def set_read_only(self, read_only: bool) -> None:
        """Set read-only mode."""
        self.read_only = read_only
    
    def is_read_only(self) -> bool:
        """Check if datasource is read-only."""
        return self.read_only
    
    def disconnect(self) -> bool:
        """Close connection and clear cache."""
        self.data_cache.clear()
        return True

    def _matches_item(self, item: Dict[str, Any], specs: Dict[str, Any]) -> bool:
        """Return True if item matches specs.

        Specs may contain operator dicts per column, e.g.
        {"name": {"starts": "chr"}, "age": {"gt": 18}}
        Supported operators: eq, gt, lt, gte, lte, has, starts, ends, regexp, in
        """
        for col, cond in specs.items():
            value = item.get(col)

            if isinstance(cond, dict):
                for op, v in cond.items():
                    # normalize operator
                    lop = op.lower()
                    if lop in ("eq", "="):
                        if value != v:
                            return False
                    elif lop in ("gt", ">"):
                        try:
                            if not (value is not None and float(value) > float(v)):
                                return False
                        except Exception:
                            return False
                    elif lop in ("lt", "<"):
                        try:
                            if not (value is not None and float(value) < float(v)):
                                return False
                        except Exception:
                            return False
                    elif lop in ("gte", "gteq", ">="):
                        try:
                            if not (value is not None and float(value) >= float(v)):
                                return False
                        except Exception:
                            return False
                    elif lop in ("lte", "lteq", "<="):
                        try:
                            if not (value is not None and float(value) <= float(v)):
                                return False
                        except Exception:
                            return False
                    elif lop == "has":
                        if value is None:
                            return False
                        if isinstance(value, str):
                            if str(v) not in value:
                                return False
                        elif isinstance(value, (list, tuple, set)):
                            if v not in value:
                                return False
                        elif isinstance(value, dict):
                            # check keys or values
                            if v not in value and v not in value.values():
                                return False
                        else:
                            return False
                    elif lop == "starts":
                        if not (isinstance(value, str) and str(value).startswith(str(v))):
                            return False
                    elif lop == "ends":
                        if not (isinstance(value, str) and str(value).endswith(str(v))):
                            return False
                    elif lop in ("regexp", "regex"):
                        try:
                            if not (isinstance(value, str) and re.search(str(v), value)):
                                return False
                        except re.error:
                            return False
                    elif lop == "in":
                        if not (value in v if not isinstance(v, str) else value == v):
                            return False
                    else:
                        # unknown operator -> fail safe compare
                        if value != v:
                            return False
            else:
                # simple equality
                if value != cond:
                    return False

        return True
    
    @abstractmethod
    def create(self, payload: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new record."""
        pass
    
    @abstractmethod
    def read(self, query: Optional[Dict[str, Any]] = None, filter: Optional[Dict[str, Any]] = None) -> Any:
        """Read records."""
        pass
    
    @abstractmethod
    def update(self, payload:Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> bool:
        """Update records."""
        pass
    
    @abstractmethod
    def delete(self, query: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> bool:
        """Delete records."""
        pass
    
    @abstractmethod
    def push(self, attributes: Dict[str, Any]) -> None:
        """Save data (implemented by subclasses)."""
        pass
    
    @abstractmethod
    def pull(self) -> Dict[str, Any]:
        """Load data (implemented by subclasses)."""
        pass
