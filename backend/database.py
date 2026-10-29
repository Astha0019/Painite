import sqlite3
import os
from backend.config import Config

def get_db_connection():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        original_price REAL,
        discount_pct INTEGER DEFAULT 0,
        category TEXT NOT NULL,
        gender TEXT NOT NULL DEFAULT 'Unisex',
        collection TEXT NOT NULL DEFAULT 'Streetwear',
        tag TEXT,
        image TEXT NOT NULL,
        color_hex TEXT DEFAULT '#101114',
        colors TEXT NOT NULL, -- JSON array
        sizes TEXT NOT NULL,  -- JSON array
        styles TEXT NOT NULL, -- JSON array
        in_stock INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Safe migration: add product columns if upgrading existing table
    cursor.execute("PRAGMA table_info(products);")
    existing_prod_cols = {row["name"] for row in cursor.fetchall()}
    if "original_price" not in existing_prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN original_price REAL;")
    if "discount_pct" not in existing_prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN discount_pct INTEGER DEFAULT 0;")
    if "gender" not in existing_prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN gender TEXT NOT NULL DEFAULT 'Unisex';")
    if "collection" not in existing_prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN collection TEXT NOT NULL DEFAULT 'Streetwear';")
    if "color_hex" not in existing_prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN color_hex TEXT DEFAULT '#101114';")

    # Orders table (configured with Indian market attributes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        customer_phone TEXT,
        total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        address TEXT NOT NULL,
        city TEXT,
        state TEXT,
        pincode TEXT,
        currency TEXT NOT NULL DEFAULT 'INR',
        shipping_fee REAL NOT NULL DEFAULT 0.0,
        payment_method TEXT NOT NULL DEFAULT 'cod',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # Safe migration: add Indian market columns to orders if upgrading existing table
    cursor.execute("PRAGMA table_info(orders);")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    if "customer_phone" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT;")
    if "city" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN city TEXT;")
    if "state" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN state TEXT;")
    if "pincode" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN pincode TEXT;")
    if "currency" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN currency TEXT NOT NULL DEFAULT 'INR';")
    if "shipping_fee" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN shipping_fee REAL NOT NULL DEFAULT 0.0;")

    # Order items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        product_id TEXT,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        color TEXT,
        size TEXT,
        style TEXT,
        custom_text TEXT,
        artwork_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
