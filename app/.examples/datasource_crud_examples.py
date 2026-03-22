"""app.examples.datasource_crud_examples - Full CRUD Examples Using Models

Comprehensive examples showing read/write operations through Models.
Models handle state management and call datasources internally.

IMPORTANT: Always access data through Models, never directly through datasources.
This ensures proper state management, change tracking, and persistence.

New Unified CRUD Format:
    Read all:        {"collection": []}
    Read with cols:  {"collection": ["col1", "col2"]}
    Read with WHERE: {"collection": ["col": value, "col2"]}
    Create:          {"collection": [{"id": 1, "name": "Alice"}]}
    Update:          {"collection": ["id": 1, "name": "updated_name"]}
    Delete:          {"collection": ["id": 1]}

Changelog:
    - 2026-01-30: Created comprehensive CRUD examples for all datasources.
    - 2026-01-30: Updated to use Models instead of direct datasource access.
        * Models handle state management and persistence
        * Datasources are internal implementation details only
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', ".."))

from app.models.AbstractModel import AbstractModel
from lib.db.datasources.json_datasource import JsonDatasource
from lib.db.datasources.file_datasource import FileDatasource


# ============================================================================
# User Model - Concrete Implementation
# ============================================================================

class UserModel(AbstractModel):
    """Concrete User model."""
    
    def get_name(self) -> str:
        return self.get('name') or 'Unknown'
    
    def set_name(self, name: str) -> None:
        self.set('name', name)
    
    def get_email(self) -> str:
        return self.get('email') or ''
    
    def set_email(self, email: str) -> None:
        self.set('email', email)


# ============================================================================
# Product Model
# ============================================================================

class ProductModel(AbstractModel):
    """Concrete Product model."""
    
    def get_name(self) -> str:
        return self.get('name') or 'Unknown'
    
    def set_name(self, name: str) -> None:
        self.set('name', name)
    
    def get_price(self) -> float:
        return self.get('price') or 0.0
    
    def set_price(self, price: float) -> None:
        self.set('price', price)


# ============================================================================
# EXAMPLE 1: JsonDatasource (Single JSON File) via Model
# ============================================================================

def example_json_datasource_crud():
    """Full CRUD example using Model with JsonDatasource."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Model + JsonDatasource (Single JSON File)")
    print("="*70)
    
    # Initialize datasource (internal to model)
    json_ds = JsonDatasource('/tmp/users_json.json', read_only=False)
    
    # ---- CREATE ----
    print("\n[CREATE] Adding users through model...")
    user1 = UserModel(json_ds, {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'})
    user1.push()  # Save to datasource
    
    user2 = UserModel(json_ds, {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'})
    user2.push()
    
    user3 = UserModel(json_ds, {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'})
    user3.push()
    print("✓ Created 3 users through models")
    
    # ---- READ ----
    print("\n[READ] Reading users from model...")
    user_read = UserModel(json_ds)
    user_read.pull()  # Load from datasource
    all_data = user_read.get_all()
    print(f"✓ Retrieved: {all_data}")
    
    # ---- UPDATE ----
    print("\n[UPDATE] Updating Alice's email through model...")
    user1.set_email('alice.updated@example.com')
    print(f"Before push: {user1.get('email')}")
    user1.push()  # Save changes
    print(f"After push: {user1.get('email')}")
    
    # ---- STATE MANAGEMENT ----
    print("\n[STATE MANAGEMENT] Testing model state snapshots...")
    user1.set_name('Alice Smith')
    print(f"Modified name: {user1.get_name()}")
    user1.push_state('before_email_change')
    user1.set_email('alice.new@example.com')
    print(f"New email: {user1.get_email()}")
    user1.pop_state()
    print(f"After pop (back to before_email_change): {user1.get_email()}")


# ============================================================================
# EXAMPLE 2: FileDatasource - Directory Mode via Model
# ============================================================================

def example_file_datasource_directory_crud():
    """Full CRUD example using Model with FileDatasource (directory mode)."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Model + FileDatasource - Directory Mode")
    print("="*70)
    
    # Initialize datasource (internal to model)
    file_ds = FileDatasource('/tmp/products_files_dir', read_only=False)
    
    # ---- CREATE ----
    print("\n[CREATE] Adding products through model...")
    prod1 = ProductModel(file_ds, {'id': 101, 'name': 'Laptop', 'price': 999})
    prod1.push()
    
    prod2 = ProductModel(file_ds, {'id': 102, 'name': 'Mouse', 'price': 25})
    prod2.push()
    
    prod3 = ProductModel(file_ds, {'id': 103, 'name': 'Keyboard', 'price': 75})
    prod3.push()
    print("✓ Created 3 products through models (files in /tmp/products_files_dir/)")
    
    # ---- READ ----
    print("\n[READ] Reading products from model...")
    prod_read = ProductModel(file_ds)
    prod_read.pull()
    all_data = prod_read.get_all()
    print(f"✓ Retrieved {len(all_data)} products")
    
    # ---- UPDATE ----
    print("\n[UPDATE] Updating Laptop price through model...")
    prod1.set_price(899)
    print(f"Before push: {prod1.get_price()}")
    prod1.push()
    print(f"After push: {prod1.get_price()}")
    
    # ---- STATE SNAPSHOTS ----
    print("\n[STATE SNAPSHOTS] Testing model snapshots...")
    prod2.push_state('original_price')
    prod2.set_price(20)
    print(f"Discounted price: {prod2.get_price()}")
    prod2.pop_state()
    print(f"Back to original: {prod2.get_price()}")


# ============================================================================
# EXAMPLE 3: FileDatasource - Single File Mode via Model
# ============================================================================

def example_file_datasource_single_file_crud():
    """Full CRUD example using Model with FileDatasource (single file mode)."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Model + FileDatasource - Single File Mode")
    print("="*70)
    
    # Initialize datasource (internal to model)
    file_ds = FileDatasource('/tmp/inventory.json', read_only=False)
    
    # ---- CREATE ----
    print("\n[CREATE] Adding inventory items through model...")
    item1 = ProductModel(file_ds, {'id': 1001, 'name': 'Widget A', 'price': 100})
    item1.push()
    
    item2 = ProductModel(file_ds, {'id': 1002, 'name': 'Widget B', 'price': 50})
    item2.push()
    
    item3 = ProductModel(file_ds, {'id': 1003, 'name': 'Widget C', 'price': 75})
    item3.push()
    print("✓ Created 3 items through models (all in /tmp/inventory.json)")
    
    # ---- READ ----
    print("\n[READ] Reading items from model...")
    item_read = ProductModel(file_ds)
    item_read.pull()
    all_data = item_read.get_all()
    print(f"✓ Retrieved {len(all_data)} items")
    
    # ---- UPDATE ----
    print("\n[UPDATE] Updating Widget B price...")
    item2.set_price(45)
    item2.push()
    print(f"✓ Updated to {item2.get_price()}")
    
    # ---- AUTO-SNAPSHOTS ----
    print("\n[AUTO-SNAPSHOTS] Model auto-creates snapshots on mutations...")
    print(f"Current price: {item3.get_price()}")
    item3.set_price(70)  # Auto-snapshot created
    print(f"After set_price: {item3.get_price()}")
    print(f"Saved snapshots: {len(item3._states)}")


# ============================================================================
# KEY DIFFERENCES: Direct vs Model Access
# ============================================================================

def show_architecture_reference():
    """Display the correct architecture pattern."""
    print("\n" + "="*70)
    print("ARCHITECTURE REFERENCE: Models vs Datasources")
    print("="*70)
    
    print("\n❌ WRONG - Direct datasource access:")
    print("  ds = JsonDatasource(...)")
    print("  ds.create({'users': [{'id': 1, 'name': 'Alice'}]})")
    print("  data = ds.read({'users': []})")
    print("  ds.update({'users': ['id': 1, 'name': 'Bob']})")
    print("  ds.delete({'users': ['id': 1]})")
    print("\n  ⚠️  No state management, no change tracking, no undo/redo")
    
    print("\n✅ CORRECT - Access through Models:")
    print("  ds = JsonDatasource(...)")
    print("  user = UserModel(ds, {'id': 1, 'name': 'Alice'})")
    print("  user.push()  # Save to datasource")
    print("  user.set_name('Bob')  # Auto-snapshot created")
    print("  user.push()  # Update in datasource")
    print("  user.pop_state()  # Undo last change")
    print("\n  ✅ State management, snapshots, undo/redo, all working!")
    
    print("\nModel Benefits:")
    print("  - Automatic state snapshots on mutations (set_*)")
    print("  - Named restore points (push_state / pop_state)")
    print("  - Typed attribute access (get_name, set_email, etc)")
    print("  - Datasource abstraction (swap backends easily)")
    print("  - Change tracking and undo/redo")


if __name__ == '__main__':
    show_architecture_reference()
    example_json_datasource_crud()
    example_file_datasource_directory_crud()
    example_file_datasource_single_file_crud()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)
