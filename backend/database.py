import sqlite3
import os
from backend.config import Config

def get_db_connection():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        pass
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
        stock_quantity INTEGER NOT NULL DEFAULT 25,
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
    if "stock_quantity" not in existing_prod_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN stock_quantity INTEGER NOT NULL DEFAULT 25;")

    # Orders table (configured with Indian market attributes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        customer_phone TEXT,
        total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Confirmed',
        address TEXT NOT NULL,
        city TEXT,
        state TEXT,
        pincode TEXT,
        currency TEXT NOT NULL DEFAULT 'INR',
        shipping_fee REAL NOT NULL DEFAULT 0.0,
        payment_method TEXT NOT NULL DEFAULT 'cod',
        whatsapp_status TEXT DEFAULT 'pending',
        estimated_delivery_date TEXT,
        tracking_number TEXT,
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
    if "whatsapp_status" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN whatsapp_status TEXT DEFAULT 'pending';")
    if "estimated_delivery_date" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN estimated_delivery_date TEXT;")
    if "tracking_number" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN tracking_number TEXT;")
    if "payment_status" not in existing_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'Pending';")

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

    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        display_order INTEGER DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Coupons table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        id TEXT PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        discount_type TEXT NOT NULL DEFAULT 'percentage', -- 'percentage' or 'fixed'
        discount_value REAL NOT NULL,
        min_order_amount REAL NOT NULL DEFAULT 0.0,
        max_discount_amount REAL,
        is_active INTEGER NOT NULL DEFAULT 1,
        usage_count INTEGER NOT NULL DEFAULT 0,
        expires_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Website Banners table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS banners (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subtitle TEXT,
        badge_text TEXT,
        button_text TEXT,
        button_link TEXT,
        image_url TEXT,
        bg_gradient TEXT,
        position TEXT NOT NULL DEFAULT 'hero', -- 'hero', 'top_bar', 'announcement'
        is_active INTEGER NOT NULL DEFAULT 1,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # WhatsApp Transmission Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_logs (
        id TEXT PRIMARY KEY,
        order_id TEXT,
        recipient_phone TEXT NOT NULL,
        recipient_name TEXT,
        message_type TEXT NOT NULL,
        message_text TEXT NOT NULL,
        status TEXT NOT NULL,
        wa_link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed initial categories if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM categories")
    if cursor.fetchone()["cnt"] == 0:
        default_categories = [
            ("cat_01", "Oversized T-Shirts", "Heavyweight 240-280 GSM architectural drape tees.", 1),
            ("cat_02", "Graphic T-Shirts", "Archival screenprints, cyber kanji, and anime art.", 2),
            ("cat_03", "Minimal & Core", "Luxury combed cotton solid studio blanks.", 3),
            ("cat_04", "Jackets", "Heavy bombers, truckers, and varsity streetwear.", 4),
            ("cat_05", "Shirts", "Camp-collar linen and utility workwear shirts.", 5),
            ("cat_06", "Sweatshirts", "French Terry loopback hoodies and crewnecks.", 6),
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO categories (id, name, description, display_order)
            VALUES (?, ?, ?, ?)
        """, default_categories)

    # Seed initial coupons if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM coupons")
    if cursor.fetchone()["cnt"] == 0:
        default_coupons = [
            ("cpn_01", "PAINITE10", "percentage", 10.0, 1499.0, 500.0, 1, 14, "2026-12-31"),
            ("cpn_02", "ATELIER20", "percentage", 20.0, 2499.0, 1000.0, 1, 8, "2026-12-31"),
            ("cpn_03", "FIRST300", "fixed", 300.0, 1799.0, 300.0, 1, 23, "2026-12-31"),
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO coupons (id, code, discount_type, discount_value, min_order_amount, max_discount_amount, is_active, usage_count, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_coupons)

    # Seed initial banners if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM banners")
    if cursor.fetchone()["cnt"] == 0:
        default_banners = [
            (
                "bnr_01",
                "AUTUMN / WINTER '26 ATELIER DROP",
                "Heavyweight 280 GSM Indian Combed Cotton · Custom Architecture · Free Express Shipping Across India",
                "★ NEW COLLECTION LIVE",
                "Explore Collection",
                "#/shop",
                "/static/images/essential-tee.jpg",
                "linear-gradient(135deg, rgba(250,247,242,0.95), rgba(252,238,233,0.85))",
                "hero",
                1,
                1
            ),
            (
                "bnr_02",
                "EXCLUSIVE FESTIVE PRIVILEGE: 10% OFF ON ORDERS ABOVE ₹1,499",
                "Use Code: PAINITE10 at checkout · Pan-India Express Delivery within 3-4 Days",
                "FESTIVE PRIVILEGE",
                "Claim Privilege",
                "#/shop",
                None,
                "linear-gradient(90deg, #A3772C, #C29A4D)",
                "top_bar",
                1,
                2
            )
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO banners (id, title, subtitle, badge_text, button_text, button_link, image_url, bg_gradient, position, is_active, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_banners)

    conn.commit()
    conn.close()

