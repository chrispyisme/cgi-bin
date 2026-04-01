import os
from urllib.parse import parse_qs
from lib.logging.Logger import Logger
from typing import Dict, List, Any, Optional
import re


class Request:
    def __init__(self, environ: dict = {}) -> None:
        # Don't update os.environ directly - that's dangerous!
        # Instead, use a copy of the environment
        self._environ = dict(os.environ)
        
        # Update with any provided environment variables (ensuring they're strings)
        if environ:
            for key, value in environ.items():
                # Convert everything to strings for CGI compatibility
                self._environ[key] = str(value) if value is not None else ''
        
        self._method = self._environ.get("REQUEST_METHOD", "GET")
        raw_uri = self._environ.get("REQUEST_URI", "/")
        
        # Remove leading /cgi-bin if present and normalize to start with '/'
        regBase = r"\/cgi-bin"
        uri = re.sub(regBase, "", raw_uri, count=1)
        uri = uri if uri.startswith("/") else f"/{uri}"
        self._uri: str = uri

        self._query_params: dict[str, str] = self._parse_query(
            self._environ.get("QUERY_STRING", "")
        )

        self._path_params: dict[str, str] = {}
        self._params: dict[str, str] = {}

        self._body: str = self._read_body(self._environ)
        self._headers: dict[str, str] = self._extract_headers(self._environ)

    # ---------- Internals ----------

    def _parse_query(self, query: str) -> dict[str, str]:
        parsed = parse_qs(query, keep_blank_values=True)
        return {k: v[0] for k, v in parsed.items()}

    def _read_body(self, environ: dict) -> str:
        # In CGI, the body comes from stdin
        import sys
        try:
            # Try to read from stdin
            if not sys.stdin.isatty():  # If stdin is not a terminal
                return sys.stdin.read()
        except Exception:
            pass
        return ""

    def _extract_headers(self, environ: dict) -> dict[str, str]:
        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                headers[key[5:].replace("_", "-").lower()] = value
        return headers

    # ---------- Routing API ----------

    def set_path_params(self, params: dict[str, str]) -> None:
        self._path_params = params
        self._rebuild_params()

    def set_query_params(self, params: dict[str, str]) -> None:
        self._query_params = params
        self._rebuild_params()

    def _rebuild_params(self) -> None:
        # path params override query params
        self._params = {**self._query_params, **self._path_params}

    # ---------- Accessors ----------

    def get_params(self) -> dict[str, str]:
        return self._params

    def get_param(self, key: str) -> str | None:
        return self._params.get(key)

    def get_query_params(self) -> dict[str, str]:
        return self._query_params

    def get_path_params(self) -> dict[str, str]:
        return self._path_params

    def get_method(self) -> str:
        return self._method

    def get_uri(self) -> str:
        return self._uri

    def get_body(self) -> str:
        return self._body

    def get_headers(self) -> dict[str, str]:
        return self._headers

    def get_header(self, name: str) -> str | None:
        return self._headers.get(name.lower())

    def get_sub_routes(self) -> list[str]:
        parts = self._uri.strip("/").split("/")
        return parts[1:] if len(parts) > 1 else []