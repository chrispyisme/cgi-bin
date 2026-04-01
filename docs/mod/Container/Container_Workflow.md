# Container.py - Version 1.0 Complete Workflow

## 🏗️ **Architecture Overview**

This Container implements a **Service Locator + Dependency Injection** pattern with the following core concepts:

1. **Service Registration** - Bind services with different lifetimes
2. **Dependency Resolution** - Automatically inject dependencies using type hints
3. **Autowiring** - Constructor parameter matching
4. **FQN Support** - Fully Qualified Names for collision prevention
5. **Factory Pattern** - Custom instantiation logic

---

## 📦 **Core API Reference (V1)**

### **Initialization**
```python
from lib.di.Container import Container

# Create container
container = Container()
```

---

## 🎯 **1. SERVICE BINDING METHODS**

### **1.1 Singleton Binding** (One instance per container)
```python
# Method 1: Direct instance
container.singleton('database', Database(host='localhost'))

# Method 2: Class reference (lazy loading)
container.singleton(Database, Database)

# Method 3: With parameters
container.singleton('cache', RedisCache, host='127.0.0.1', port=6379)
```

**Behavior:**
- Instance created on first `make()` call
- Same instance returned for subsequent calls
- `force_build=True` ignores singleton cache

### **1.2 Factory Binding** (New instance each time)
```python
# Method 1: Class
container.factory('user_model', User)

# Method 2: Callable factory function
container.factory('logger', lambda: Logger(level='INFO'))

# Method 3: With parameters
container.factory('mailer', SMTPMailer, host='smtp.gmail.com')
```

**Behavior:**
- New instance created on every `make()` call
- Parameters can be overridden at resolution time

### **1.3 Direct Binding** (Existing object)
```python
# Bind existing instance
config = {'debug': True}
container.bind('config', config)

# Bind function
container.bind('validator', validate_email)
```

### **1.4 Aliases** (Short names for services)
```python
# Create alias for convenience
container.alias('db', Database)
container.alias('db', 'app.database.Database')  # String FQN works too

# Usage
db1 = container.make('db')  # Resolves to Database
db2 = container.make(Database)  # Same result
```

---

## 🔍 **2. SERVICE RESOLUTION**

### **2.1 Basic Resolution**
```python
# Resolve singleton (cached)
db = container.make('database')

# Resolve factory (new instance each time)
user = container.make('user_model')

# Force new instance (ignore singleton cache)
fresh_db = container.make('database', force_build=True)
```

### **2.2 Constructor Injection with Type Hints**
```python
# Service with dependencies
class UserService:
    def __init__(self, database: Database, logger: Logger):
        self.db = database
        self.logger = logger

# Automatic resolution
service = container.make(UserService)
# Container automatically injects Database and Logger instances
```

**Type Hint Resolution Order:**
1. Check `override_params` passed to `make()`
2. Check container bindings for the type
3. Use default parameter value if available
4. Raise `AppException` if unresolved

### **2.3 Parameter Overrides**
```python
# Binding with default params
container.bind('mailer', SMTPMailer, 
               host='smtp.gmail.com',
               port=587)

# Override at resolution
mailer = container.make('mailer',
                       host='custom.smtp.com',  # Override
                       timeout=30)  # Additional param
```

### **2.4 FQN Resolution** (Fully Qualified Names)
```python
# Resolve by module path
Request = container.resolve('lib.http.Request')

# Build instance from FQN
request = container.build('lib.http.Request', {'path': '/'})

# Using autoloader fallback (if configured)
controller = container.resolve('app.controllers.UserController')
```

---

## 🛠️ **3. ADVANCED PATTERNS**

### **3.1 Factory Functions with Container Access**
```python
def create_service(container, config=None):
    """Factory that needs container access"""
    db = container.make(Database)
    return ComplexService(db, config)

container.factory('complex', create_service, config={'retries': 3})
```

**Note:** Factory functions with `container`, `c`, or `cont` as first parameter receive container instance.

### **3.2 Callable Resolution** (For Controllers/Actions)
```python
class UserController:
    def __init__(self, user_service: UserService):
        self.service = user_service
    
    def index(self, request: Request):
        return self.service.get_all()

# Method 1: Array style
result = container.call([UserController, 'index'], request=req)

# Method 2: String style
result = container.call('UserController@index', request=req)

# Method 3: Manual callable
handler = container.make_callable([UserController, 'index'])
result = handler(request=req)
```

### **3.3 Autoloader Integration**
```python
from lib.di.Autoloader import Autoloader

autoloader = Autoloader()
autoloader.register_paths(['app/controllers', 'app/models'])
autoloader.load()

container.set_autoloader(autoloader)

# Now FQN resolution uses autoloader as fallback
UserModel = container.resolve('app.models.User')  # No explicit import needed
```

---

## 📝 **4. PROPERTIES SYSTEM**

```python
# Store configuration
container.add_property('debug', True)
container.add_property('version', '1.0.0')

# Retrieve
debug = container.get_property('debug', default=False)

# Check existence
if container.has_property('api_key'):
    key = container.get_property('api_key')

# Get all properties
all_props = container.get_props()

# Remove property
container.remove_property('temp_value')
```

---

## 🔧 **5. DEBUGGING & INSPECTION**

### **5.1 Container Introspection**
```python
# List all bindings
bindings = container.get_bindings()  # ['Database', 'Logger', ...]

# List singleton services
singletons = container.get_singletons()  # ['Database', 'Config']

# List factory services
factories = container.get_factories()  # ['UserModel', 'Request']

# Get instantiated singletons
instances = container.get_instances()  # {'Database': <instance>, ...}

# Detailed service info
info = container.get_service_info()
# [
#   {'name': 'Database', 'type': 'singleton', 'instantiated': True},
#   {'name': 'UserModel', 'type': 'factory', 'instantiated': None}
# ]

# Complete dump
dump = container.dump()
```

### **5.2 Service Validation**
```python
# Check if service exists
if container.has_binding('Database'):
    db = container.make('Database')

# Check service type
if container.is_singleton('Database'):
    print("Database is singleton")
```

---

## 💡 **6. PRACTICAL EXAMPLES**

### **Example 1: Web Application Setup**
```python
def setup_app_container():
    """Configure container for a web app"""
    container = Container()
    
    # Configuration
    container.add_property('env', os.getenv('APP_ENV', 'production'))
    container.add_property('debug', os.getenv('DEBUG', 'false') == 'true')
    
    # Core infrastructure (singletons)
    container.singleton('database', Database, 
                       host=os.getenv('DB_HOST'),
                       database=os.getenv('DB_NAME'))
    
    container.singleton('cache', RedisCache,
                       url=os.getenv('REDIS_URL'))
    
    container.singleton('session', SessionManager,
                       secret=os.getenv('SESSION_SECRET'))
    
    # Business services
    container.singleton('user_service', UserService)
    container.singleton('auth_service', AuthService)
    
    # HTTP services (factories - new per request)
    container.factory('request', Request)
    container.factory('response', Response)
    
    # Aliases for convenience
    container.alias('db', 'database')
    container.alias('users', 'user_service')
    
    return container
```

### **Example 2: Dependency Chain**
```python
# Service Dependencies:
# Controller → Service → Repository → Database

class UserRepository:
    def __init__(self, database: Database):
        self.db = database

class UserService:
    def __init__(self, repository: UserRepository, logger: Logger):
        self.repo = repository
        self.logger = logger

class UserController:
    def __init__(self, service: UserService):
        self.service = service
    
    def get_user(self, user_id: int):
        return self.service.find(user_id)

# Registration
container.singleton(Database, Database)
container.singleton(UserRepository, UserRepository)
container.singleton(UserService, UserService)
container.singleton(UserController, UserController)

# Automatic resolution chain
controller = container.make(UserController)
# Container resolves: UserController → UserService → UserRepository → Database
```

### **Example 3: Testing with Mocks**
```python
class TestContainer(Container):
    """Container for testing with mocked dependencies"""
    
    def __init__(self):
        super().__init__()
        
        # Mock external services
        self.singleton('database', MockDatabase)
        self.singleton('payment_gateway', MockPaymentGateway)
        
        # Real service to test
        self.singleton('order_service', OrderService)
        
        # Test configuration
        self.add_property('testing', True)

# Usage in tests
def test_order_service():
    container = TestContainer()
    service = container.make('order_service')
    
    # service has mocked dependencies
    result = service.process(test_order)
    assert result.success
```

---

## ⚠️ **7. COMMON PITFALLS & SOLUTIONS**

### **Problem 1: Circular Dependencies**
```python
# ❌ Circular: ServiceA → ServiceB → ServiceA
class ServiceA:
    def __init__(self, b: ServiceB): ...

class ServiceB:
    def __init__(self, a: ServiceA): ...

# ✅ Solution: Use property/setter injection
class ServiceA:
    def __init__(self):
        self.b = None  # Set later
    
    def set_b(self, b: ServiceB):
        self.b = b

# Manually wire after creation
a = ServiceA()
b = ServiceB(a)
a.set_b(b)
```

### **Problem 2: Missing Type Hints**
```python
# ❌ Won't work - no type hint
class Service:
    def __init__(self, database):  # No type hint
        self.db = database

# ✅ Add type hints
class Service:
    def __init__(self, database: Database):
        self.db = database
```

### **Problem 3: Optional Dependencies**
```python
# ✅ Use Optional type hint with default
class Service:
    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or NullCache()
```

---

## 🚀 **8. QUICKSTART TEMPLATE**

```python
from lib.di.Container import Container

# 1. Create container
container = Container()

# 2. Add configuration
container.add_property('debug', True)
container.add_property('app_name', 'MyApp')

# 3. Register core services (singletons)
container.singleton('database', Database, host='localhost')
container.singleton('logger', Logger, level='INFO')
container.singleton('config', ConfigLoader().load())

# 4. Register business services
container.singleton('user_service', UserService)
container.singleton('auth_service', AuthService)

# 5. Register factories (transient)
container.factory('request', HttpRequest)
container.factory('response', HttpResponse)

# 6. Create aliases
container.alias('db', 'database')
container.alias('users', 'user_service')

# 7. Use services
db = container.make('db')  # Singleton
user_service = container.make('users')  # Singleton
request = container.make('request')  # New instance

# 8. Automatic DI
class AppController:
    def __init__(self, user_service: UserService, logger: Logger):
        self.user_service = user_service
        self.logger = logger

controller = container.make(AppController)  # Dependencies auto-injected
```

---

## 📋 **Version 1.0 Feature Summary**

| Feature | Status | Description |
|---------|--------|-------------|
| Singleton Binding | ✅ | One instance per container |
| Factory Binding | ✅ | New instance each call |
| Constructor DI | ✅ | Automatic via type hints |
| Parameter Overrides | ✅ | At binding and resolution |
| FQN Support | ✅ | Module.Class names |
| Aliases | ✅ | Short names for services |
| Autoloader Integration | ✅ | Class discovery fallback |
| Callable Resolution | ✅ | Controller/action invocation |
| Properties System | ✅ | Key-value storage |
| Debug & Inspection | ✅ | Service listing and info |
| Force Build | ✅ | Ignore singleton cache |
| Container-aware Factories | ✅ | Pass container to factories |

---

## 🔮 **What's Next for Version 2?**

Potential enhancements:
1. **Interface binding** - Bind implementations to interfaces
2. **Scoped lifetimes** - Request-scoped services
3. **Decorator support** - `@inject` decorators
4. **Configuration files** - YAML/JSON service definitions
5. **Service tags** - Group and filter services
6. **Compiled container** - Performance optimization
7. **Event hooks** - Pre/post resolution events
8. **Lazy loading** - Proxy objects for heavy services

---

This Container v1 provides a solid foundation for dependency injection in Python applications. Start with simple singleton bindings and gradually incorporate more advanced features as needed. The type-hint based autowiring eliminates much of the manual configuration while maintaining clarity and testability.
