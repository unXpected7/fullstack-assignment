import pytest
import pytest_asyncio
import sqlite3
import tempfile
import os
from typing import Generator, Dict, Any
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="session")
def test_db_path() -> str:
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    yield db_path
    # Clean up
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="function")
def test_db(test_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Create and initialize test database"""
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row

    # Create tables
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

    # Insert test data
    conn.execute('''
        INSERT INTO discount_codes (code, percentage) VALUES
        ('SAVE10', 10.0),
        ('SAVE20', 20.0),
        ('SAVE15', 15.0)
    ''')

    conn.execute('''
        INSERT INTO product_service_config (endpoint, headers)
        VALUES ('https://api.example.com/products', '{}')
    ''')

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def test_client(test_db_path: str) -> TestClient:
    """Create test client with mocked database"""
    with pytest.MonkeyPatch().context() as m:
        def mock_get_db_connection():
            conn = sqlite3.connect(test_db_path)
            conn.row_factory = sqlite3.Row
            return conn

        m.setattr('main.get_db_connection', mock_get_db_connection)
        yield TestClient(app)


@pytest.fixture
def sample_product_data() -> Dict[str, Any]:
    """Sample product data for testing"""
    return {
        "id": "prod_001",
        "name": "Test Product",
        "price": 99.99,
        "stock": 50,
        "vendor_id": "vendor_001",
        "vendor_name": "Vendor A",
        "image_url": "https://example.com/image.jpg",
        "description": "A test product for unit testing"
    }


@pytest.fixture
def sample_product_data_multiple_vendors() -> Dict[str, Dict[str, Any]]:
    """Sample product data from multiple vendors"""
    return {
        "prod_high_value": {
            "id": "prod_high_value",
            "name": "High Value Product",
            "price": 850.00,
            "stock": 10,
            "vendor_id": "vendor_001",
            "vendor_name": "Premium Vendor",
            "image_url": "https://example.com/high-value.jpg"
        },
        "prod_low_value": {
            "id": "prod_low_value",
            "name": "Low Value Product",
            "price": 750.00,
            "stock": 25,
            "vendor_id": "vendor_002",
            "vendor_name": "Budget Vendor",
            "image_url": "https://example.com/low-value.jpg"
        },
        "prod_mid_value": {
            "id": "prod_mid_value",
            "name": "Mid Value Product",
            "price": 500.00,
            "stock": 15,
            "vendor_id": "vendor_003",
            "vendor_name": "Standard Vendor",
            "image_url": "https://example.com/mid-value.jpg"
        }
    }


@pytest.fixture
def sample_cart_item_data() -> Dict[str, Any]:
    """Sample cart item data for testing"""
    return {
        "product_id": "prod_001",
        "quantity": 2
    }


@pytest.fixture
def sample_discount_data() -> Dict[str, Any]:
    """Sample discount code data"""
    return {
        "code": "SAVE10",
        "percentage": 10.0,
        "is_active": True
    }


@pytest.fixture
def mock_product_service_config() -> Dict[str, Any]:
    """Mock product service configuration"""
    return {
        "endpoint": "https://api.example.com/products",
        "api_key": "test_api_key",
        "headers": {
            "Authorization": "Bearer test_api_key",
            "Content-Type": "application/json"
        }
    }


@pytest.fixture
def mock_external_api_response(sample_product_data: Dict[str, Any]) -> Mock:
    """Mock external API response"""
    mock_response = Mock()
    mock_response.json.return_value = sample_product_data
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
async def async_mock_product_service():
    """Async mock for product service"""
    mock = AsyncMock()
    return mock


@pytest.fixture
def setup_cart_session(test_db: sqlite3.Connection) -> str:
    """Create a test cart session and return session ID"""
    session_id = "test_session_12345"
    test_db.execute(
        "INSERT INTO cart_sessions (id) VALUES (?)",
        (session_id,)
    )
    test_db.commit()
    return session_id


@pytest.fixture
def setup_cart_with_items(test_db: sqlite3.Connection, setup_cart_session: str,
                         sample_product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a cart with items for testing"""
    session_id = setup_cart_session

    # Add items to cart
    test_db.execute('''
        INSERT INTO cart_items (
            session_id, product_id, product_name, price, quantity,
            vendor_id, vendor_name, image_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        sample_product_data["id"],
        sample_product_data["name"],
        sample_product_data["price"],
        2,
        sample_product_data["vendor_id"],
        sample_product_data["vendor_name"],
        sample_product_data["image_url"]
    ))

    test_db.commit()

    return {
        "session_id": session_id,
        "product_id": sample_product_data["id"],
        "quantity": 2,
        "price": sample_product_data["price"]
    }


@pytest.fixture
def invalid_product_data() -> Dict[str, Any]:
    """Invalid product data for negative testing"""
    return {
        "id": "",
        "name": "",
        "price": -10.0,
        "stock": -5,
        "vendor_id": None,
        "vendor_name": None
    }


@pytest.fixture
def boundary_test_data() -> Dict[str, Dict[str, Any]]:
    """Boundary test data for edge cases"""
    return {
        "zero_price": {
            "id": "prod_zero",
            "name": "Zero Price Product",
            "price": 0.0,
            "stock": 10,
            "vendor_id": "vendor_001",
            "vendor_name": "Test Vendor"
        },
        "max_quantity": {
            "id": "prod_max_qty",
            "name": "Max Quantity Product",
            "price": 10.0,
            "stock": 1,
            "vendor_id": "vendor_002",
            "vendor_name": "Limited Vendor"
        },
        "exact_shipping_threshold": {
            "id": "prod_threshold",
            "name": "Threshold Product",
            "price": 800.0,
            "stock": 5,
            "vendor_id": "vendor_003",
            "vendor_name": "Threshold Vendor"
        }
    }


# Async fixtures for async testing
@pytest_asyncio.fixture
async def async_test_client(test_db_path: str) -> TestClient:
    """Create async test client with mocked database"""
    with pytest.MonkeyPatch().context() as m:
        def mock_get_db_connection():
            conn = sqlite3.connect(test_db_path)
            conn.row_factory = sqlite3.Row
            return conn

        m.setattr('main.get_db_connection', mock_get_db_connection)
        yield TestClient(app)