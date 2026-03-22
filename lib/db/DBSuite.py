# /usr/lib/cgi-bin/base/db/Database.py

import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any
from lib.logging.Logger import Logger

class Database:
    """MySQL/MariaDB Connection Manager"""
    
    def __init__(
        self,
        host: str = 'localhost',
        user: str = 'root',
        password: str = '',
        database: str = '',
        port: int = 3306,
        autocommit: bool = True
    ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.autocommit = autocommit
        self.connection = None
        self.log = Logger(level="INFO", file="/usr/lib/cgi-bin/app/logs/app.log")
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                autocommit=self.autocommit
            )
            self.log.log(f"Database connected: {self.database}")
        except Error as e:
            self.log.log(f"Error connecting to database: {e}")
            raise
    
    def get_connection(self):
        """Get active connection"""
        if not self.connection or not self.connection.is_connected():
            self._connect()
        return self.connection
    
    def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute a query (INSERT, UPDATE, DELETE)"""
        try:
            cursor = self.get_connection().cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.get_connection().commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        except Error as e:
            self.log.log(f"Query execution error: {e}")
            raise
    
    def fetch_all(self, query: str, params: tuple = None) -> list:
        """Fetch all results"""
        try:
            cursor = self.get_connection().cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            self.log.log(f"Fetch all error: {e}")
            raise
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch single result"""
        try:
            cursor = self.get_connection().cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            self.log.log(f"Fetch one error: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.log.log("Database connection closed")


# /usr/lib/cgi-bin/base/db/QueryBuilder.py

from typing import List, Dict, Any, Optional, Union

class QueryBuilder:
    """Generic SQL Query Builder"""
    
    def __init__(self, table: str):
        self.table = table
        self.select_columns = []
        self.where_conditions = []
        self.where_params = []
        self.limit_value = None
        self.offset_value = None
        self.order_by_clause = None
    
    def select(self, columns: Union[List[str], str] = None) -> "QueryBuilder":
        """Set columns to select"""
        if columns is None:
            self.select_columns = ['*']
        elif isinstance(columns, str):
            self.select_columns = [columns]
        elif isinstance(columns, list):
            self.select_columns = columns
        return self
    
    def where(self, conditions: Dict[str, Any]) -> "QueryBuilder":
        """Add WHERE conditions with operators"""
        for column, value in conditions.items():
            if isinstance(value, dict):
                # Handle operator-based conditions
                for operator, op_value in value.items():
                    condition_str = self._build_condition(column, operator, op_value)
                    self.where_conditions.append(condition_str)
                    if operator not in ['in', 'not_in']:
                        self.where_params.append(op_value)
                    else:
                        self.where_params.extend(op_value if isinstance(op_value, list) else [op_value])
            else:
                # Simple equality
                self.where_conditions.append(f"`{column}` = %s")
                self.where_params.append(value)
        return self
    
    def _build_condition(self, column: str, operator: str, value: Any) -> str:
        """Build condition string based on operator"""
        col = f"`{column}`"
        operators = {
            'eq': f"{col} = %s",
            'ne': f"{col} != %s",
            'gt': f"{col} > %s",
            'gte': f"{col} >= %s",
            'lt': f"{col} < %s",
            'lte': f"{col} <= %s",
            'like': f"{col} LIKE %s",
            'starts': f"{col} LIKE %s",
            'ends': f"{col} LIKE %s",
            'in': f"{col} IN ({','.join(['%s'] * len(value))})",
            'not_in': f"{col} NOT IN ({','.join(['%s'] * len(value))})",
            'is_null': f"{col} IS NULL",
            'is_not_null': f"{col} IS NOT NULL",
        }
        
        if operator in operators:
            condition = operators[operator]
            if operator == 'starts':
                self.where_params[-1] = f"{value}%"
                return condition.replace("%s", "%s", 1)
            elif operator == 'ends':
                self.where_params[-1] = f"%{value}"
                return condition.replace("%s", "%s", 1)
            return condition
        
        # Default to equals if operator not found
        self.where_params.pop()  # Remove the value we added
        return f"{col} = %s"
    
    def limit(self, limit: int) -> "QueryBuilder":
        """Set LIMIT"""
        self.limit_value = limit
        return self
    
    def offset(self, offset: int) -> "QueryBuilder":
        """Set OFFSET"""
        self.offset_value = offset
        return self
    
    def order_by(self, column: str, direction: str = 'ASC') -> "QueryBuilder":
        """Set ORDER BY"""
        self.order_by_clause = f"ORDER BY `{column}` {direction.upper()}"
        return self
    
    def build_select(self) -> tuple:
        """Build SELECT query"""
        columns = ', '.join(self.select_columns) if self.select_columns else '*'
        query = f"SELECT {columns} FROM `{self.table}`"
        
        if self.where_conditions:
            where_clause = ' AND '.join(self.where_conditions)
            query += f" WHERE {where_clause}"
        
        if self.order_by_clause:
            query += f" {self.order_by_clause}"
        
        if self.limit_value:
            query += f" LIMIT {self.limit_value}"
        
        if self.offset_value:
            query += f" OFFSET {self.offset_value}"
        
        return query, tuple(self.where_params)
    
    def build_insert(self, data: Dict[str, Any]) -> tuple:
        """Build INSERT query"""
        columns = ', '.join([f"`{k}`" for k in data.keys()])
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO `{self.table}` ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())
        return query, values
    
    def build_update(self, data: Dict[str, Any]) -> tuple:
        """Build UPDATE query"""
        set_clause = ', '.join([f"`{k}` = %s" for k in data.keys()])
        query = f"UPDATE `{self.table}` SET {set_clause}"
        
        values = list(data.values())
        
        if self.where_conditions:
            where_clause = ' AND '.join(self.where_conditions)
            query += f" WHERE {where_clause}"
            values.extend(self.where_params)
        
        return query, tuple(values)
    
    def build_delete(self) -> tuple:
        """Build DELETE query"""
        query = f"DELETE FROM `{self.table}`"
        
        if self.where_conditions:
            where_clause = ' AND '.join(self.where_conditions)
            query += f" WHERE {where_clause}"
        
        return query, tuple(self.where_params)
    
    def reset(self):
        """Reset builder for reuse"""
        self.select_columns = []
        self.where_conditions = []
        self.where_params = []
        self.limit_value = None
        self.offset_value = None
        self.order_by_clause = None
        return self


# /usr/lib/cgi-bin/base/db/ActiveRecord.py

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