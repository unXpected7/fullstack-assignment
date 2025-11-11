from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
import json
import secrets
from datetime import datetime
import httpx
from cachetools import TTLCache

app = FastAPI(title="Shopping Cart API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('shopping_cart.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create cart sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create cart items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
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

    # Create discount codes table (optional - for predefined codes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discount_codes (
            code TEXT PRIMARY KEY,
            percentage REAL CHECK (percentage >= 0 AND percentage <= 100),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create product service config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_service_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            api_key TEXT,
            headers TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert sample discount codes
    cursor.execute('''
        INSERT OR IGNORE INTO discount_codes (code, percentage) VALUES
        ('SAVE10', 10.0),
        ('SAVE20', 20.0),
        ('SAVE15', 15.0)
    ''')

    # Insert sample product service config
    cursor.execute('''
        INSERT OR IGNORE INTO product_service_config (endpoint, headers)
        VALUES (?, ?)
    ''', ('https://api.example.com/products', '{}'))

    conn.commit()
    conn.close()

# Cache for product information (5 minute TTL)
product_cache = TTLCache(maxsize=1000, ttl=300)

# Models
class CartItem(BaseModel):
    product_id: str
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    product_id: str
    product_name: str
    price: float
    quantity: int
    vendor_id: str
    vendor_name: str
    image_url: Optional[str] = None

class CartResponse(BaseModel):
    session_id: str
    items: List[CartItemResponse]
    subtotal: float
    discount: float
    shipping: float
    total: float
    discount_code: Optional[str] = None

class DiscountCodeRequest(BaseModel):
    code: str

class ProductServiceConfig(BaseModel):
    endpoint: str
    api_key: Optional[str] = None
    headers: Optional[Dict] = None

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Helper functions
def calculate_totals(session_id: str, discount_code: Optional[str] = None) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get cart items grouped by vendor
    cursor.execute('''
        SELECT vendor_id, vendor_name, SUM(price * quantity) as vendor_subtotal
        FROM cart_items
        WHERE session_id = ?
        GROUP BY vendor_id, vendor_name
    ''', (session_id,))

    vendor_groups = cursor.fetchall()

    # Calculate shipping based on vendor rules
    shipping = 0
    for vendor in vendor_groups:
        if vendor['vendor_subtotal'] < 800:
            shipping += 100

    # Get subtotal
    cursor.execute('''
        SELECT COALESCE(SUM(price * quantity), 0) as subtotal
        FROM cart_items
        WHERE session_id = ?
    ''', (session_id,))

    subtotal = cursor.fetchone()['subtotal']

    # Calculate discount
    discount = 0
    if discount_code:
        cursor.execute('''
            SELECT percentage FROM discount_codes
            WHERE code = ? AND is_active = 1
        ''', (discount_code,))
        result = cursor.fetchone()
        if result:
            discount = subtotal * (result['percentage'] / 100)

    # Calculate final total
    total = subtotal - discount + shipping

    conn.close()

    return {
        'subtotal': round(subtotal, 2),
        'discount': round(discount, 2),
        'shipping': round(shipping, 2),
        'total': round(total, 2)
    }

def get_or_create_session_id() -> str:
    """Get existing session or create new one"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Try to get an existing session (in production, use session management)
    cursor.execute('SELECT id FROM cart_sessions LIMIT 1')
    result = cursor.fetchone()

    if result:
        session_id = result['id']
    else:
        # Create new session
        session_id = secrets.token_urlsafe(32)
        cursor.execute('INSERT INTO cart_sessions (id) VALUES (?)', (session_id,))

    conn.commit()
    conn.close()
    return session_id

async def fetch_product_from_external_api(product_id: str) -> Optional[dict]:
    """Fetch product information from external API with caching"""
    # Check cache first
    cache_key = f"product_{product_id}"
    if cache_key in product_cache:
        return product_cache[cache_key]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get product service configuration
    cursor.execute('''
        SELECT endpoint, api_key, headers
        FROM product_service_config
        WHERE is_active = 1
        LIMIT 1
    ''')

    config = cursor.fetchone()
    conn.close()

    if not config or not config['endpoint']:
        return None

    try:
        headers = json.loads(config['headers']) if config['headers'] else {}
        if config['api_key']:
            headers['Authorization'] = f'Bearer {config["api_key"]}'

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{config['endpoint']}/{product_id}",
                headers=headers
            )
            response.raise_for_status()

            product_data = response.json()

            # Cache the result
            product_cache[cache_key] = product_data
            return product_data

    except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error fetching product {product_id}: {e}")
        return None

# API Endpoints
@app.post("/api/v1/cart/items")
async def add_to_cart(item: CartItem, session_id: Optional[str] = None):
    """Add item to cart"""
    # Get or create session
    if not session_id:
        session_id = get_or_create_session_id()

    # Fetch product details from external API
    product_data = await fetch_product_from_external_api(item.product_id)

    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_data.get('stock', 0) < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if item already exists in cart
    cursor.execute('''
        SELECT id FROM cart_items
        WHERE session_id = ? AND product_id = ?
    ''', (session_id, item.product_id))

    existing_item = cursor.fetchone()

    if existing_item:
        # Update quantity
        cursor.execute('''
            UPDATE cart_items
            SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (item.quantity, existing_item['id']))
    else:
        # Add new item
        cursor.execute('''
            INSERT INTO cart_items (
                session_id, product_id, product_name, price, quantity,
                vendor_id, vendor_name, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            item.product_id,
            product_data.get('name'),
            product_data.get('price', 0),
            item.quantity,
            product_data.get('vendor_id'),
            product_data.get('vendor_name'),
            product_data.get('image_url')
        ))

    conn.commit()
    conn.close()

    return {"message": "Item added to cart", "session_id": session_id}

@app.get("/api/v1/cart", response_model=CartResponse)
async def get_cart(session_id: Optional[str] = None):
    """Get cart details"""
    if not session_id:
        session_id = get_or_create_session_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get cart items
    cursor.execute('''
        SELECT id, product_id, product_name, price, quantity,
               vendor_id, vendor_name, image_url
        FROM cart_items
        WHERE session_id = ?
        ORDER BY id DESC
    ''', (session_id,))

    items = []
    for row in cursor.fetchall():
        items.append(CartItemResponse(**dict(row)))

    conn.close()

    # Calculate totals
    totals = calculate_totals(session_id)

    return CartResponse(
        session_id=session_id,
        items=items,
        **totals
    )

@app.put("/api/v1/cart/items/{item_id}")
async def update_item_quantity(item_id: int, quantity: int, session_id: Optional[str] = None):
    """Update item quantity"""
    if not session_id:
        session_id = get_or_create_session_id()

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if item exists and belongs to session
    cursor.execute('''
        SELECT product_id FROM cart_items
        WHERE id = ? AND session_id = ?
    ''', (item_id, session_id))

    item = cursor.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # Check stock availability
    product_data = await fetch_product_from_external_api(item['product_id'])
    if product_data and product_data.get('stock', 0) < quantity:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient stock")

    # Update quantity
    cursor.execute('''
        UPDATE cart_items
        SET quantity = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (quantity, item_id))

    conn.commit()
    conn.close()

    return {"message": "Quantity updated"}

@app.delete("/api/v1/cart/items/{item_id}")
async def remove_item(item_id: int, session_id: Optional[str] = None):
    """Remove item from cart"""
    if not session_id:
        session_id = get_or_create_session_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if item exists and belongs to session
    cursor.execute('''
        SELECT id FROM cart_items
        WHERE id = ? AND session_id = ?
    ''', (item_id, session_id))

    item = cursor.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    # Remove item
    cursor.execute('DELETE FROM cart_items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

    return {"message": "Item removed"}

@app.delete("/api/v1/cart")
async def clear_cart(session_id: Optional[str] = None):
    """Clear cart"""
    if not session_id:
        session_id = get_or_create_session_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM cart_items WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()

    return {"message": "Cart cleared"}

@app.post("/api/v1/cart/discount")
async def apply_discount_code(request: DiscountCodeRequest, session_id: Optional[str] = None):
    """Apply discount code"""
    if not session_id:
        session_id = get_or_create_session_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validate discount code
    cursor.execute('''
        SELECT code, percentage FROM discount_codes
        WHERE code = ? AND is_active = 1
    ''', (request.code,))

    discount = cursor.fetchone()
    if not discount:
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid discount code")

    # Store discount code in session (in production, use session storage)
    # For this implementation, we'll calculate on the fly
    conn.close()

    totals = calculate_totals(session_id, request.code)
    return {
        "message": "Discount code applied",
        "code": request.code,
        "discount_amount": totals['discount']
    }

@app.delete("/api/v1/cart/discount")
async def remove_discount_code(session_id: Optional[str] = None):
    """Remove discount code"""
    if not session_id:
        session_id = get_or_create_session_id()

    # In production, clear discount from session storage
    # For this implementation, we'll calculate without discount
    totals = calculate_totals(session_id)

    return {
        "message": "Discount code removed",
        "discount_amount": 0
    }

@app.post("/api/v1/config/product-service")
async def configure_product_service(config: ProductServiceConfig):
    """Configure external product service"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert or update configuration
    cursor.execute('''
        INSERT OR REPLACE INTO product_service_config
        (endpoint, api_key, headers) VALUES (?, ?, ?)
    ''', (config.endpoint, config.api_key, json.dumps(config.headers or {})))

    conn.commit()
    conn.close()

    # Clear cache to use new configuration
    product_cache.clear()

    return {"message": "Product service configured successfully"}

@app.get("/api/v1/config/product-service")
async def get_product_service_config():
    """Get product service configuration"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT endpoint, api_key, headers
        FROM product_service_config
        WHERE is_active = 1
        LIMIT 1
    ''')

    config = cursor.fetchone()
    conn.close()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return {
        "endpoint": config['endpoint'],
        "api_key": config['api_key'],
        "headers": json.loads(config['headers']) if config['headers'] else {}
    }

@app.get("/")
async def root():
    return {"message": "Shopping Cart API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)