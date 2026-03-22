#!/usr/bin/python3
"""
CHANGELOG: fs/files.py FileSystem

"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import configparser
from lib.di.Container  import Container

try:
    import yaml
except ImportError:
    yaml = None

try:
    import toml
except ImportError:
    toml = None

"""
File and Directory Management Module

Author: Christopher J. McIntosh
Date-Modified: 2024-06-10
                                                                                                                                                                                                                                                                 

Description:
This module provides the FileSystem class for managing file and directory operations,
including mapping directories, resolving files, loading content, and handling JSON files.

Directory Mapping

"""

class AppException(Exception):
    pass




class FileSystem:
    def __init__(self, directories: Optional[Union[List[str], List[Path], Dict[str, str], Dict[str, Path]]] = None, c:Container = None) -> None:
        self._mapped_directories: Dict[str, Path] = {}
        self._log = c.make("logger")
        #self._log.info("Filesytem initilaized with the logger")
        self._default_extension: str = "php"
        self._default_html_extension: str = "html"
        self._file_cache: Dict[str, str] = {}
        #print(c) WE GOT HE CONTAINER!!!!!!!
        # Initialize with directories if provided
        if directories:
            self._init_directories(directories)
    
    def _init_directories(self, directories: Union[List[str], List[Path], Dict[str, str], Dict[str, Path]]) -> None:
        """Initialize directories from various input formats"""
        if isinstance(directories, dict):
            # Format: {"name": "path", "views": "/app/views"}
            for name, path in directories.items():
                self.map_directory(name, path)
        elif isinstance(directories, list):
            # Format: ["/app/views", "/app/public"] or list of Path objects
            for i, directory in enumerate(directories):
                name = f"dir_{i}"  # Generate a name
                self.map_directory(name, directory)
    
    # ---------- Directory Mapping ----------

    def map_directory(self, name: str, directory: str | Path) -> FileSystem:
        path = Path(directory).resolve()

        if not path.is_dir():
            # Try relative to current directory or base path
            alt_path = Path.cwd() / directory
            if alt_path.is_dir():
                path = alt_path
            else:
                # Create directory if it doesn't exist?
                # path.mkdir(parents=True, exist_ok=True)
                raise AppException(f"Directory not found: {directory}")

        self._mapped_directories[name] = path
        return self


    def __str__(self) -> str :
        return f"FileSystem(mapped_directories={self._mapped_directories})"
        
        
    #change to look for a namespace from mapped dirs, if it does not find the 
    #given name, then assume its a path to a dir and return
    #that path as a Path object
    def get_directory(self, name: str) -> Optional[Path]:
        return self._mapped_directories.get(name)
    #no param return mapped dirs, param is a path to a dir like above
    def get_directories(self) -> Dict[str, Path]:
        return dict(self._mapped_directories)

    # ---------- File Resolution ----------

    def find_file(
        self,
        name: str,
        directory: Optional[str] = None,
        extension: Optional[str] = None
    ) -> Optional[Path]:

        path = Path(name)

        # 1. Absolute path
        if path.is_absolute() and path.is_file():
            return path

        normalized = Path(str(name).strip("/"))
        ext = extension or self._default_extension

        if ext and normalized.suffix == "":
            normalized = normalized.with_suffix(f".{ext.lstrip('.')}")

        parts = normalized.parts

        # 2. Subdirectory-aware search
        if len(parts) > 1:
            subdir, remainder = parts[0], Path(*parts[1:])

            if directory and directory == subdir:
                base = self._mapped_directories.get(directory)
                if base:
                    candidate = base / remainder
                    if candidate.is_file():
                        return candidate

            elif directory is None:
                for base in self._mapped_directories.values():
                    candidate = base / normalized
                    if candidate.is_file():
                        return candidate

        # 3. Flat search
        bases: List[Path] = []

        if directory:
            base = self._mapped_directories.get(directory)
            if base:
                bases.append(base)
        else:
            bases.extend(self._mapped_directories.values())

        for base in bases:
            candidate = base / normalized
            if candidate.is_file():
                return candidate

        return None

    # ---------- Directory Scanning ----------
    
    def find_files_by_extension(
        self,
        extensions: List[str],
        directory: Optional[str] = None
    ) -> List[Path]:

        bases: List[Path] = []

        if directory:
            base = self._mapped_directories.get(directory, Path(directory))
            if base.is_dir():
                bases.append(base)
        else:
            bases.extend(self._mapped_directories.values())

        found: List[Path] = []

        for base in bases:
            for path in base.rglob("*"):
                if path.is_file() and path.suffix.lstrip(".") in extensions:
                    found.append(path)

        return list(dict.fromkeys(found))  # preserve order, remove duplicates

    # ---------- File Loading ----------

    def load_file(self, path: str, use_cache: bool = True) -> str:
        if use_cache and path in self._file_cache:
            return self._file_cache[path]

        resolved = Path(path)

        if not resolved.is_file():
            found = self.find_file(path)
            if not found:
                raise AppException(f"File not found: {path}")
            resolved = found

        try:
            content = resolved.read_text()
        except Exception as e:
            raise AppException(f"Failed to read file: {resolved}") from e

        if use_cache:
            self._file_cache[str(resolved)] = content
            self._file_cache[path] = content

        return content

    # ---------- PHP-style Include / Require ----------

    def require_file(self, path: str):
        resolved = Path(path)

        if not resolved.is_file():
            found = self.find_file(path, extension="php")
            if not found:
                raise AppException(f"File not found: {path}")
            resolved = found

        # Python equivalent: execute file
        namespace = {}
        exec(resolved.read_text(), namespace)
        return namespace

    def include_file(self, path: str):
        return self.require_file(path)

    # ---------- JSON ----------

    def parse_json_file(self, path: str) -> dict:
        resolved = Path(path)

        if not resolved.is_file():
            raise AppException(f"File not found: {path}")

        try:
            return json.loads(resolved.read_text())
        except json.JSONDecodeError as e:
            raise AppException(f"Failed to parse JSON file: {path}") from e

    # ---------- Write ----------

    def write_file(self, path: str, content: str) -> bool:
        resolved = Path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)

        try:
            resolved.write_text(content)
            self._file_cache[str(resolved)] = content
            return True
        except Exception:
            return False

    # ---------- HTML Reader ----------
    @staticmethod
    def read_file_abs(path:str) -> str:
        resolved = Path(path)
        if not resolved.is_file():
            raise AppException(f"File not found: {path}")
        try:
            return resolved.read_text()
        except Exception as e:
            raise AppException(f"Failed to read file: {resolved}") from e
        
    def read_file(self, base_name: str) -> str:
        path = self.find_file(base_name, extension=self._default_html_extension)
        if not path:
            raise AppException(f"File not found: {base_name}")
        return path.read_text()

    # ---------- Configuration ----------

    @staticmethod
    def parse_config_file(file_path: Union[str, Path]) -> dict:
        """
        Parse a config file in any supported format.
        Supports: YAML, JSON, INI, CONF, TOML, and others.
        
        Args:
            file_path: Path to config file or directory containing config files
            
        Returns:
            Dictionary with parsed config. If directory is provided, returns
            {filename_without_ext: parsed_content, ...}
        """
        path = Path(file_path)
        
        if path.is_dir():
            # Process directory: return dict with filename keys
            result = {}
            for file in path.iterdir():
                if file.is_file():
                    try:
                        parsed = FileSystem.parse_config_file(file)
                        key = file.stem  # filename without extension
                        result[key] = parsed
                    except Exception:
                        # Skip files that fail to parse
                        continue
            return result
        
        if not path.is_file():
            raise AppException(f"Config file not found: {file_path}")
        
        content = path.read_text()
        suffix = path.suffix.lower()
        
        # JSON
        if suffix == '.json':
            try:
                return json.loads(content) or {}
            except json.JSONDecodeError as e:
                raise AppException(f"Failed to parse JSON config: {file_path}") from e
        
        # YAML
        if suffix in ['.yaml', '.yml']:
            if yaml is None:
                raise AppException(f"YAML support requires 'pyyaml' package. Install: pip install pyyaml")
            try:
                return yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise AppException(f"Failed to parse YAML config: {file_path}") from e
        
        # INI / CONF
        if suffix in ['.ini', '.conf', '.cfg', '.config']:
            try:
                config = configparser.ConfigParser()
                config.read_string(content)
                # Convert to nested dict
                result = {}
                for section in config.sections():
                    result[section] = dict(config.items(section))
                return result if result else {}
            except configparser.Error as e:
                raise AppException(f"Failed to parse INI/CONF config: {file_path}") from e
        
        # TOML
        if suffix == '.toml':
            if toml is None:
                raise AppException(f"TOML support requires 'toml' package. Install: pip install toml")
            try:
                return toml.loads(content) or {}
            except toml.TomlDecodeError as e:
                raise AppException(f"Failed to parse TOML config: {file_path}") from e
        
        # Try YAML by default for unknown extensions
        if yaml is not None:
            try:
                return yaml.safe_load(content) or {}
            except:
                pass
        
        # Try JSON as fallback
        try:
            return json.loads(content) or {}
        except:
            pass
        
        # If all fails, try INI
        try:
            config = configparser.ConfigParser()
            config.read_string(content)
            result = {}
            for section in config.sections():
                result[section] = dict(config.items(section))
            return result if result else {}
        except:
            raise AppException(f"Unable to parse config file: {file_path}. Supported formats: JSON, YAML, INI, TOML")

    def set_default_extension(self, extension: str) -> "FileSystem":
        self._default_extension = extension.lstrip(".")
        return self

    def get_default_extension(self) -> str:
        return self._default_extension

    def clear_cache(self) -> "FileSystem":
        self._file_cache.clear()
        return self

    # ---------- Duplicate Handling ----------

    def handle_duplicates(
        self,
        files: List[Path],
        strategy: str = "first"
    ) -> List[Path]:

        grouped: Dict[str, List[Path]] = {}

        for file in files:
            grouped.setdefault(file.name, []).append(file)

        result: List[Path] = []

        for paths in grouped.values():
            if len(paths) == 1:
                result.append(paths[0])
            elif strategy == "first":
                result.append(paths[0])
            elif strategy == "last":
                result.append(paths[-1])
            elif strategy == "all":
                result.extend(paths)

        return result
