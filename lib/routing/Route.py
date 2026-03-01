"""lib.routing.Route - Individual Route Representation

Defines a single HTTP route with pattern matching and parameter extraction.

Pattern Matching:
    - Parameter style with regex: '/user/{id:\d+}' → named capture group with custom regex
    - Simple parameter: '/user/{id}' → matches any non-slash chars (equivalent to {id:[^/]+})
    - Wildcard style: '/user/*' → matches anything after /user/
    - Catch-all: '/{.*}' → matches all routes (use {.*} for catch-all patterns)
    - Raw regex: '/user/(.*)' or '/user/(?P<id>\\d+)' → custom patterns

Handler Parameters:
    Routes can specify override_params for DI container overrides:
    route.override_params = {'user_id': 5, 'read_only': True}
    These are merged into handler invocation via container.make(fqn, **override_params)

Usage:
    from lib.routing.Route import Route
    
    # With regex constraint
    route = Route(
        uri='/user/{id:\d+}/dashboard',
        method='GET',
        handler='app.controllers.UserController@show',
        middleware=['auth', 'log'],
        override_params={'cache': True}
    )
    
    # Simple parameter (any non-slash chars)
    route2 = Route(
        uri='/posts/{slug}',
        method='GET',
        handler='app.controllers.PostController@show'
    )
    
    # Catch-all wildcard
    route3 = Route(
        uri='/{.*}',
        method='GET',
        handler='app.controllers.FallbackController@notFound'
    )
    
    # Match a request
    if route.matches('/user/42/dashboard', 'GET'):
        params = route.matches('/user/42/dashboard', 'GET')
        print(params)  # {'id': '42'}

Changelog:
    - 2026-02-16: Added support for {varname:regex} pattern syntax for intuitive regex constraints.
    - 2026-01-30: Added `override_params` for per-route DI overrides.
    - 2026-01-29: Extended pattern support (parameter, wildcard, regex).
"""

from typing import Any, List, Optional, Dict
import re


class Route:
    """Represents a single HTTP route.

    Supports multiple kinds of URI patterns:
    - Parameter with regex: '/user/{id:\d+}' → named capture `id` matching only digits
    - Simple parameter: '/user/{id}' → named capture `id` matching any non-slash chars
    - Wildcard style: '/user/*' → converted to regex '/user/.*'
    - Catch-all: '/{.*}' → matches any request (use as fallback route)
    - Raw regex: '/user/(.*)' or '/user/(?P<id>\\d+)' → custom regex patterns

    Parameter template syntax:
        {varname} → defaults to [^/]+ (any non-slash chars)
        {varname:regex} → uses custom regex pattern (e.g., {id:\d+})

    For unnamed capture groups the match will expose numeric keys ('0', '1', ...)
    in the returned params dict so handlers can still access captured values.
    
    Integrates with Container for handler resolution with optional DI overrides
    via override_params dict.
    """
    def __init__(
        self,
        uri: str,
        method: str,
        handler: Any,
        middleware: Optional[List[str]] = [],
        name: Optional[str] = None,
        override_params: Optional[Dict] = {}
    ):
        self.uri: str = uri
        self.method: str = method.upper()
        self.handler: Any = handler
        self.name: Optional[str] = name
        self.middleware: List[str] = middleware or []
        # Parameters to pass when resolving the handler from the container
        self.override_params: Dict = override_params or {}
        self.pattern: re.Pattern = self._compile_pattern(uri)
        self.param_names: List[str] = self._extract_params(uri)
    
    def _compile_pattern(self, uri: str) -> re.Pattern:
        """Convert route URI to regex pattern.
        
        Supports:
        - {varname:regex} → named parameter with custom regex
        - {varname} → named parameter matching any non-slash chars
        - {regex} → inline regex pattern without variable name (e.g., {.*}, {\d+})
        - /* → wildcard style (converted to .*)
        - Raw regex with () or []
        """
        # Check for {varname:regex} patterns first (has colon)
        if '{' in uri and ':' in uri:
            # Replace {varname:regex} with (?P<varname>regex)
            pattern = re.sub(r'\{(\w+):([^}]+)\}', r'(?P<\1>\2)', uri)
            pattern = f"^{pattern}$"
            return re.compile(pattern)
        
        # Check for simple {varname} patterns (word chars only in braces, no colon)
        if '{' in uri and not ':' in uri:
            # First try to match {varname} style (word chars)
            temp_pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', uri)
            # If substitution happened, use it; otherwise treat as inline regex
            if temp_pattern != uri:
                pattern = f"^{temp_pattern}$"
                return re.compile(pattern)
            
            # Otherwise treat {anything} as inline regex pattern (e.g., {.*}, {\d+})
            pattern = re.sub(r'\{([^}]+)\}', r'(\1)', uri)
            pattern = f"^{pattern}$"
            return re.compile(pattern)

        # Wildcard style: '*' -> '.*'
        if '*' in uri:
            p = uri.replace('*', '.*')
            pattern = f"^{p}$"
            return re.compile(pattern)

        # Raw regex style (contains explicit group or bracket characters)
        if '(' in uri or '[' in uri:
            p = uri
            # Anchor if not already anchored
            if not p.startswith('^'):
                p = f'^{p}$'
            return re.compile(p)

        # Exact match fallback
        pattern = f"^{uri}$"
        return re.compile(pattern)
    
    def _extract_params(self, uri: str) -> List[str]:
        """Extract parameter names from URI.
        
        Handles both {varname} and {varname:regex} syntax.
        """
        # Extract variable names from both {varname} and {varname:regex}
        return re.findall(r'\{(\w+)(?::[^}]+)?\}', uri)
    
    def matches(self, uri: str, method: str) -> Optional[Dict[str, str]]:
        """Check if this route matches the given URI and method."""
        if self.method != method.upper():
            return None
        
        match = self.pattern.match(uri)
        if match:
            gd = match.groupdict()
            if gd:
                return gd
            # No named groups — return numeric-indexed groups so handlers can use them
            groups = match.groups()
            return {str(i): groups[i] for i in range(len(groups))} if groups else {}
        return None
