import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any
from lib.logging.Logger import Logger

class Database:
    """MySQL/MariaDB Connection Manager"""
    
    def __init__(
        self,
        host: str = 'localhost',
        user: str = 'pycgi',
        password: str = 'bf6912',
        database: str = 'httpstack',
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
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
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

