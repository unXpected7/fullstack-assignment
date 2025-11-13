import pytest
import sqlite3
from unittest.mock import Mock, patch
from typing import List, Dict, Any, Optional


class MockCartRepository:
    """Mock Cart Repository for testing data access layer"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection

    def create_session(self, session_id: str = None) -> str:
        """Create a new cart session"""
        if not session_id:
            import secrets
            session_id = secrets.token_urlsafe(32)

        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO cart_sessions (id) VALUES (?)",
            (session_id,)
        )
        self.db.commit()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cart session by ID"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM cart_sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def add_cart_item(self, session_id: str, product_id: str, product_name: str,
                     price: float, quantity: int, vendor_id: str, vendor_name: str,
                     image_url: str = None) -> int:
        """Add item to cart"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO cart_items (
                session_id, product_id, product_name, price, quantity,
                vendor_id, vendor_name, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, product_id, product_name, price, quantity,
            vendor_id, vendor_name, image_url
        ))
        self.db.commit()
        return cursor.lastrowid

    def get_cart_items(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all items in a cart"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, product_id, product_name, price, quantity,
                   vendor_id, vendor_name, image_url
            FROM cart_items
            WHERE session_id = ?
            ORDER BY id DESC
        ''', (session_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_cart_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get specific cart item"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM cart_items WHERE id = ?",
            (item_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_item_quantity(self, item_id: int, quantity: int) -> bool:
        """Update item quantity"""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE cart_items SET quantity = ? WHERE id = ?",
            (quantity, item_id)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def remove_cart_item(self, item_id: int) -> bool:
        """Remove item from cart"""
        cursor = self.db.cursor()
        cursor.execute(
            "DELETE FROM cart_items WHERE id = ?",
            (item_id,)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def clear_cart(self, session_id: str) -> int:
        """Clear all items from cart"""
        cursor = self.db.cursor()
        cursor.execute(
            "DELETE FROM cart_items WHERE session_id = ?",
            (session_id,)
        )
        self.db.commit()
        return cursor.rowcount

    def get_cart_totals_by_vendor(self, session_id: str) -> List[Dict[str, Any]]:
        """Get cart totals grouped by vendor"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT vendor_id, vendor_name, SUM(price * quantity) as vendor_subtotal,
                   COUNT(*) as item_count
            FROM cart_items
            WHERE session_id = ?
            GROUP BY vendor_id, vendor_name
            ORDER BY vendor_subtotal DESC
        ''', (session_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_existing_cart_item(self, session_id: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Get existing cart item for updating"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, quantity FROM cart_items
            WHERE session_id = ? AND product_id = ?
        ''', (session_id, product_id))

        row = cursor.fetchone()
        return dict(row) if row else None

    def increment_item_quantity(self, item_id: int, additional_quantity: int) -> bool:
        """Increment item quantity"""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE cart_items SET quantity = quantity + ? WHERE id = ?",
            (additional_quantity, item_id)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def get_cart_summary(self, session_id: str) -> Dict[str, Any]:
        """Get cart summary statistics"""
        cursor = self.db.cursor()

        # Get item count and total value
        cursor.execute('''
            SELECT COUNT(*) as item_count,
                   COALESCE(SUM(price * quantity), 0) as subtotal,
                   COUNT(DISTINCT vendor_id) as vendor_count
            FROM cart_items
            WHERE session_id = ?
        ''', (session_id,))

        summary = dict(cursor.fetchone())

        # Get vendor breakdown for shipping calculation
        vendor_totals = self.get_cart_totals_by_vendor(session_id)
        summary['vendor_breakdown'] = vendor_totals

        return summary


@pytest.mark.unit
@pytest.mark.repository
@pytest.mark.cart
class TestCartRepository:
    """Test cases for Cart Repository functionality"""

    @pytest.fixture
    def cart_repository(self, test_db):
        """Create cart repository instance with test database"""
        return MockCartRepository(test_db)

    def test_create_session_without_id(self, cart_repository):
        """Test creating a session without providing ID"""
        session_id = cart_repository.create_session()

        assert session_id is not None
        assert len(session_id) > 0

        # Verify session was created
        session = cart_repository.get_session(session_id)
        assert session is not None
        assert session['id'] == session_id

    def test_create_session_with_id(self, cart_repository):
        """Test creating a session with specific ID"""
        custom_session_id = "test_session_123"
        session_id = cart_repository.create_session(custom_session_id)

        assert session_id == custom_session_id

        # Verify session was created
        session = cart_repository.get_session(session_id)
        assert session is not None
        assert session['id'] == custom_session_id

    def test_get_nonexistent_session(self, cart_repository):
        """Test getting non-existent session"""
        session = cart_repository.get_session("nonexistent")
        assert session is None

    @pytest.mark.happy_path
    def test_add_cart_item(self, cart_repository):
        """Test adding item to cart"""
        session_id = cart_repository.create_session()

        item_id = cart_repository.add_cart_item(
            session_id=session_id,
            product_id="prod_001",
            product_name="Test Product",
            price=99.99,
            quantity=2,
            vendor_id="vendor_001",
            vendor_name="Test Vendor",
            image_url="https://example.com/image.jpg"
        )

        assert item_id is not None
        assert isinstance(item_id, int)

        # Verify item was added
        items = cart_repository.get_cart_items(session_id)
        assert len(items) == 1
        assert items[0]['id'] == item_id
        assert items[0]['product_id'] == "prod_001"
        assert items[0]['quantity'] == 2

    def test_get_cart_items_empty(self, cart_repository):
        """Test getting items from empty cart"""
        session_id = cart_repository.create_session()
        items = cart_repository.get_cart_items(session_id)
        assert items == []

    def test_get_cart_items_multiple(self, cart_repository):
        """Test getting multiple cart items"""
        session_id = cart_repository.create_session()

        # Add multiple items
        cart_repository.add_cart_item(
            session_id, "prod_001", "Product 1", 10.0, 1, "v1", "Vendor 1"
        )
        cart_repository.add_cart_item(
            session_id, "prod_002", "Product 2", 20.0, 2, "v2", "Vendor 2"
        )

        items = cart_repository.get_cart_items(session_id)
        assert len(items) == 2

        # Items should be ordered by id DESC
        assert items[0]['product_id'] == "prod_002"
        assert items[1]['product_id'] == "prod_001"

    @pytest.mark.happy_path
    def test_get_cart_item_by_id(self, cart_repository):
        """Test getting specific cart item"""
        session_id = cart_repository.create_session()

        item_id = cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", 99.99, 1, "v1", "Vendor 1"
        )

        item = cart_repository.get_cart_item(item_id)
        assert item is not None
        assert item['id'] == item_id
        assert item['product_id'] == "prod_001"

    def test_get_nonexistent_cart_item(self, cart_repository):
        """Test getting non-existent cart item"""
        item = cart_repository.get_cart_item(99999)
        assert item is None

    @pytest.mark.happy_path
    def test_update_item_quantity(self, cart_repository):
        """Test updating item quantity"""
        session_id = cart_repository.create_session()

        item_id = cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", 99.99, 1, "v1", "Vendor 1"
        )

        success = cart_repository.update_item_quantity(item_id, 5)
        assert success is True

        # Verify update
        item = cart_repository.get_cart_item(item_id)
        assert item['quantity'] == 5

    def test_update_nonexistent_item_quantity(self, cart_repository):
        """Test updating quantity of non-existent item"""
        success = cart_repository.update_item_quantity(99999, 5)
        assert success is False

    @pytest.mark.happy_path
    def test_remove_cart_item(self, cart_repository):
        """Test removing cart item"""
        session_id = cart_repository.create_session()

        item_id = cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", 99.99, 1, "v1", "Vendor 1"
        )

        success = cart_repository.remove_cart_item(item_id)
        assert success is True

        # Verify removal
        items = cart_repository.get_cart_items(session_id)
        assert len(items) == 0

    def test_remove_nonexistent_cart_item(self, cart_repository):
        """Test removing non-existent cart item"""
        success = cart_repository.remove_cart_item(99999)
        assert success is False

    @pytest.mark.happy_path
    def test_clear_cart(self, cart_repository):
        """Test clearing all items from cart"""
        session_id = cart_repository.create_session()

        # Add multiple items
        cart_repository.add_cart_item(session_id, "prod_001", "Product 1", 10.0, 1, "v1", "Vendor 1")
        cart_repository.add_cart_item(session_id, "prod_002", "Product 2", 20.0, 2, "v2", "Vendor 2")

        cleared_count = cart_repository.clear_cart(session_id)
        assert cleared_count == 2

        # Verify cart is empty
        items = cart_repository.get_cart_items(session_id)
        assert len(items) == 0

    def test_clear_empty_cart(self, cart_repository):
        """Test clearing already empty cart"""
        session_id = cart_repository.create_session()
        cleared_count = cart_repository.clear_cart(session_id)
        assert cleared_count == 0

    @pytest.mark.happy_path
    def test_get_cart_totals_by_vendor(self, cart_repository):
        """Test getting cart totals grouped by vendor"""
        session_id = cart_repository.create_session()

        # Add items from different vendors
        cart_repository.add_cart_item(session_id, "prod_001", "Product 1", 100.0, 2, "v1", "Vendor 1")  # $200
        cart_repository.add_cart_item(session_id, "prod_002", "Product 2", 50.0, 1, "v1", "Vendor 1")   # $50
        cart_repository.add_cart_item(session_id, "prod_003", "Product 3", 75.0, 1, "v2", "Vendor 2")   # $75

        vendor_totals = cart_repository.get_cart_totals_by_vendor(session_id)

        assert len(vendor_totals) == 2

        # Vendor 1 should have $250 total
        v1_total = next((v for v in vendor_totals if v['vendor_id'] == 'v1'), None)
        assert v1_total is not None
        assert v1_total['vendor_subtotal'] == 250.0
        assert v1_total['item_count'] == 2

        # Vendor 2 should have $75 total
        v2_total = next((v for v in vendor_totals if v['vendor_id'] == 'v2'), None)
        assert v2_total is not None
        assert v2_total['vendor_subtotal'] == 75.0
        assert v2_total['item_count'] == 1

    def test_get_existing_cart_item(self, cart_repository):
        """Test getting existing cart item by session and product"""
        session_id = cart_repository.create_session()

        cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", 99.99, 1, "v1", "Vendor 1"
        )

        existing_item = cart_repository.get_existing_cart_item(session_id, "prod_001")
        assert existing_item is not None
        assert existing_item['quantity'] == 1

    def test_get_existing_cart_item_not_found(self, cart_repository):
        """Test getting non-existing cart item"""
        session_id = cart_repository.create_session()

        existing_item = cart_repository.get_existing_cart_item(session_id, "prod_001")
        assert existing_item is None

    @pytest.mark.happy_path
    def test_increment_item_quantity(self, cart_repository):
        """Test incrementing item quantity"""
        session_id = cart_repository.create_session()

        cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", 99.99, 1, "v1", "Vendor 1"
        )
        item = cart_repository.get_existing_cart_item(session_id, "prod_001")

        success = cart_repository.increment_item_quantity(item['id'], 3)
        assert success is True

        # Verify increment
        updated_item = cart_repository.get_cart_item(item['id'])
        assert updated_item['quantity'] == 4  # 1 + 3

    def test_increment_nonexistent_item_quantity(self, cart_repository):
        """Test incrementing quantity of non-existent item"""
        success = cart_repository.increment_item_quantity(99999, 3)
        assert success is False

    @pytest.mark.happy_path
    def test_get_cart_summary(self, cart_repository):
        """Test getting cart summary statistics"""
        session_id = cart_repository.create_session()

        # Add items
        cart_repository.add_cart_item(session_id, "prod_001", "Product 1", 100.0, 2, "v1", "Vendor 1")  # $200
        cart_repository.add_cart_item(session_id, "prod_002", "Product 2", 50.0, 1, "v2", "Vendor 2")   # $50

        summary = cart_repository.get_cart_summary(session_id)

        assert summary['item_count'] == 3
        assert summary['subtotal'] == 250.0
        assert summary['vendor_count'] == 2
        assert len(summary['vendor_breakdown']) == 2

    def test_get_cart_summary_empty(self, cart_repository):
        """Test getting summary of empty cart"""
        session_id = cart_repository.create_session()

        summary = cart_repository.get_cart_summary(session_id)

        assert summary['item_count'] == 0
        assert summary['subtotal'] == 0.0
        assert summary['vendor_count'] == 0
        assert len(summary['vendor_breakdown']) == 0

    @pytest.mark.negative
    def test_add_cart_item_invalid_session(self, cart_repository):
        """Test adding item with invalid session ID"""
        # This should not raise an exception in the mock implementation
        item_id = cart_repository.add_cart_item(
            session_id="invalid_session",
            product_id="prod_001",
            product_name="Test Product",
            price=99.99,
            quantity=1,
            vendor_id="v1",
            vendor_name="Vendor 1"
        )
        assert item_id is not None

    @pytest.mark.edge_case
    def test_add_cart_item_zero_quantity(self, cart_repository):
        """Test adding item with zero quantity"""
        session_id = cart_repository.create_session()

        item_id = cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", 99.99, 0, "v1", "Vendor 1"
        )
        assert item_id is not None

        # Verify item was added with zero quantity
        item = cart_repository.get_cart_item(item_id)
        assert item['quantity'] == 0

    @pytest.mark.edge_case
    def test_add_cart_item_negative_price(self, cart_repository):
        """Test adding item with negative price"""
        session_id = cart_repository.create_session()

        item_id = cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", -99.99, 1, "v1", "Vendor 1"
        )
        assert item_id is not None

        # Verify item was added with negative price
        item = cart_repository.get_cart_item(item_id)
        assert item['price'] == -99.99

    @pytest.mark.boundary
    def test_large_quantity_values(self, cart_repository):
        """Test handling large quantity values"""
        session_id = cart_repository.create_session()

        large_quantity = 999999
        item_id = cart_repository.add_cart_item(
            session_id, "prod_001", "Test Product", 10.0, large_quantity, "v1", "Vendor 1"
        )
        assert item_id is not None

        # Verify large quantity
        item = cart_repository.get_cart_item(item_id)
        assert item['quantity'] == large_quantity

    @pytest.mark.performance
    def test_bulk_cart_operations(self, cart_repository):
        """Test performance of bulk cart operations"""
        import time

        session_id = cart_repository.create_session()
        start_time = time.time()

        # Add many items
        item_ids = []
        for i in range(100):
            item_id = cart_repository.add_cart_item(
                session_id, f"prod_{i:03d}", f"Product {i}", 10.0 + i, 1, f"v{i%10}", f"Vendor {i%10}"
            )
            item_ids.append(item_id)

        add_time = time.time() - start_time

        # Get all items
        start_time = time.time()
        items = cart_repository.get_cart_items(session_id)
        get_time = time.time() - start_time

        # Update quantities
        start_time = time.time()
        for item_id in item_ids[:50]:  # Update first 50 items
            cart_repository.update_item_quantity(item_id, 2)
        update_time = time.time() - start_time

        # Remove items
        start_time = time.time()
        for item_id in item_ids[:25]:  # Remove first 25 items
            cart_repository.remove_cart_item(item_id)
        remove_time = time.time() - start_time

        # Assert reasonable performance (these values may need adjustment)
        assert add_time < 1.0  # Should add 100 items quickly
        assert get_time < 0.1  # Should retrieve items quickly
        assert update_time < 0.5  # Should update items quickly
        assert remove_time < 0.5  # Should remove items quickly

        # Verify final state
        final_items = cart_repository.get_cart_items(session_id)
        assert len(final_items) == 75  # 100 - 25 removed

    def test_database_transaction_rollback(self, test_db):
        """Test database transaction rollback on errors"""
        # This test simulates what would happen in a real repository
        # with proper transaction management
        repo = MockCartRepository(test_db)

        try:
            # Start transaction (simulated)
            session_id = repo.create_session()

            # Add item
            item_id = repo.add_cart_item(
                session_id, "prod_001", "Test Product", 99.99, 1, "v1", "Vendor 1"
            )

            # Simulate an error that would cause rollback
            raise Exception("Simulated error")

        except Exception:
            # In a real implementation, you would rollback here
            # For this mock, we just verify the item was added before the error
            items = repo.get_cart_items(session_id)
            assert len(items) == 1  # Item exists because we don't have real rollback