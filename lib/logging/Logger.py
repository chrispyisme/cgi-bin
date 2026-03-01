"""lib.logging.Logger - Enhanced logging utility with rich formatting"""

import os
import sys
import time
import inspect
import threading
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class Logger:
    """Enhanced logging utility with rich formatting"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red background
        'RESET': '\033[0m'
    }
    
    def __init__(self, level: str = "INFO", file: Optional[str] = None, 
                 name: Optional[str] = None, format: Optional[str] = None):
        self.level = LogLevel[level.upper()]
        self.file = Path(file) if file else None
        self.name = name or "Logger"
        self.format = format or "%(asctime)s [%(levelname)8s] %(filename)s:%(lineno)d - %(message)s"
        self._lock = threading.RLock()
        
        if self.file:
            self.file.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the caller - SIMPLIFIED FIXED VERSION"""
        try:
            # Get the current stack
            stack = inspect.stack()
            
            # Skip logger methods by finding first frame not from this module
            for frame_info in stack:
                # frame_info is a tuple: (frame, filename, lineno, function, code_context, index)
                filename = frame_info.filename
                function = frame_info.function
                
                # Skip frames from this logger class
                if "logging" in filename or "Logger" in filename or function in ['_log', 'debug', 'info', 'warning', 'error', 'critical', 'log']:
                    continue
                
                # Found the caller
                return {
                    'filename': os.path.basename(filename),
                    'lineno': frame_info.lineno,
                    'funcName': function,
                    'fullpath': filename
                }
                
        except Exception:
            pass
        
        # Fallback
        return {
            'filename': 'unknown',
            'lineno': 0,
            'funcName': 'unknown',
            'fullpath': 'unknown'
        }
    
    def _log(self, level: LogLevel, message: str, exc_info: bool = False) -> None:
        """Internal logging method"""
        if level.value < self.level.value:
            return
        
        caller_info = self._get_caller_info()
        
        # Get current time with microseconds
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Prepare log record
        record = {
            'asctime': timestamp,
            'levelname': level.name,
            'name': self.name,
            'filename': caller_info['filename'],
            'lineno': caller_info['lineno'],
            'funcName': caller_info['funcName'],
            'fullpath': caller_info['fullpath'],
            'message': str(message),
        }
        
        # Format the message
        try:
            formatted = self.format % record
        except KeyError as e:
            # If format string has invalid placeholder, use simple format
            formatted = f"{timestamp} [{level.name:8s}] {message}"
        
        # Add exception info if requested
        if exc_info:
            import traceback
            formatted += "\n" + traceback.format_exc()
        
        # Write to file and/or console
        with self._lock:
            # Write to file if specified 
            if self.file:
                try:
                    with open(self.file, 'a', encoding='utf-8') as f:
                        f.write(formatted + "\n")
                except Exception as e:
                    sys.stderr.write(f"Failed to write to log file {self.file}: {e}\n")
            
            # Also write to console (colored if terminal supports it)
            if sys.stderr.isatty() and level.name in self.COLORS:
                sys.stderr.write(f"{self.COLORS[level.name]}{formatted}{self.COLORS['RESET']}\n")
            else:
                sys.stderr.write(formatted + "\n")
    
    # Keep all the other methods the same...
    def debug(self, message: str, exc_info: bool = False) -> None:
        self._log(LogLevel.DEBUG, message, exc_info)
    
    def info(self, message: str, exc_info: bool = False) -> None:
        self._log(LogLevel.INFO, message, exc_info)
    
    def warning(self, message: str, exc_info: bool = False) -> None:
        self._log(LogLevel.WARNING, message, exc_info)
    
    def error(self, message: str, exc_info: bool = False) -> None:
        self._log(LogLevel.ERROR, message, exc_info)
    
    def critical(self, message: str, exc_info: bool = False) -> None:
        self._log(LogLevel.CRITICAL, message, exc_info)
    
    # Alias for backward compatibility
    def log(self, message: str, exc_info: bool = False) -> None:
        self.info(message, exc_info)