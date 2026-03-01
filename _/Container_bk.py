import yaml
import inspect
import importlib
from lib.logging.Logger import Logger
from typing import Any, Callable, Dict, Optional
from ..lib.di.Autoloader import Autoloader

class AppException(Exception):
    pass                 

class Container:
    """Minimal but fully functional DI container"""
    
    def __init__(self):
        self._bindings: Dict[str, Any] = {}
        self._instances: Dict[str, Any] = {}
        self._aliases: Dict[str, str] = {}
        self._props: Dict[str, Any] = {}
        self._binding_params: Dict[str, Dict] = {}  # Store params for bindings
        self._is_singleton: Dict[str, bool] = {}  # Track singleton status
        self._autoloader: Autoloader
        self.services = {}
        self._log = Logger()
        
    def add_property(self, key, value):
        self._props[key] = value
        return self
    def get_prop(self, key):
        return self._props[key]
    
    def register(self, name, factory, singleton=False):
        self.services[name] = {'factory': factory, 'singleton': singleton}
        return self

    def set_autoloader(self, autoloader: Any) -> "Container":
        """Register an autoloader for fallback class resolution"""
        self._autoloader = autoloader
        return self
        
    def make(self, abstract: Any, force_build: bool = False, **override_params) -> Any:
        """
        Resolve instance, merging binding params with override params
        
        Args:
            abstract: String key or class (e.g., "Request" or Request)
        """
        # Special-case: fully-qualified module.Class string -> resolve/build directly
        if isinstance(abstract, str) and '.' in abstract:
            # Try to resolve the symbol
            try:
                concrete = self._resolve_fqn(abstract)
            except AppException:
                # Fallback to treating as binding key
                concrete = None

            binding_params = override_params.copy()

            if concrete is not None and inspect.isclass(concrete):
                
                if force_build:
                    return self._build(concrete, binding_params)
                # Not forcing build: try to use usual binding/cache semantics via normalized key
                key = self._normalize_key(concrete)
            else:
                # treat as binding key
                key = self._normalize_key(abstract)

        else:
            key = self._normalize_key(abstract)

        # Check for existing singleton instance
        if key in self._instances and self._instances[key] is not None and not force_build:
            return self._instances[key]

        # Get binding params (if any) and merge with override
        binding_params = self._binding_params.get(key, {}).copy()
        binding_params.update(override_params)

        # If force_build is requested and we have a binding for this key, attempt to build fresh
        if force_build and key in self._bindings:
            concrete = self._bindings.get(key)
            # If concrete is a string FQN, resolve it
            if isinstance(concrete, str):
                concrete_resolved = self._resolve_fqn(concrete)
                if inspect.isclass(concrete_resolved):
                    instance = self._build(concrete_resolved, binding_params)
                else:
                    # callable factory or instance
                    instance = self._resolve(key, binding_params)
            elif inspect.isclass(concrete):
                instance = self._build(concrete, binding_params)
            else:
                instance = self._resolve(key, binding_params)
        else:
            # Resolve normally (this will build if necessary)
            instance = self._resolve(key, binding_params)

        # Store singleton if registered as such
        if key in self._instances and not force_build:
            self._instances[key] = instance

        return instance

    def _resolve(self, abstract: str, params: Dict) -> Any:
        """Resolve the concrete implementation"""
        # Resolve alias
        abstract = self._aliases.get(abstract, abstract)
        
        # Get concrete from bindings
        concrete = self._bindings.get(abstract, abstract)

        # Callable factory (lambda, function, or method)
        if callable(concrete) and not inspect.isclass(concrete):
            # Check signature to determine how to call
            sig = inspect.signature(concrete)
            
            param_names = list(sig.parameters.keys())
            
            # If first param is named 'container' or 'c', pass container
            if param_names and param_names[0] in ('container', 'c', 'cont'):
                return concrete(self, **params)
            else:
                # Otherwise just pass params
                return concrete(**params)

        # Already an object instance
        if not isinstance(concrete, str) and not inspect.isclass(concrete):
            return concrete

        # String (FQN) or class → build it
        return self._build(concrete, params)

    def _build(self, concrete: Any, params: Dict) -> Any:
        """Build an instance with dependency injection - FIXED VERSION"""
        # If string, resolve to actual class
        if isinstance(concrete, str):
            concrete = self._resolve_fqn(concrete)

        # Must be a class
        if not inspect.isclass(concrete):
            raise AppException(f"Cannot build non-class {concrete}")

        # Get constructor signature
        ctor = concrete.__init__
        sig = inspect.signature(ctor)

        args = []
        kwargs = {}
        
        for name, param in sig.parameters.items():
            if name == "self":
                continue

            # 1. Check if param was explicitly provided
            if name in params:
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append(params[name])
                else:
                    kwargs[name] = params[name]
                continue

            # 2. Check if param has type annotation (for DI)
            if param.annotation is not inspect.Parameter.empty:
                try:
                    # Try to resolve from container - BUT skip built-in types
                    annotation_str = str(param.annotation)
                    
                    # Skip built-in types that can't be instantiated via container
                    builtin_types = {int, str, float, bool, list, dict, tuple, set, bytes}
                    
                    if param.annotation in builtin_types or annotation_str in [
                        '<class \'int\'>', '<class \'str\'>', '<class \'float\'>', 
                        '<class \'bool\'>', '<class \'list\'>', '<class \'dict\'>',
                        '<class \'tuple\'>', '<class \'set\'>', '<class \'bytes\'>'
                    ]:
                        # Skip built-in types - they don't need DI
                        raise AppException(f"Skipping built-in type {param.annotation}")
                    
                    dep = self.make(param.annotation)
                    if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                        args.append(dep)
                    else:
                        kwargs[name] = dep
                    continue
                except AppException as e:
                    # If can't resolve, fall through to default check
                    if "Skipping built-in type" not in str(e):
                        pass  # Log or handle other DI failures

            # 3. Use default value if available
            if param.default is not inspect.Parameter.empty:
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append(param.default)
                else:
                    kwargs[name] = param.default
                continue

            # 4. SPECIAL HANDLING: If parameter is 'args', provide empty dict
            # This fixes classes like Home that expect args parameter
            if name == 'args':
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append({})
                else:
                    kwargs[name] = {}
                continue

            # 5. SPECIAL HANDLING: If parameter is 'kwargs', provide empty dict
            if name == 'kwargs':
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append({})
                else:
                    kwargs[name] = {}
                continue

            # 6. SPECIAL HANDLING: Common parameter names get sensible defaults
            if name in ['config', 'settings', 'options']:
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append({})
                else:
                    kwargs[name] = {}
                continue

            # 7. Can't resolve this parameter - provide None for built-in types
            # This is more forgiving for classes with simple parameters
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                args.append(None)
            else:
                kwargs[name] = None

        try:
            return concrete(*args, **kwargs)
        except TypeError as e:
            # If we get a TypeError about invalid keyword arguments,
            # try again without the kwargs (only use args)
            if "keyword argument" in str(e):
                # Try with positional arguments only
                try:
                    return concrete(*args)
                except TypeError:
                    # Last resort: try with no arguments
                    try:
                        return concrete()
                    except TypeError:
                        raise AppException(f"Failed to instantiate {concrete}: {e}") from e
            raise AppException(f"Failed to instantiate {concrete}: {e}") from e

    def has_binding(self, abstract: str) -> bool:
        """Check if a binding exists"""
        return abstract in self._bindings

    def is_singleton(self, abstract: str) -> bool:
        """Check if a binding is registered as singleton"""
        return self._is_singleton.get(abstract, False)
    
    def _resolve_fqn(self, ref: str) -> Any:
        """Resolve a fully qualified name to a class/function"""
        if "." not in ref:
            # Only treat plain strings as binding keys; do not fall back to globals
            if ref in self._bindings:
                return self._bindings[ref]
            elif ref in self._autoloader._registry_simple:
                return self._autoloader._registry_simple[ref]  
            raise AppException(f"Symbol or binding '{ref}' not found")

        # Module.Class or Module.function
        module_path, attr = ref.rsplit(".", 1)
        try:
            module = importlib.import_module(module_path)
            return getattr(module, attr)
        except (ImportError, AttributeError) as e:
            # Fallback to autoloader if available
            if self._autoloader:
                cls = self._autoloader.get_class(ref)
                if cls:
                    return cls
            raise AppException(f"Cannot resolve '{ref}': {e}") from e

    def resolve(self, ref: str) -> Any:
        """Public wrapper for resolving a fully-qualified name or binding"""
        return self._resolve_fqn(ref)

    def build(self, concrete: Any, params: Dict = {}) -> Any:
        """Public builder that accepts class or FQN and params."""
        if params is None:
            params = {}
        if isinstance(concrete, str):
            concrete = self._resolve_fqn(concrete)
        if not inspect.isclass(concrete):
            raise AppException(f"Cannot build non-class {concrete}")
        return self._build(concrete, params)

    def alias(self, alias: Any, fqn: Any) -> None:
        """Register an alias for a fully qualified name
        
        Args:
            alias: String or class to use as alias
            fqn: String or class to resolve to
        """
        alias_key = self._normalize_key(alias)
        fqn_key = self._normalize_key(fqn)
        self._aliases[alias_key] = fqn_key

    def _normalize_key(self, key: Any) -> str:
        """Convert class or string to normalized key"""
        # Use module-qualified name for classes to avoid collisions
        if inspect.isclass(key):
            return f"{key.__module__}.{key.__name__}"
        return str(key)

    def bind(self, abstract: Any, concrete: Any, **params) -> None:
        """Bind abstract to concrete with optional parameters
        
        Args:
            abstract: String key or class (e.g., "Request" or Request)
            concrete: Implementation (string FQN, class, callable, or instance)
        """
        key = self._normalize_key(abstract)
        self._bindings[key] = concrete
        self._is_singleton[key] = False
        if params:
            self._binding_params[key] = params

    def singleton(self, abstract: Any, concrete: Any, **params) -> None:
        """Register singleton with optional parameters
        
        Args:
            abstract: String key or class (e.g., "Request" or Request)
            concrete: Implementation (string FQN, class, callable, or instance)
        """
        key = self._normalize_key(abstract)
        self._bindings[key] = concrete
        # If concrete is an instance object (not a string, class, or factory function), store it directly
        # Check if it's an instance by seeing if it's a class or string - if neither, it's likely an instance
        is_instance = not isinstance(concrete, str) and not inspect.isclass(concrete) and not (callable(concrete) and (inspect.isfunction(concrete) or inspect.ismethod(concrete) or inspect.isbuiltin(concrete)))
        if is_instance:
            self._instances[key] = concrete
        else:
            self._instances[key] = None
        self._is_singleton[key] = True
        if params:
            self._binding_params[key] = params

    def factory(self, abstract: Any, concrete: Any, **params) -> None:
        """Register factory (always creates new instance) with optional parameters
        
        Args:
            abstract: String key or class (e.g., "Request" or Request)
            concrete: Implementation (string FQN, class, callable, or instance)
        """
        self.bind(abstract, concrete, **params)

    def _get_name(self, key):
        """Convert key to display name (handles class objects)"""
        return key.__name__ if hasattr(key, '__name__') else str(key)

    def get_bindings(self):
        """Get all registered service names"""
        return [self._get_name(name) for name in self._bindings.keys()]

    def get_singletons(self):
        """Get all singleton service names"""
        return [self._get_name(name) for name, is_singleton in self._is_singleton.items() if is_singleton]

    def get_factories(self):
        """Get all factory service names"""
        return [self._get_name(name) for name, is_singleton in self._is_singleton.items() if not is_singleton]

    def get_instances(self):
        """Get all instantiated singletons"""
        return {self._get_name(name): instance for name, instance in self._instances.items() if instance is not None}

    def get_service_info(self):
        """Get detailed info about all services"""
        info = []
        for name in self._bindings.keys():
            display_name = self._get_name(name)
            is_singleton = self._is_singleton.get(name, False)
            service_type = "singleton" if is_singleton else "factory"
            instantiated = self._instances.get(name) is not None if is_singleton else None
            
            info.append({
                'name': display_name,
                'type': service_type,
                'instantiated': instantiated
            })
        return info

    def dump(self):
        """Dump container contents for debugging"""
        return {
            'bindings': self.get_bindings(),
            'singletons': self.get_singletons(),
            'factories': self.get_factories(),
            'properties': list(self._props.keys()),
            'instantiated': list(self.get_instances().keys()),
            'service_info': self.get_service_info()
        }

    def call(self, handler: Any, **parameters) -> Any:
        """
        Call a handler with dependency injection
        
        Example:
            container.call([MyController, "index"], request=request, response=response)
        """
        callable_fn = self.make_callable(handler)
        sig = inspect.signature(callable_fn)

        args = []
        kwargs = {}
        
        for name, param in sig.parameters.items():
            # 1. Explicitly provided parameter
            if name in parameters:
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append(parameters[name])
                else:
                    kwargs[name] = parameters[name]
                continue

            # 2. Type annotation (DI) - skip built-in types
            if param.annotation is not inspect.Parameter.empty:
                annotation_str = str(param.annotation)
                builtin_types = {int, str, float, bool, list, dict, tuple, set, bytes}
                
                if param.annotation not in builtin_types and annotation_str not in [
                    '<class \'int\'>', '<class \'str\'>', '<class \'float\'>', 
                    '<class \'bool\'>', '<class \'list\'>', '<class \'dict\'>',
                    '<class \'tuple\'>', '<class \'set\'>', '<class \'bytes\'>'
                ]:
                    try:
                        dep = self.make(param.annotation)
                        if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                            args.append(dep)
                        else:
                            kwargs[name] = dep
                        continue
                    except AppException:
                        pass

            # 3. Default value
            if param.default is not inspect.Parameter.empty:
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append(param.default)
                else:
                    kwargs[name] = param.default
                continue

            # 4. SPECIAL HANDLING for 'args' and 'kwargs'
            if name == 'args':
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append({})
                else:
                    kwargs[name] = {}
                continue
                
            if name == 'kwargs':
                if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                    args.append({})
                else:
                    kwargs[name] = {}
                continue

            # 5. Can't resolve - provide None
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                args.append(None)
            else:
                kwargs[name] = None

        return callable_fn(*args, **kwargs)

    def make_callable(self, handler: Any) -> Callable:
        """
        Convert handler to callable
        
        Supports:
            - Function: my_function
            - Array: [ClassName, "method"]
            - String: "ClassName@method"
            - FQN: "app.controllers.HomeController"
        """
        # Already callable
        if callable(handler):
            return handler

        # Array/tuple: [Class, "method"]
        if isinstance(handler, (list, tuple)) and len(handler) == 2:
            cls_or_name, method = handler
            
            # If it's a string, resolve it
            if isinstance(cls_or_name, str):
                instance = self.make(cls_or_name)
            # If it's a class, instantiate it
            elif inspect.isclass(cls_or_name):
                instance = self.make(cls_or_name.__name__)
            # Already an instance
            else:
                instance = cls_or_name
            
            if not hasattr(instance, method):
                raise AppException(f"Method '{method}' not found on {cls_or_name}")
            
            return getattr(instance, method)

        # String: "Class@method"
        if isinstance(handler, str) and "@" in handler:
            cls_name, method = handler.split("@", 1)
            instance = self.make(cls_name)
            
            if not hasattr(instance, method):
                raise AppException(f"Method '{method}' not found on {cls_name}")
            
            return getattr(instance, method)

        # Fully qualified function or class
        if isinstance(handler, str):
            symbol = self._resolve_fqn(handler)
            if callable(symbol):
                return symbol
            raise AppException(f"Symbol '{handler}' is not callable")
        
        raise AppException(f"Cannot make callable from {handler}")