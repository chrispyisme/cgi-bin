"""app.examples.model_datasource_example - Model & Datasource Usage Examples

Demonstrates practical usage patterns for the Model/Datasource architecture:
    1. JsonDatasource: Single JSON file persistence
    2. FileDatasource: Directory-based file storage
    3. State Management: Auto-push and pop_state for undo
    4. Direct CRUD: Using datasources without models

Origin:
    Created to accompany PHP HTTPStack v2 Model/Datasource conversion.

Usage:
    Run all examples:
        python app/examples/model_datasource_example.py

Examples Included:
    - Example 1: JsonDatasource with basic CRUD
    - Example 2: FileDatasource with directory storage
    - Example 3: State management with automatic snapshots
    - Example 4: Direct CRUD operations without models

Key Patterns Demonstrated:
    - Model initialization with datasource
    - Attribute get/set operations
    - Automatic state snapshots on mutations
    - Manual state restore points with push_state
    - Undo with pop_state
    - Datasource push/pull for sync
    - Read-only vs. writable datasources
    - Query filtering on CRUD reads

Changelog:
    - 2026-01-30: Created with 4 comprehensive runnable examples.
    - 2026-01-30: Updated CRUD examples to use new unified input format:
        * Read all: {"collection": []}
        * Read with columns: {"collection": ["col1", "col2"]}
        * Read with WHERE: {"collection": ["col": value, "col2", "col3"]}
        * Create/Update/Delete follow same {"collection": [...]} format
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', ".."))

from app.models.AbstractModel import AbstractModel
from lib.db.datasources.json_datasource import JsonDatasource
from lib.db.datasources.file_datasource import FileDatasource


# Example 1: User model with JSON datasource
class UserModel(AbstractModel):
    """Concrete user model implementation."""
    
    def get_username(self) -> str:
        return self.get('username') or 'Anonymous'
    
    def get_email(self) -> str:
        return self.get('email') or ''
    
    def set_username(self, username: str) -> None:
        self.set('username', username)
    
    def set_email(self, email: str) -> None:
        self.set('email', email)


# Example 2: Simple usage
def example_json_datasource():
    """Example: Use JSON datasource."""
    print("=== Example 1: JSON Datasource ===")
    
    # Create a JSON datasource (writable)
    json_ds = JsonDatasource('/tmp/users.json', read_only=False)
    
    # Initialize with some data
    json_ds.create({'id': 1, 'username': 'alice', 'email': 'alice@example.com'})
    json_ds.create({'id': 2, 'username': 'bob', 'email': 'bob@example.com'})
    
    # Create a model with the datasource
    user_model = UserModel(json_ds, {'id': 1, 'username': 'alice', 'email': 'alice@example.com'})
    
    print(f"User: {user_model.get_username()} ({user_model.get_email()})")
    
    # Modify and save
    user_model.set_username('Alice Updated')
    user_model.push()  # Save to datasource
    
    print(f"Updated: {user_model.get_username()}")
    
    # State management
    user_model.set_email('new@example.com')
    print(f"Email before pop: {user_model.get_email()}")
    user_model.pop_state()
    print(f"Email after pop: {user_model.get_email()}")


def example_file_datasource():
    """Example: Use file datasource."""
    print("\n=== Example 2: File Datasource ===")
    
    # Create a file datasource in directory mode
    file_ds = FileDatasource('/tmp/users_data', read_only=False)
    
    # Create records
    file_ds.create({'id': 1, 'username': 'charlie', 'email': 'charlie@example.com'})
    
    # Create a model
    user_model = UserModel(file_ds)
    user_model.set('id', 2)
    user_model.set_username('David')
    user_model.set_email('david@example.com')
    
    print(f"User: {user_model.get_username()} ({user_model.get_email()})")
    
    # Push to save
    user_model.push()
    
    # Pull to reload
    user_model.pull()
    print(f"After pull: {user_model.get_username()}")


def example_state_management():
    """Example: State management with push/pop."""
    print("\n=== Example 3: State Management ===")
    
    json_ds = JsonDatasource('/tmp/states.json', read_only=False)
    model = UserModel(json_ds, {'id': 1, 'status': 'active'})
    
    print(f"Initial: {model.get('status')}")
    
    # Change 1: changes status and auto-pushes state
    model.set('status', 'inactive')
    print(f"After set: {model.get('status')}")
    
    # List available states
    states = model._states
    print(f"Saved states: {list(states.keys())}")
    
    # Pop back to previous state
    model.pop_state()
    print(f"After pop: {model.get('status')}")


def example_datasource_crud():
    """Example: Direct CRUD operations on datasource."""
    print("\n=== Example 4: Direct Datasource CRUD ===")
    
    json_ds = JsonDatasource('/tmp/crud_example.json', read_only=False)
    
    # Create - using new format: {"collection": [record_data]}
    json_ds.create({"products": [{'id': 1, 'name': 'Product A', 'price': 100}]})
    json_ds.create({"products": [{'id': 2, 'name': 'Product B', 'price': 200}]})
    
    # Read all - using new format: {"collection": []}
    all_records = json_ds.read({"products": []})
    print(f"All records: {all_records}")
    
    # Read with column selection - using new format: {"collection": ["col1", "col2"]}
    selected = json_ds.read({"products": ["id", "name"]})
    print(f"Products (id, name only): {selected}")
    
    # Read with WHERE clause - using new format: {"collection": {"col": value}}
    expensive = json_ds.read({"products": {"price": 200}})
    # Extract names from matched records
    expensive_names = [item.get('name') for item in expensive.values()]
    print(f"Products with price 200 (name): {expensive_names}")

    # Update - using new format: {"collection": {"col": value, "new_col": new_value}}
    json_ds.update({"products": {"id": 1, "price": 150}})
    print(f"After update: {json_ds.read({'products': {'id': 1}})}")

    # Delete - using new format: {"collection": {"col": value}}
    json_ds.delete({"products": {"id": 2}})
    print(f"After delete: {json_ds.read({'products': []})}")


if __name__ == '__main__':
    example_json_datasource()
    example_file_datasource()
    example_state_management()
    example_datasource_crud()
