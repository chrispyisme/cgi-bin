"""lib.di.Autoloader - Simplified Class Auto-Discovery and Registration

FEATURES:
- Pass paths directly to __init__: Autoloader(['app', 'lib'])
- Automatically scans, imports, and registers all classes
- Resolves by FQN (app.controllers.Home) OR simple name (Home)
- Shared registry with Container for seamless DI
- Filters out dev files, config files, hidden files automatically
- Optional FileSystem integration for advanced file operations

USAGE:
    # Basic usage
    autoloader = Autoloader(['app', 'lib'])
    
    # Get class by FQN
    cls = autoloader.get('app.controllers.Home')
    
    # Get class by simple name (searches registry)
    cls = autoloader.get('Home')
    
    # Use with Container
    container = Container()
    container.set_autoloader(autoloader)
    
    # Now Container can resolve classes
    home = container.make('Home')  # Works!
    home = container.make('app.controllers.Home')  # Also works!
    
    # With FileSystem integration
    from lib.fs.files import FileSystem
    fs = FileSystem({'app': '/usr/lib/cgi-bin/app'})
    autoloader = Autoloader(['app', 'lib'], filesystem=fs)

Changelog:
- 2026-02-09: Complete rewrite for simplicity
    - Constructor auto-scans paths
    - Dual resolution (FQN + simple name)
    - Better filtering with patterns
    - FileSystem integration ready
    - Shared registry with Container
"""

import os
import sys
import re
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any


class AutoloaderException(Exception):
    """Exception raised by Autoloader"""
    pass


class Autoloader:
    """
    Simplified autoloader that scans directories and builds a class registry.
    
    The registry contains two mappings:
    1. FQN -> class (e.g., 'app.controllers.Home' -> HomeClass)
    2. Simple name -> class (e.g., 'Home' -> HomeClass)
    
    This allows Container to resolve classes by either FQN or simple name.
    """
    
    # File patterns to exclude
    EXCLUDE_PATTERNS = [
        r'^_',       # _private.py, __pycache__
        r'^\.',      # .hidden.py
        r'^ep_',     # ep_endpoint.py
        r'^cfg_',    # cfg_config.py
        r'^test_',   # test_something.py (optional)
    ]
    
    def __init__(
        self, 
        paths: List[str] = [],
        filesystem: Optional[Any] = None,
        exclude_patterns: List[str] = [],
        auto_scan: bool = True
    ):
        """
        Initialize Autoloader and optionally auto-scan paths.
        
        Args:
            paths: List of directory paths to scan (e.g., ['app', 'lib'])
            filesystem: Optional FileSystem instance for directory operations
            exclude_patterns: Custom regex patterns to exclude files
            auto_scan: If True, automatically scan on initialization
        """
        self._registry_fqn: Dict[str, type] = {}      # FQN -> class
        self._registry_simple: Dict[str, type] = {}   # SimpleName -> class
        self._loaded_modules: Dict[str, Any] = {}     # module_name -> module
        self._paths: List[Path] = []
        self._filesystem = filesystem
        
        # Set exclude patterns
        self._exclude_patterns = exclude_patterns or self.EXCLUDE_PATTERNS
        self._compiled_patterns = [re.compile(p) for p in self._exclude_patterns]
        
        # Register paths
        if paths:
            for path in paths:
                self.add_path(path)
        
        # Auto-scan if requested
        if auto_scan and self._paths:
            self.scan()
    
    def add_path(self, path: str) -> "Autoloader":
        """Add a directory path to scan"""
        resolved_path = Path(path).resolve()
        
        if not resolved_path.is_dir():
            # Try relative to current working directory
            alt_path = Path.cwd() / path
            if alt_path.is_dir():
                resolved_path = alt_path
            else:
                raise AutoloaderException(f"Directory not found: {path}")
        
        if resolved_path not in self._paths:
            self._paths.append(resolved_path)
        
        return self
    
    def scan(self) -> "Autoloader":
        """Scan all registered paths and build the registry"""
        for path in self._paths:
            self._scan_directory(path, path)
        return self
    
    def _should_exclude(self, filename: str) -> bool:
        """Check if filename matches any exclude pattern"""
        for pattern in self._compiled_patterns:
            if pattern.match(filename):
                return True
        return False
    
    def _scan_directory(
        self, 
        directory: Path, 
        base_path: Path, 
        package_name: str = ""
    ) -> None:
        """
        Recursively scan a directory for Python files and import them.
        
        Args:
            directory: Current directory being scanned
            base_path: Root directory (for calculating module names)
            package_name: Current package name (for nested packages)
        """
        try:
            items = sorted(directory.iterdir())
        except PermissionError:
            return  # Skip directories we can't read
        
        for item in items:
            # Skip excluded files/dirs
            if self._should_exclude(item.name):
                continue
            
            if item.is_file() and item.suffix == '.py':
                # Calculate module name relative to base_path
                try:
                    rel_path = item.relative_to(base_path.parent)
                    module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')
                    
                    # Handle __init__.py files
                    if item.name == '__init__.py':
                        if rel_path.parent != Path('.'):
                            module_name = str(rel_path.parent).replace(os.sep, '.')
                        else:
                            module_name = package_name or base_path.name
                    
                except ValueError:
                    # File not under base_path, use stem
                    module_name = item.stem
                    if package_name:
                        module_name = f"{package_name}.{module_name}"
                
                # Import the module
                self._import_module(module_name, item)
            
            elif item.is_dir():
                # Determine if this is a Python package
                init_file = item / '__init__.py'
                new_package_name = package_name
                
                if init_file.exists():
                    # This is a package, calculate its name
                    try:
                        rel_path = item.relative_to(base_path)
                        new_package_name = str(rel_path).replace(os.sep, '.')
                    except ValueError:
                        if package_name:
                            new_package_name = f"{package_name}.{item.name}"
                        else:
                            new_package_name = item.name
                
                # Recursively scan subdirectory
                self._scan_directory(item, base_path, new_package_name)
    
    def _import_module(self, module_name: str, file_path: Path) -> None:
        """
        Import a module and extract classes into the registry.
        
        Args:
            module_name: Fully qualified module name (e.g., 'app.controllers.Home')
            file_path: Path to the .py file
        """
        # Skip if already imported
        if module_name in self._loaded_modules:
            return
        
        try:
            # Create module spec and load it
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            
            if not spec or not spec.loader:
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Store the loaded module
            self._loaded_modules[module_name] = module
            
            # Extract all classes from the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Only register classes defined in this module (not imported ones)
                if obj.__module__ == module_name:
                    fqn = f"{module_name}.{name}"
                    
                    # Register by FQN
                    self._registry_fqn[fqn] = obj
                    
                    # Register by simple name (last one wins if duplicates)
                    self._registry_simple[name] = obj
        
        except Exception as e:
            # Log error but continue scanning
            # You can integrate your Logger here if needed
            print(f"Warning: Failed to import {module_name} from {file_path}: {e}")
    
    def get(self, name: str) -> Optional[type]:
        """
        Get a class by FQN or simple name.
        
        Args:
            name: Either FQN ('app.controllers.Home') or simple name ('Home')
        
        Returns:
            The class if found, None otherwise
        """
        # Try FQN first (more specific)
        if name in self._registry_fqn:
            return self._registry_fqn[name]
        
        # Try simple name
        if name in self._registry_simple:
            return self._registry_simple[name]
        
        return None
    
    def get_class(self, fqn: str) -> Optional[type]:
        """Alias for get() - for backwards compatibility"""
        return self.get(fqn)
    
    def has(self, name: str) -> bool:
        """Check if a class is registered"""
        return name in self._registry_fqn or name in self._registry_simple
    
    def get_registry(self) -> Dict[str, type]:
        """Get the complete FQN registry"""
        return dict(self._registry_fqn)
    
    def get_simple_registry(self) -> Dict[str, type]:
        """Get the simple name registry"""
        return dict(self._registry_simple)
    
    def list_classes(self, simple: bool = False) -> List[str]:
        """
        List all registered class names.
        
        Args:
            simple: If True, return simple names; if False, return FQNs
        
        Returns:
            Sorted list of class names
        """
        if simple:
            return sorted(self._registry_simple.keys())
        else:
            return sorted(self._registry_fqn.keys())
    
    def list_modules(self) -> List[str]:
        """List all loaded module names"""
        return sorted(self._loaded_modules.keys())
    
    def get_module(self, module_name: str) -> Optional[Any]:
        """Get a loaded module by name"""
        return self._loaded_modules.get(module_name)
    
    def clear(self) -> "Autoloader":
        """Clear all registries and loaded modules"""
        self._registry_fqn.clear()
        self._registry_simple.clear()
        self._loaded_modules.clear()
        return self
    
    def rescan(self) -> "Autoloader":
        """Clear and re-scan all paths"""
        self.clear()
        return self.scan()
    
    def stats(self) -> Dict[str, int]:
        """Get statistics about the autoloader"""
        return {
            'total_classes': len(self._registry_fqn),
            'unique_simple_names': len(self._registry_simple),
            'loaded_modules': len(self._loaded_modules),
            'paths': len(self._paths),
        }
    
    def __repr__(self) -> str:
        stats = self.stats()
        return (
            f"Autoloader("
            f"classes={stats['total_classes']}, "
            f"modules={stats['loaded_modules']}, "
            f"paths={stats['paths']})"
        )