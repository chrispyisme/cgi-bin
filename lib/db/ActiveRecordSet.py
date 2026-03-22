
from typing import Dict, Any, Optional, List
from lib.db.Database import Database
from lib.db.QueryBuilder import QueryBuilder

class ActiveRecordSet:
    """Represents a collection of records"""
    
    def __init__(self, records: List[Dict[str, Any]]):
        self.records = records
        self._index = 0
    
    def __iter__(self):
        return iter(self.records)
    
    def __len__(self):
        return len(self.records)
    
    def __getitem__(self, index):
        return self.records[index]
    
    def all(self) -> List[Dict[str, Any]]:
        """Get all records as list of dicts"""
        return self.records
    
    def first(self) -> Optional[Dict[str, Any]]:
        """Get first record"""
        return self.records[0] if self.records else None
    
    def last(self) -> Optional[Dict[str, Any]]:
        """Get last record"""
        return self.records[-1] if self.records else None
    
    def count(self) -> int:
        """Get record count"""
        return len(self.records)
    
    def pluck(self, column: str) -> List[Any]:
        """Get single column from all records"""
        return [record.get(column) for record in self.records]
    
    def filter(self, callback) -> "ActiveRecordSet":
        """Filter records using callback"""
        filtered = [r for r in self.records if callback(r)]
        return ActiveRecordSet(filtered)
    
    def map(self, callback) -> List[Any]:
        """Map records through callback"""
        return [callback(r) for r in self.records]

