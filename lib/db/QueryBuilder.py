import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any, Union, List
from lib.logging.Logger import Logger

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
    
    def select(self, columns: Union[List[str], str] = []) -> "QueryBuilder":
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
            'gt': f"{col} > %s",
            'lt': f"{col} < %s",
            'gte': f"{col} >= %s",
            'gteq': f"{col} >= %s",
            'lte': f"{col} <= %s",
            'lteq': f"{col} <= %s",
            'like': f"{col} LIKE %s",
            'has': f"{col} LIKE %s",
            'starts': f"{col} LIKE %s",
            'ends': f"{col} LIKE %s",
            'regex': f"{col} REGEXP %s",
            'in': f"{col} IN ({','.join(['%s'] * len(value))})",
            'not_in': f"{col} NOT IN ({','.join(['%s'] * len(value))})",
            'is_null': f"{col} IS NULL",
            'is_not_null': f"{col} IS NOT NULL",
        }
        
        if operator in operators:
            condition = operators[operator]
            if operator == 'starts':
                self.where_params[-1] = f"{value}%"
            elif operator == 'ends':
                self.where_params[-1] = f"%{value}"
            elif operator == 'has':
                self.where_params[-1] = f"%{value}%"
            return condition
        
        # Default to equals if operator not found
        self.where_params.pop()
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
