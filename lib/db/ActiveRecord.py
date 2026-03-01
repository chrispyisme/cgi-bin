import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any
from lib.logging.Logger import Logger
from lib.db.Database import Database
from lib.db.QueryBuilder import QueryBuilder
from lib.db.ActiveRecordSet import ActiveRecordSet

class ActiveRecord:
    """Generic Active Record for database tables"""
    
    def __init__(self, db: Database, table: str, primary_key: str = 'id'):
        self.db = db
        self.table = table
        self.primary_key = primary_key
    
    # ========== READ Operations ==========
    
    def read(self, criteria: Optional[Dict[str, Any]] = None) -> ActiveRecordSet:
        """
        Read records with flexible criteria
        
        Examples:
            read()  # All records
            read({"userEmail": "test@example.com"})  # Simple match
            read({"orderDate": {"starts": "2026-01-"}})  # Complex operators
            read({"orderID", "orderShippingPrice"})  # Specific columns
        """
        builder = QueryBuilder(self.table)
        
        if criteria is None:
            # No criteria, return all
            builder.select()
        elif isinstance(criteria, dict):
            columns_to_select = []
            where_criteria = {}
            
            for key, value in criteria.items():
                if isinstance(value, dict):
                    # This is a WHERE condition with operators
                    where_criteria[key] = value
                elif isinstance(value, str) or isinstance(value, (int, float)):
                    # This is a simple WHERE condition
                    where_criteria[key] = value
                else:
                    # Might be a column list
                    columns_to_select.append(key)
            
            # If we have column names, select them
            if columns_to_select:
                builder.select(columns_to_select)
            else:
                builder.select()
            
            # Apply WHERE conditions
            if where_criteria:
                builder.where(where_criteria)
        
        query, params = builder.build_select()
        results = self.db.fetch_all(query, params)
        return ActiveRecordSet(results)
    
    def read_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        """Read single record by primary key"""
        builder = QueryBuilder(self.table)
        builder.select().where({self.primary_key: id_value})
        query, params = builder.build_select()
        return self.db.fetch_one(query, params)
    
    def read_one(self, criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Read single record matching criteria"""
        builder = QueryBuilder(self.table)
        builder.select().where(criteria).limit(1)
        query, params = builder.build_select()
        return self.db.fetch_one(query, params)
    
    # ========== CREATE Operations ==========
    
    def create(self, data: Dict[str, Any]) -> int:
        """Insert a new record and return affected rows"""
        builder = QueryBuilder(self.table)
        query, params = builder.build_insert(data)
        return self.db.execute_query(query, params)
    
    # ========== UPDATE Operations ==========
    
    def update(self, data: Dict[str, Any], criteria: Dict[str, Any]) -> int:
        """Update records matching criteria"""
        builder = QueryBuilder(self.table)
        builder.where(criteria)
        query, params = builder.build_update(data)
        return self.db.execute_query(query, params)
    
    def update_by_id(self, id_value: Any, data: Dict[str, Any]) -> int:
        """Update record by primary key"""
        return self.update(data, {self.primary_key: id_value})
    
    # ========== DELETE Operations ==========
    
    def delete(self, criteria: Dict[str, Any]) -> int:
        """Delete records matching criteria"""
        builder = QueryBuilder(self.table)
        builder.where(criteria)
        query, params = builder.build_delete()
        return self.db.execute_query(query, params)
    
    def delete_by_id(self, id_value: Any) -> int:
        """Delete record by primary key"""
        return self.delete({self.primary_key: id_value})
    
    # ========== AGGREGATE Operations ==========
    
    def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """Count records"""
        builder = QueryBuilder(self.table)
        builder.select("COUNT(*) as count")
        if criteria:
            builder.where(criteria)
        query, params = builder.build_select()
        result = self.db.fetch_one(query, params)
        return result['count'] if result else 0
    
    def exists(self, criteria: Dict[str, Any]) -> bool:
        """Check if record exists"""
        return self.count(criteria) > 0