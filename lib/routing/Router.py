"""lib.routing.Router - HTTP Request Router and Handler Dispatcher

Routes HTTP requests to handlers and invokes them with DI container support.

Features:
    - Route registration with URI patterns (parameter, wildcard, regex)
    - Advanced parameter patterns with regex: {varname:regex}
    - Per-route DI override parameters (override_params)
    - Middleware support (global and per-route) with flexible handler formats
    - Handler resolution from FQN strings or callables
    - Request/response forwarding
    - YAML route loading

Route Pattern Examples:
    - Simple parameter: /user/{id} → matches /user/123, /user/abc, etc.
    - Regex parameter: /user/{id:\d+} → matches only /user/123
    - Named pattern: /{name:\w+}/ → matches alphanumeric names only
    - Wildcard: /admin/* → matches /admin/anything/here
    - Catch-all: /{.*} → fallback for unmatched routes
    - Custom regex: /post/(\d+) → raw regex pattern

Handler Formats:
    - FQN@method: 'app.controllers.UserController@show'
    - List format: [UserController, 'show']
    - Callable: lambda request, **params: response

Middleware Handler Formats:
    - Callable: lambda container, request, next: response
    - FQN string: 'app.middleware.AuthMiddleware' (instantiated)
    - FQN@method: 'app.middleware.Auth@check' (method called)
    - Simple name: 'AuthMiddleware' (resolved via autoloader)

Usage:
    from lib.routing.Router import Router
    from lib.di.Container import Container
    from lib.di.Autoloader import Autoloader
    
    autoloader = Autoloader(['app', 'lib'])
    container = Container()
    container.set_autoloader(autoloader)
    router = Router(request, autoloader=autoloader)
    
    # Add route with regex constraint
    router.add_route(
        uri='/users/{id:\d+}',
        method='GET',
        handler='app.controllers.UserController@show',
        override_params={'cache': True, 'timeout': 30}
    )
    
    # Register middleware (multiple formats supported)
    router.use('app.middleware.AuthMiddleware')  # Will be instantiated
    router.use('app.middleware.Auth@check')      # Will call check() method
    router.use(lambda container, request, next: next())  # Direct callable
    
    # Dispatch request
    response = router.dispatch(container)

DI Integration:
    Routes can specify override_params which are merged into container.make().
    This allows per-route dependency overrides without modifying container bindings.

Middleware:
    - Global middleware applied to all routes via use()
    - Per-route middleware applied to specific routes
    - Middleware can modify request/response flow

Changelog:
    - 2026-02-16: Enhanced middleware handler resolution (FQN, @method, simple names, callables)
    - 2026-02-16: Enhanced documentation for {varname:regex} pattern syntax.
    - 2026-01-30: Updated docstring for model/datasource integration.
    - 2026-01-29: Added `override_params` support; uses public Container APIs.
    - 2026-01-28: Initial implementation with basic routing.
"""

from typing import List, Callable, Any, Dict, Optional
from lib.routing.Route import Route
#import handler
import re
import os
from lib.logging.Logger import Logger
import yaml
from pathlib import Path
import importlib
import inspect


class Router:
    def __init__(self, request, routes_path=None):
        self.routes = []
        self.middleware = {}
        self.global_middleware = []
        # Middleware registered against arbitrary URI patterns (no handler required)
        # Each entry: {'uri': str, 'pattern': re.Pattern, 'middleware': List[Any]}
        self.path_middleware = []
        self.request = request
        
        self._log = Logger(format="%(asctime)s [%(levelname)8s] %(name)s:%(filename)s:%(lineno)d - %(funcName)s() - %(message)s", level="INFO", file="/usr/lib/cgi-bin/app/logs/Router.log")
        if routes_path:
            self._load_routes(routes_path)
    
    def _load_routes(self, path):
        """Load routes from YAML file"""
        file = Path(path)
        if not file.exists():
            return
        
        try:
            content = file.read_text()
            routes_config = yaml.safe_load(content)
            
            # Load routes
            for route_data in routes_config.get('routes', []):
                self.add_route(
                    uri=route_data['uri'],
                    method=route_data.get('method', 'GET'),
                    handler=route_data['handler'],
                    middleware=route_data.get('middleware', [])
                )
        except Exception as e:
            print(f"Error loading routes: {e}")
    
    def add_route(self, uri, method, handler, middleware=None, override_params=None):
        """Add a route and resolve handler FQN using autoloader

        override_params: Optional dict of key=>value params to pass into
        `container.make()` when the route's controller is resolved.
        """
        route = Route(
            uri=uri,
            method=method,
            handler=handler,
            middleware=middleware,
            override_params=override_params,
        )
        self.routes.append(route)
        #self._log.info(f"Added route: {uri} -> {handler}")
    
    def register_middleware(self, name: str, handler: Any):
        """Register middleware by name with flexible handler formats.
        
        Handler formats:
        - Callable: lambda/function ref → called with (container, request, next)
        - FQN string: 'app.middleware.AuthMiddleware' → instantiated with (container, request, next)
        - FQN@method: 'app.middleware.Auth@check' → method called with (container, request, next)
        - Simple name: 'AuthMiddleware' → looked up in autoloader._registry_simple
        """
        self.middleware[name] = handler
    
    def use(self, middleware_handler: Any) -> "Router":
        """Apply middleware to all routes.
        
        Args:
            middleware_handler: Can be:
                - String (FQN): 'app.middleware.AuthMiddleware' or simple name 'AuthMiddleware'
                - String with method: 'app.middleware.Auth@check'
                - Callable: function or lambda
        
        Returns:
            self for chaining
        """
        # If it's a string, register it by name
        if isinstance(middleware_handler, str):
            name = middleware_handler
            self.register_middleware(name, middleware_handler)
            if name not in self.global_middleware:
                self.global_middleware.append(name)
        else:
            # For callables, generate a unique name
            name = f"_middleware_{len(self.middleware)}"
            self.register_middleware(name, middleware_handler)
            if name not in self.global_middleware:
                self.global_middleware.append(name)
        
        return self

    def register_path_middleware(self, uri: str, middleware: list):
        """Register middleware for a URI pattern without adding a full route.

        Example:
            router.register_path_middleware('/health', ['AuthMiddleware', my_callable])

        The `uri` accepts the same pattern syntax as `Route` (eg. '/api/{id:\\d+}').
        Middleware listed will be executed for matching requests even if no route
        handler exists for that URI.
        """
        # Reuse Route to compile pattern
        try:
            r = Route(uri=uri, method='GET', handler=lambda *_: None)
            self.path_middleware.append({
                'uri': uri,
                'pattern': r.pattern,
                'middleware': middleware or []
            })
            #self._log.info(f"Registered path-only middleware for: {uri}")
        except Exception as e:
            raise ValueError(f"Failed to register path middleware for {uri}: {e}")
    
    def _resolve_middleware_handler(self, container, handler: Any) -> Callable:
        """Resolve middleware handler to a callable.
        
        Supports:
        1. Callables (functions, lambdas) → returned as-is
        2. Registered middleware names → looked up in self.middleware registry
        3. FQN strings: 'app.middleware.AuthMiddleware' → instantiate class with (container, request, next)
        4. FQN@method: 'app.middleware.Auth@check' → call method with (container, request, next)
        5. Simple names: 'AuthMiddleware' → lookup in autoloader._registry_simple, then instantiate
        """
        # Already a callable
        if callable(handler):
            return handler
        
        # Handle string handlers
        if isinstance(handler, str):
            """ # First check if it's a registered middleware name
            if handler in self.middleware:
                # Recursively resolve the registered handler
                registered_handler = self.middleware[handler]
                self._log.info(f"Resolving registered middleware: {handler} -> {registered_handler}")
                return self._resolve_middleware_handler(container, registered_handler)
            """
            
            # Check for @method syntax
            if '@' in handler:
                fqn_path, method_name = handler.rsplit('@', 1)
                
                try:
                    # Resolve the class
                    target_class = self._resolve_class_from_string(container, fqn_path)
                    
                    # Return a wrapper that instantiates and calls the method
                    def middleware_wrapper1(container, request, next_callback):
                        # Instantiate directly with (container, request, next)
                        instance = target_class(container, request, next_callback)
                        method = getattr(instance, method_name)
                        return method(container, request, next_callback)
                    
                    return middleware_wrapper1
                except Exception as e:
                    raise ValueError(f"Failed to resolve middleware method {handler}: {e}")
            else:
                # Just FQN or simple name - instantiate with (container, request, next)
                try:
                    target_class = self._resolve_class_from_string(container, handler)
                    
                    # Return a wrapper that instantiates the middleware
                    def middleware_wrapper(container, request, next_callback):
                        # Directly instantiate with (container, request, next)
                        instance = target_class(container, request, next_callback)
                        # If it has a handle method, call it
                        if hasattr(instance, 'handle'):
                            return instance.handle(container, request, next_callback)
                        # Otherwise assume the instance was the middleware (e.g., callable class)
                        # or it handled everything in __init__
                        return instance
                    
                    return middleware_wrapper
                except Exception as e:
                    raise ValueError(f"Failed to resolve middleware {handler}: {e}")
        
        raise ValueError(f"Invalid middleware handler type: {type(handler)}")
    
    def _resolve_class_from_string(self, container, name: str) -> type:
        """Resolve a class from FQN or simple name.
        
        Tries:
        1. FQN via autoloader._registry_fqn
        2. Simple name via autoloader._registry_simple
        3. Container resolution as fallback
        """
        try:
            # Get autoloader from container
            autoloader = None
            if hasattr(container, '_autoloader'):
                autoloader = container._autoloader
            elif hasattr(container, 'get_autoloader'):
                autoloader = container.get_autoloader()
            
            if autoloader:
                # Try FQN lookup in autoloader
                if hasattr(autoloader, '_registry_fqn') and name in autoloader._registry_fqn:
                    return autoloader._registry_fqn[name]
                
                # Try simple name lookup in autoloader
                if hasattr(autoloader, '_registry_simple') and name in autoloader._registry_simple:
                    return autoloader._registry_simple[name]
            
            # If autoloader doesn't have it, try container resolution
            target = container.resolve(name)
            if inspect.isclass(target):
                return target
            # If it's a module, try to get the class from it
            if inspect.ismodule(target):
                class_name = name.split('.')[-1]
                if hasattr(target, class_name):
                    cls = getattr(target, class_name)
                    if inspect.isclass(cls):
                        return cls
        except:
            pass
        
        raise ValueError(f"Cannot resolve class: {name}")
    
    def find_route(self, uri, method):
        """Find matching route and extract parameters"""
        for route in self.routes:
            match = route.matches(uri, method)
            if match is not None:
                return route, match
        
        return None, None
    
    def get_routes(self):
        """Get all routes for debugging"""
        return [{
            'uri': r.uri,
            'method': r.method,
            'handler': r.handler,
            'middleware': r.middleware,
            'override_params': getattr(r, 'override_params', {})
        } for r in self.routes]
    
    def dispatch(self, container):
        """Dispatch the request through middleware and handler"""
        
        # Get path from environment (more reliable than request.get_uri())
        path_info = os.environ.get('PATH_INFO', '')
        
        # If no PATH_INFO, try to extract from REQUEST_URI
        if not path_info:
            request_uri = self.request.get_uri()
            script_name = os.environ.get('SCRIPT_NAME', '')
            
            # Remove script name from URI
            if script_name and request_uri.startswith(script_name):
                path_info = request_uri[len(script_name):]
            else:
                # Fallback to old logic
                path_info = re.sub(r"^/(public|private)", "", request_uri)
        
        # Clean up the path
        if path_info.startswith('/cgi-bin/public'):
            path_info = path_info[len('/cgi-bin/public'):]
        elif path_info.startswith('/public'):
            path_info = path_info[len('/public'):]
        
        # Default to root
        if not path_info:
            path_info = '/'
        
        uri = path_info
        method = self.request.get_method()
        
        # Find matching route
        route, params = self.find_route(uri, method)
        #self._log.info(f"Dispatching request: {method} {uri} -> Route: {route.uri if route else 'None'}, Params: {params}")
        if not route:
            # If no route matched, check for path-only middleware that may
            # want to handle this URI even without a full route handler.
            middleware_chain = []

            # Add global middleware first
            for mw_name in self.global_middleware:
                if mw_name in self.middleware:
                    mw_handler = self.middleware[mw_name]
                    try:
                        resolved_mw = self._resolve_middleware_handler(container, mw_handler)
                        middleware_chain.append(resolved_mw)
                    except Exception as e:
                        #self._log.info(f"Failed to resolve global middleware {mw_name}: {e}")
                        continue
                elif container.has_binding(mw_name):
                    mw = container.make(mw_name)
                    if mw:
                        middleware_chain.append(mw)

            # Add any registered path-only middleware that match this URI
            for pm in self.path_middleware:
                try:
                    if pm['pattern'].match(uri):
                        for mw_handler in pm.get('middleware', []):
                            try:
                                resolved_mw = self._resolve_middleware_handler(container, mw_handler)
                                middleware_chain.append(resolved_mw)
                            except Exception as e:
                                #self._log.info(f"Failed to resolve path middleware {mw_handler}: {e}")
                                continue
                except Exception:
                    continue

            # If we have middleware to run, execute the chain and return.
            if middleware_chain:
                def execute_path_chain(index=0):
                    if index < len(middleware_chain):
                        mw = middleware_chain[index]
                        if hasattr(mw, 'handle'):
                            return mw.handle(container, self.request, lambda: execute_path_chain(index + 1))
                        elif callable(mw):
                            return mw(container, self.request, lambda: execute_path_chain(index + 1))
                    else:
                        # No handler to call after path-only middleware
                        return None

                execute_path_chain()
                # After path-only middleware runs, if no handler took over, return 404
                response = container.make('response')
                response.set_status_code(404)
                response.set_content_type("text/html")
                response.set_body("<h1>404 - Route Not Found</h1>")
                response.send()
                return

            # No path middleware matched; return 404 as before
            response = container.make('response')
            response.set_status_code(404)
            response.set_content_type("text/html")
            response.set_body("<h1>404 - Route Not Found</h1>")
            response.send()
            return
        
        # Set route params on request
        if params:
            self.request.set_path_params(params)
        
        # Build complete middleware chain: global + route-specific
        middleware_chain = []
        
        # Add global middleware first
        for mw_name in self.global_middleware:
            if mw_name in self.middleware:
                mw_handler = self.middleware[mw_name]
                # Resolve the middleware handler
                try:
                    resolved_mw = self._resolve_middleware_handler(container, mw_handler)
                    middleware_chain.append(resolved_mw)
                except Exception as e:
                    self._log.info(f"Failed to resolve global middleware {mw_name}: {e}")
                    continue
            elif container.has_binding(mw_name):
                mw = container.make(mw_name)
                if mw:
                    middleware_chain.append(mw)
        
        # Add route-specific middleware
        if route.middleware:
            for mw_handler in route.middleware:
                #self._log.info(f"Resolving route-specific middleware: {mw_handler}")
                try:
                    resolved_mw = self._resolve_middleware_handler(container, mw_handler)
                    middleware_chain.append(resolved_mw)
                except Exception as e:
                    self._log.info(f"Failed to resolve route middleware {mw_handler}: {e}")
                    continue
        
        # Execute middleware chain and handler
        def execute_chain(index=0):
            if index < len(middleware_chain):
                # Execute middleware
                mw = middleware_chain[index]
               
                # Check if middleware has a handle method or is callable
                if hasattr(mw, 'handle'):
                    return mw.handle(container, self.request, lambda: execute_chain(index + 1))
                elif callable(mw):
                    return mw(container, self.request, lambda: execute_chain(index + 1))
            else:
                # All middleware done, execute handler
                return self._call_handler(container, self.request, route, **(params or {}))
        
        return execute_chain()
    
    def _call_handler(self, container, request, route, **params):
        """Call the controller handler using resolved FQN

        `route` is a `Route` instance -- its `override_params` will be
        forwarded to `container.make()` when instantiating controllers.
        """
        handler = route.handler
        override_params = getattr(route, 'override_params', {}) or {}
        
        # Handle FQN format "app.controllers.routes.ControllerName@method"
        if isinstance(handler, str) and '@' in handler:
            fqn_path, method = handler.rsplit('@', 1)

            try:
                # Resolve the symbol first
                target = container.resolve(fqn_path)
                
                # If it's a module, look for a class with the same name inside it
                if inspect.ismodule(target):
                    class_name = fqn_path.split('.')[-1]
                    if hasattr(target, class_name):
                        target = getattr(target, class_name)
                
                # Now pass the actual Class to make()
                controller = container.make(target, force_build=bool(override_params), **(override_params or {}))
                
                handler_method = getattr(controller, method)
                return handler_method(container, request, **params)
        
            except Exception as e:
                raise e
        
        # If callable (lambda or function), just call it
        if callable(handler):
            # Merge override_params with path params (path params override)
            merged = {**override_params, **params}
            return handler(container, request, **merged)
        
        # Fallback
        raise ValueError(f"Unable to resolve handler: {handler}")
