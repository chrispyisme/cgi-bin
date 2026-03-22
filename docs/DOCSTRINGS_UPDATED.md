# Documentation Updates - January 30, 2026

## Summary

All new model/datasource files and relevant framework files have been updated with comprehensive docstrings following Python conventions.

## CRUD Input Format Changes (2026-01-30)

### New Unified Input Format

All CRUD operations now use a single, consistent input format:

```python
{"collection_name": [specification_array]}
```

**Examples:**
- Read all: `{"users": []}`
- Read with columns: `{"users": ["id", "name", "email"]}`
- Read with WHERE: `{"users": {"id": 1}}` (returns matching records)
- Read with columns: `{"users": ["id", "name"]}` (returns only those fields)
- Create/Update/Delete: `{"users": [{"id": 1, "name": "Alice"}]}`

This replaces the previous format with separate `query`, `filter_`, `where`, and `params` parameters. Operator-based WHERE conditions are supported using nested dicts, e.g. `{"users": {"age": {"gt": 18}, "name": {"starts": "Chr"}}}`.

## Files Updated

### New Model & Datasource Files

#### Model Layer
- **app/models/contracts.py**
  - Module docstring with origin (PHP HTTPStack v2), changelog, and usage examples
  - Class docstrings for `Attributes` and `AttributeState` contracts
  - Method docstrings for all abstract methods

- **app/models/base.py**
  - Module docstring with origin, usage patterns, and best practices
  - Class docstring explaining dict-backed attribute storage
  - Thread-safety notes
  - Method docstrings for all attribute operations

- **app/models/model.py**
  - Comprehensive module docstring with usage examples
  - Detailed class docstring covering:
    - Automatic state snapshots on mutations
    - Named state restore points
    - Datasource integration
  - Method docstrings for state and datasource operations

#### Datasource Layer

- **app/datasources/contracts.py**
  - Module docstring with origin and custom implementation examples
  - Class docstrings for `CrudInterface` and `DatasourceInterface`
  - Clear separation of concerns (CRUD vs push/pull)

- **app/datasources/abstract.py**
  - Module docstring with origin and custom datasource example
  - Class docstring listing common features:
    - Read-only mode enforcement
    - Data caching
    - Standardized interface

- **app/datasources/json_datasource.py**
  - Comprehensive module docstring with:
    - File format documentation
    - Best use cases
    - NOT recommended scenarios
  - Usage examples (read-only vs writable modes)
  - Class docstring with threading notes

- **app/datasources/file_datasource.py**
  - Detailed module docstring covering:
    - Directory mode vs single-file mode
    - Detailed structure examples
    - Best use cases for each mode
  - Usage examples for both modes
  - Recommended dataset sizes

- **app/datasources/db_datasource.py**
  - Module docstring with:
    - Database interface expectations
    - Complete method signatures
    - Best practices (transactions, scaling)
  - Usage examples with Database integration
  - Row context management notes

#### Examples
- **app/examples/model_datasource_example.py**
  - Module docstring documenting:
    - 4 example categories
    - Key patterns demonstrated
    - How to run examples
  - Changelog tracking creation date

### Updated Framework Files

#### Routing Layer

- **lib/routing/Route.py**
  - Module docstring with:
    - Pattern matching types (parameter, wildcard, regex)
    - Handler parameter explanation
    - Integration with Container
  - Usage example showing parameter matching
  - Changelog with feature additions

- **lib/routing/Router.py**
  - Comprehensive module docstring with:
    - Feature list
    - Handler format examples
    - Complete usage example with DI
    - Middleware explanation
  - Detailed DI integration notes
  - Changelog tracking DI improvements

#### DI Container Layer

- **lib/di/Container.py**
  - Extensive module docstring covering:
    - Feature list with 9 capabilities
    - Complete usage patterns
    - Key concepts section (Bindings, DI Autowiring, Override Parameters, Autoloader)
    - Type-object DI explanation
    - Module-qualified keys benefit
  - Class docstring explaining:
    - Purpose as core DI system
    - Module-qualified key usage
    - Type object preference
  - Changelog tracking major improvements

## Documentation Standards Applied

### Module-Level Docstrings
All files include:
1. **Title**: Descriptive name with component scope
2. **Description**: What the module does
3. **Origin**: Where code came from (PHP HTTPStack v2)
4. **Changelog**: Version history with dates
5. **Usage**: Complete code examples
6. **Key Concepts**: For complex modules

### Class Docstrings
All classes include:
1. **Short Summary**: One-line description
2. **Detailed Description**: What the class does and how
3. **Special Notes**: Threading, performance, limitations
4. **Usage Example**: For most classes

### Method Docstrings
All public methods include:
1. **Description**: What it does
2. **Args**: Parameter descriptions with types
3. **Returns**: Return type and value description
4. **Raises**: Exceptions that may be raised

## Benefits

1. **IDE Integration**: Autocomplete and inline documentation
2. **API Discovery**: Easy to understand public interfaces
3. **Maintenance**: Clear intent and usage patterns
4. **Type Hints**: Combined with existing type annotations
5. **DCI Documentation**: Dependency Injection patterns explained
6. **Migration Context**: PHP HTTPStack v2 origins documented

## Navigation

- Overview: See [app/models/README.md](app/models/README.md)
- Examples: See [app/examples/model_datasource_example.py](app/examples/model_datasource_example.py)
- DI Guide: Check Container and Router docstrings for integration patterns

## Next Steps

For enhanced developer experience:
1. Generate HTML documentation: `pydoc -w app.models lib.db.datasources lib.routing lib.di`
2. IDE hover documentation will now work automatically
3. Consider adding type stub files (.pyi) for complex types
4. Enable automatic docstring generation in CI/CD pipeline

---

**Updated**: January 30, 2026
**Status**: Complete - All 14 files documented
