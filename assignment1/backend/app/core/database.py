import sqlite3
from typing import Optional
from app.config.settings import settings


def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(settings.database_url.replace("sqlite:///", ""))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables"""
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

    # Create discount codes table
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