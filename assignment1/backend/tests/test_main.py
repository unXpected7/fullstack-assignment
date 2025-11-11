import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from main import app
import json
import sqlite3
from unittest.mock import patch, AsyncMock

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    """Create a test database and clean up after tests"""
    # Create test database
    conn = sqlite3.connect(':memory:')  # In-memory database for testing
    conn.execute('''
        CREATE TABLE cart_sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            product_id TEXT,
            product_name TEXT,
            price REAL,
            quantity INTEGER,
            vendor_id TEXT,
            vendor_name TEXT,
            image_url TEXT,
            FOREIGN KEY (session_id) REFERENCES cart_sessions (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE discount_codes (
            code TEXT PRIMARY KEY,
            percentage REAL CHECK (percentage >= 0 AND percentage <= 100),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE product_service_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            api_key TEXT,
            headers TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        INSERT INTO discount_codes (code, percentage) VALUES
        ('SAVE10', 10.0),
        ('SAVE20', 20.0)
    ''')
    conn.execute('''
        INSERT INTO product_service_config (endpoint, headers)
        VALUES ('https://api.example.com/products', '{}')
    ''')
    conn.commit()
    conn.close()

    # Apply the test database configuration to the app
    with patch('main.get_db_connection') as mock_get_db:
        def mock_db():
            test_conn = sqlite3.connect(':memory:')
            test_conn.row_factory = sqlite3.Row
            return test_conn
        mock_get_db.side_effect = mock_db

    yield

    # Clean up - the in-memory database will be garbage collected

@pytest.fixture
def sample_product_data():
    return {
        "id": "prod_001",
        "name": "Test Product",
        "price": 99.99,
        "stock": 50,
        "vendor_id": "vendor_001",
        "vendor_name": "Vendor A",
        "image_url": "https://example.com/image.jpg"
    }

@pytest.mark.asyncio
async def test_add_to_cart_success(test_db, sample_product_data):
    """Test successfully adding item to cart"""
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 2
        })

        assert response.status_code == 200
        data = response.json()
        assert "Item added to cart" in data["message"]
        assert "session_id" in data

@pytest.mark.asyncio
async def test_add_to_cart_product_not_found(test_db):
    """Test adding non-existent product to cart"""
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = None

        response = client.post("/api/v1/cart/items", json={
            "product_id": "non_existent",
            "quantity": 1
        })

        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_add_to_cart_insufficient_stock(test_db, sample_product_data):
    """Test adding item with insufficient stock"""
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        sample_product_data["stock"] = 1
        mock_fetch.return_value = sample_product_data

        response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 5  # Request more than available stock
        })

        assert response.status_code == 400
        assert "Insufficient stock" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_cart_empty(test_db):
    """Test getting empty cart"""
    response = client.get("/api/v1/cart")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["subtotal"] == 0.0
    assert data["discount"] == 0.0
    assert data["shipping"] == 0.0
    assert data["total"] == 0.0

@pytest.mark.asyncio
async def test_get_cart_with_items(test_db, sample_product_data):
    """Test getting cart with items"""
    # First add item to cart
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 2
        })
        session_id = add_response.json()["session_id"]

        # Now get cart
        response = client.get(f"/api/v1/cart?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == "prod_001"
        assert data["items"][0]["quantity"] == 2
        assert data["subtotal"] == 199.98  # 99.99 * 2
        assert data["items"][0]["vendor_id"] == "vendor_001"

@pytest.mark.asyncio
async def test_update_item_quantity(test_db, sample_product_data):
    """Test updating item quantity"""
    # Add item first
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 1
        })
        session_id = add_response.json()["session_id"]

        # Get cart to find item ID
        cart_response = client.get(f"/api/v1/cart?session_id={session_id}")
        item_id = cart_response.json()["items"][0]["id"]

        # Update quantity
        response = client.put(f"/api/v1/cart/items/{item_id}?session_id={session_id}", json={"quantity": 5})

        assert response.status_code == 200
        assert "Quantity updated" in response.json()["message"]

        # Verify update
        cart_response = client.get(f"/api/v1/cart?session_id={session_id}")
        assert cart_response.json()["items"][0]["quantity"] == 5

@pytest.mark.asyncio
async def test_update_item_quantity_invalid(test_db, sample_product_data):
    """Test updating item quantity with invalid values"""
    # Add item first
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 1
        })
        session_id = add_response.json()["session_id"]

        # Get cart to find item ID
        cart_response = client.get(f"/api/v1/cart?session_id={session_id}")
        item_id = cart_response.json()["items"][0]["id"]

        # Try to update with quantity 0
        response = client.put(f"/api/v1/cart/items/{item_id}?session_id={session_id}", json={"quantity": 0})
        assert response.status_code == 400
        assert "Quantity must be at least 1" in response.json()["detail"]

@pytest.mark.asyncio
async def test_remove_item(test_db, sample_product_data):
    """Test removing item from cart"""
    # Add item first
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 1
        })
        session_id = add_response.json()["session_id"]

        # Get cart to find item ID
        cart_response = client.get(f"/api/v1/cart?session_id={session_id}")
        item_id = cart_response.json()["items"][0]["id"]

        # Remove item
        response = client.delete(f"/api/v1/cart/items/{item_id}?session_id={session_id}")
        assert response.status_code == 200
        assert "Item removed" in response.json()["message"]

        # Verify item is removed
        cart_response = client.get(f"/api/v1/cart?session_id={session_id}")
        assert len(cart_response.json()["items"]) == 0

@pytest.mark.asyncio
async def test_clear_cart(test_db, sample_product_data):
    """Test clearing entire cart"""
    # Add some items first
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 1
        })
        session_id = add_response.json()["session_id"]

        # Clear cart
        response = client.delete(f"/api/v1/cart?session_id={session_id}")
        assert response.status_code == 200
        assert "Cart cleared" in response.json()["message"]

        # Verify cart is empty
        cart_response = client.get(f"/api/v1/cart?session_id={session_id}")
        assert len(cart_response.json()["items"]) == 0

@pytest.mark.asyncio
async def test_apply_discount_code(test_db, sample_product_data):
    """Test applying discount code"""
    # Add item to cart
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 10  # $999.90 total
        })
        session_id = add_response.json()["session_id"]

        # Apply discount
        response = client.post(f"/api/v1/cart/discount?session_id={session_id}", json={"code": "SAVE10"})
        assert response.status_code == 200
        data = response.json()
        assert "Discount code applied" in data["message"]
        assert data["code"] == "SAVE10"
        assert data["discount_amount"] == 99.99  # 10% of 999.90

@pytest.mark.asyncio
async def test_apply_invalid_discount_code(test_db, sample_product_data):
    """Test applying invalid discount code"""
    # Add item to cart
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 1
        })
        session_id = add_response.json()["session_id"]

        # Apply invalid discount
        response = client.post(f"/api/v1/cart/discount?session_id={session_id}", json={"code": "INVALID"})
        assert response.status_code == 404
        assert "Invalid discount code" in response.json()["detail"]

@pytest.mark.asyncio
async def test_remove_discount_code(test_db, sample_product_data):
    """Test removing discount code"""
    # Add item and apply discount
    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_product_data

        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_001",
            "quantity": 10
        })
        session_id = add_response.json()["session_id"]

        client.post(f"/api/v1/cart/discount?session_id={session_id}", json={"code": "SAVE10"})

        # Remove discount
        response = client.delete(f"/api/v1/cart/discount?session_id={session_id}")
        assert response.status_code == 200
        assert "Discount code removed" in response.json()["message"]

@pytest.mark.asyncio
async def test_shipping_calculation_multiple_vendors(test_db):
    """Test shipping calculation with multiple vendors"""
    # Mock product data for two vendors
    product_a = {
        "id": "prod_a",
        "name": "Product A",
        "price": 900,  # Above $800 threshold
        "stock": 10,
        "vendor_id": "vendor_001",
        "vendor_name": "Vendor A"
    }

    product_b = {
        "id": "prod_b",
        "name": "Product B",
        "price": 500,  # Below $800 threshold
        "stock": 10,
        "vendor_id": "vendor_002",
        "vendor_name": "Vendor B"
    }

    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        # Mock responses for different product IDs
        async def mock_fetch_side_effect(product_id):
            if product_id == "prod_a":
                return product_a
            elif product_id == "prod_b":
                return product_b
            return None

        mock_fetch.side_effect = mock_fetch_side_effect

        # Add items from both vendors
        add_response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_a",
            "quantity": 1
        })
        session_id = add_response.json()["session_id"]

        client.post("/api/v1/cart/items", json={
            "product_id": "prod_b",
            "quantity": 1,
            "session_id": session_id
        })

        # Get cart totals
        response = client.get(f"/api/v1/cart?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["subtotal"] == 1400.0  # 900 + 500
        assert data["shipping"] == 100.0   # 0 (vendor A) + 100 (vendor B)
        assert data["total"] == 1500.0     # 1400 + 100

@pytest.mark.asyncio
async def test_configure_product_service(test_db):
    """Test configuring external product service"""
    config = {
        "endpoint": "https://api.example.com/products",
        "api_key": "test_key",
        "headers": {"Authorization": "Bearer test"}
    }

    response = client.post("/api/v1/config/product-service", json=config)
    assert response.status_code == 200
    assert "Product service configured successfully" in response.json()["message"]

@pytest.mark.asyncio
async def test_get_product_service_config(test_db):
    """Test getting product service configuration"""
    response = client.get("/api/v1/config/product-service")
    assert response.status_code == 200
    data = response.json()
    assert "endpoint" in data
    assert "headers" in data

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Shopping Cart API is running" in response.json()["message"]

@pytest.mark.asyncio
async def test_vendor_based_shipping_rules(test_db):
    """Test vendor-based shipping calculation rules"""
    # Test case 1: Vendor subtotal >= $800 should have $0 shipping
    product_high_value = {
        "id": "prod_high",
        "name": "High Value Product",
        "price": 850,  # Above $800
        "stock": 10,
        "vendor_id": "vendor_high",
        "vendor_name": "Vendor High"
    }

    product_low_value = {
        "id": "prod_low",
        "name": "Low Value Product",
        "price": 750,  # Below $800
        "stock": 10,
        "vendor_id": "vendor_low",
        "vendor_name": "Vendor Low"
    }

    with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
        def mock_fetch_side_effect(product_id):
            if product_id == "prod_high":
                return product_high_value
            elif product_id == "prod_low":
                return product_low_value
            return None

        mock_fetch.side_effect = mock_fetch_side_effect

        # Add one item from each vendor
        response = client.post("/api/v1/cart/items", json={
            "product_id": "prod_high",
            "quantity": 1
        })
        session_id = response.json()["session_id"]

        client.post("/api/v1/cart/items", json={
            "product_id": "prod_low",
            "quantity": 1,
            "session_id": session_id
        })

        # Check totals
        cart_response = client.get(f"/api/v1/cart?session_id={session_id}")
        data = cart_response.json()

        # High vendor: $850 subtotal, should have $0 shipping
        # Low vendor: $750 subtotal, should have $100 shipping
        # Total shipping: $100
        assert data["shipping"] == 100.0
        assert data["subtotal"] == 1600.0  # 850 + 750
        assert data["total"] == 1700.0     # 1600 + 100