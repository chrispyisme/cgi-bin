import sys
import os
import inspect
from typing import Any, Dict, List, Optional, Callable
from lib.di.Container import Container

class ServiceManager:
    """
    Service Manager for your existing Container
    
    Features:
    - Add, remove, update services
    - Internal service registry with metadata
    - Auto-resolve params (FQNs, classes, primitives, etc.)
    - Query by type, tags
    - Bulk load from config
    """
    
    def __init__(self, container: Container):
        """Initialize with your existing Container instance"""
        self.container = container
        self._registry: Dict[str, Dict[str, Any]] = {}
    
    # ========== CORE OPERATIONS ==========
    
    def add(self, abstract: str, concrete: str|Callable, service_type: str = 'singleton', 
            params: Optional[Dict] = None, tags: Optional[List[str]] = None,
            description: str = '') -> 'ServiceManager':
        """
        Add a service
        
        Args:
            abstract: Service name (e.g., "router", "database")
            concrete: Class FQN (e.g., "lib.routing.Router.Router")
            service_type: 'singleton', 'factory', or 'bind'
            params: Constructor params (auto-resolved!)
            tags: Optional tags for categorization
            description: Optional description
        """
        # Store in registry
        self._registry[abstract] = {
            'abstract': abstract,
            'concrete': concrete,
            'type': service_type,
            'params': params or {},
            'tags': tags or [],
            'description': description,
            'registered': True
        }
        
        # Register with container
        self._register_service(abstract)
        
        return self
    
    def remove(self, abstract: str) -> bool:
        """Remove a service"""
        if abstract not in self._registry:
            return False
        
        # Mark as unregistered
        self._registry[abstract]['registered'] = False
        
        # Remove from container
        key = self.container._normalize_key(abstract)
        self.container._bindings.pop(key, None)
        self.container._instances.pop(key, None)
        self.container._is_singleton.pop(key, None)
        self.container._binding_params.pop(key, None)
        
        del self._registry[abstract]
        return True
    
    def update(self, abstract: str, **kwargs) -> bool:
        """
        Update service config
        
        Can update: concrete, params, type, tags, description
        """
        if abstract not in self._registry:
            return False
        
        service = self._registry[abstract]
        
        # Update fields
        for field in ['concrete', 'params', 'type', 'tags', 'description']:
            if field in kwargs:
                service[field] = kwargs[field]
        
        # Re-register
        self._register_service(abstract)
        return True
    
    def reload(self, abstract: str) -> bool:
        """Force rebuild singleton instance"""
        if abstract not in self._registry:
            return False
        
        key = self.container._normalize_key(abstract)
        if key in self.container._instances:
            self.container._instances[key] = None
        
        return True
    
    # ========== BULK OPERATIONS ==========
    
    def load_services(self, services: List[Dict]) -> 'ServiceManager':
        """
        Load from config array
        
        Example:
        services = [
            {
                "abstract": "router",
                "concrete": "lib.routing.Router.Router",
                "type": "singleton",
                "params": {"request": "lib.http.Request.Request"},
                "tags": ["routing", "http"]
            }
        ]
        """
        for service in services:
            self.add(
                abstract=service['abstract'],
                concrete=service['concrete'],
                service_type=service.get('type', 'singleton'),
                params=service.get('params'),
                tags=service.get('tags'),
                description=service.get('description', '')
            )
        return self
    
    def clear_all(self) -> 'ServiceManager':
        """Remove all services"""
        for abstract in list(self._registry.keys()):
            self.remove(abstract)
        return self
    
    # ========== QUERY OPERATIONS ==========
    
    def has(self, abstract: str) -> bool:
        """Check if service exists"""
        return abstract in self._registry and self._registry[abstract]['registered']
    
    def get_service(self, abstract: str) -> Optional[Any]:
        """Get service metadata"""
        return self._registry.get(abstract)
    
    def list_services(self, service_type: Optional[str] = None, 
                     tag: Optional[str] = None) -> List[str]:
        """List services, optionally filtered by type or tag"""
        services = []
        for abstract, service in self._registry.items():
            if not service['registered']:
                continue
            if service_type and service['type'] != service_type:
                continue
            if tag and tag not in service['tags']:
                continue
            services.append(abstract)
        return services
    
    def get_registry(self) -> Dict[str, Dict]:
        """Get full registry"""
        return {k: v for k, v in self._registry.items() if v['registered']}
    
    def get_singletons(self) -> List[str]:
        """Get all singletons"""
        return self.list_services(service_type='singleton')
    
    def get_factories(self) -> List[str]:
        """Get all factories"""
        return self.list_services(service_type='factory')
    
    def get_tagged(self, tag: str) -> List[str]:
        """Get services with specific tag"""
        return self.list_services(tag=tag)
    
    # ========== CONTAINER PROXY ==========
    def add_property(self, key:str, value:Any):
        self.container.add_property(key, value)
        
    def get_property(self, key:str):
        return self.container.get_property(key) 
    
    def make(self, abstract: str, **override_params) -> Any:
        """Get service instance from container"""
        return self.container.make(abstract, **override_params)
    
    def resolve(self, ref: str) -> Any:
        """Resolve FQN or binding"""
        return self.container.resolve(ref)
    
    def build(self, concrete: Any, params: Optional[Dict] = None) -> Any:
        """Build instance with DI"""
        return self.container.build(concrete, params or {})
    
    # ========== INTERNAL METHODS ==========
    
    def _register_service(self, abstract: str) -> None:
        """Register service with container"""
        service = self._registry[abstract]
        
        # Register binding using container's methods
        if service['type'] == 'singleton':
            self.container.singleton(service['abstract'], service['concrete'])
        elif service['type'] == 'factory':
            self.container.factory(service['abstract'], service['concrete'])
        else:
            self.container.bind(service['abstract'], service['concrete'])
        
        # Auto-resolve and inject params
        if service['params']:
            resolved = self._auto_resolve_params(service['params'])
            key = self.container._normalize_key(service['abstract'])
            self.container._binding_params[key] = resolved
            
    def _auto_resolve_params(self, params: Dict) -> Dict:
        """Auto-resolve all param types"""
        return {name: self._resolve_value(value) for name, value in params.items()}
    
    def _resolve_value(self, value: Any) -> Any:
        """
        Smart auto-resolver - handles ANY value type
        
        - Primitives (int, float, bool, None) → pass through
        - Collections (list, dict, etc.) → pass through
        - Functions → pass through
        - Classes → instantiate via container
        - FQN strings → resolve via container
        - Simple class names → check autoloader registry
        - Plain strings → pass through
        """
        # Primitives
        if value is None or isinstance(value, (int, float, bool, list, dict, tuple, set)):
            return value
        
        # Functions (not classes)
        if callable(value) and not inspect.isclass(value):
            return value
        
        # Classes - instantiate
        if inspect.isclass(value):
            try:
                return self.container.make(value)
            except:
                return value
        
        # Strings - resolve if FQN, binding, or in autoloader
        if isinstance(value, str):
            # Check if it's a registered binding
            if value in self.container._bindings:
                try:
                    return self.container.make(value)
                except:
                    pass
            
            # Check if it looks like an FQN (has dots)
            elif '.' in value:
                try:
                    return self.container.make(value)
                except:
                    pass
            
            # Check autoloader's simple registry (e.g., "Home" -> app.controllers.Home)
            elif hasattr(self.container, '_autoloader') and self.container._autoloader:
                if hasattr(self.container._autoloader, '_registry_simple'):
                    if value in self.container._autoloader._registry_simple:
                        try:
                            return self.container.make(value)
                        except:
                            pass
        
        # Everything else - pass through
        return value
    
    # ========== DEBUG ==========
    
    def dump(self) -> Dict:
        """Dump state for debugging"""
        return {
            'registry': self.get_registry(),
            'total_services': len(self._registry),
            'singletons': self.get_singletons(),
            'factories': self.get_factories(),
            'container_state': self.container.dump()
        }
    
    def print_registry(self) -> None:
        """Pretty print registry"""
        print("=" * 70)
        print("SERVICE REGISTRY")
        print("=" * 70)
        
        for abstract, service in self._registry.items():
            if not service['registered']:
                continue
            
            print(f"\n{abstract}")
            print(f"  Type: {service['type']}")
            print(f"  Concrete: {service['concrete']}")
            if service['params']:
                print(f"  Params: {list(service['params'].keys())}")
            if service['tags']:
                print(f"  Tags: {', '.join(service['tags'])}")
            if service['description']:
                print(f"  Description: {service['description']}")
        
        print("\n" + "=" * 70)


