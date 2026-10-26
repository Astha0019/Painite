import json
import uuid
import datetime
from backend.database import get_db_connection
from backend.auth import hash_password

def seed_database(force_refresh=False):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM products")
    count = cursor.fetchone()["cnt"]
    if count > 0 and not force_refresh:
        # Check if prices are already in INR (above 100)
        cursor.execute("SELECT AVG(price) as avg_p FROM products")
        avg_price = cursor.fetchone()["avg_p"] or 0
        if avg_price > 100:
            conn.close()
            return

    print("Seeding Painite Studio India database (INR / Indian Streetwear)...")

    # 1. Seed Users
    admin_id = "usr_admin_001"
    customer_id = "usr_cust_001"

    cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, (
        admin_id,
        "Painite Studio Director",
        "admin@painite.studio",
        hash_password("PainiteAdmin!42"),
        "admin"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id,
        "Aarav Sharma",
        "customer@painite.studio",
        hash_password("PainiteUser!42"),
        "customer"
    ))

    # 2. Seed Indian Streetwear & Customized T-Shirt Collection
    products = [
        {
            "id": "p1",
            "name": "The Essential Heavyweight Tee",
            "description": "240 GSM dense combed Indian cotton blank tailored for everyday streetwear with a structured, breathable drape.",
            "price": 1299.00,
            "category": "Core",
            "tag": "BESTSELLER",
            "image": "/static/images/essential-tee.jpg",
            "colors": ["Onyx Black", "Kora White", "Slate Grey", "Dusk Olive"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Oversized", "Boxy"]
        },
        {
            "id": "p2",
            "name": "Noir Studio Oversized Tee",
            "description": "Garment-dyed carbon black streetwear blank with double-needle ribbed collar and subtle enzyme wash treatment.",
            "price": 1499.00,
            "category": "Studio",
            "tag": "NEW ARRIVAL",
            "image": "/static/images/noir-studio-tee.jpg",
            "colors": ["Onyx Black", "Slate Grey", "Kora White"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "p3",
            "name": "Form / Function Architectural Tee",
            "description": "Architectural silhouette featuring drop shoulders, clean geometric balance, and reinforced Japanese-style binding.",
            "price": 1799.00,
            "category": "Edition 01",
            "tag": "LIMITED DROP",
            "image": "/static/images/form-function-tee.jpg",
            "colors": ["Kora White", "Chai Sand", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "p4",
            "name": "Atelier 280 GSM Custom Heavyweight Blank",
            "description": "Dense knit 280 GSM French Terry cotton blank crafted specifically for bespoke studio custom graphics and personal silkscreen prints.",
            "price": 1499.00,
            "category": "Customizable",
            "tag": "CUSTOM T-SHIRT",
            "image": "/static/images/essential-tee.jpg",
            "colors": ["Onyx Black", "Kora White", "Dusk Olive", "Chai Sand"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy", "Classic"]
        },
        {
            "id": "p5",
            "name": "Archival Monolith Acid Wash Tee",
            "description": "Limited studio series exploring raw mineral wash finishes, oversized proportions, subtle tonal branding, and archival stitching.",
            "price": 1999.00,
            "category": "Studio",
            "tag": "LIMITED DROP",
            "image": "/static/images/noir-studio-tee.jpg",
            "colors": ["Onyx Black", "Slate Grey"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "p6",
            "name": "Kinetic Raw Hem Deconstructed Tee",
            "description": "Deconstructed relaxed street fit with raw bottom hem, reinforced neckline, and signature Painite Studio minimal branding.",
            "price": 1699.00,
            "category": "Edition 01",
            "tag": "NEW ARRIVAL",
            "image": "/static/images/form-function-tee.jpg",
            "colors": ["Kora White", "Onyx Black", "Chai Sand"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "p7",
            "name": "Bespoke Streetwear Boxy Custom Tee",
            "description": "Engineered modern boxy fit blank ready for your personal custom typography, uploaded artwork, or studio embroidery badge.",
            "price": 1599.00,
            "category": "Customizable",
            "tag": "CUSTOM T-SHIRT",
            "image": "/static/images/noir-studio-tee.jpg",
            "colors": ["Onyx Black", "Kora White", "Slate Grey", "Indigo Navy"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "p8",
            "name": "Vintage Mineral Wash Custom Blank",
            "description": "Hand-treated mineral wash vintage cotton blank with pre-shrunk heavyweight feel. Designed for bold streetwear designs.",
            "price": 1799.00,
            "category": "Customizable",
            "tag": "CUSTOM T-SHIRT",
            "image": "/static/images/form-function-tee.jpg",
            "colors": ["Slate Grey", "Onyx Black", "Dusk Olive"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        }
    ]

    for p in products:
        cursor.execute("""
            INSERT OR REPLACE INTO products (id, name, description, price, category, tag, image, colors, sizes, styles, in_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            p["id"], p["name"], p["description"], p["price"], p["category"],
            p["tag"], p["image"], json.dumps(p["colors"]), json.dumps(p["sizes"]), json.dumps(p["styles"])
        ))

    # 3. Seed Sample Indian Orders
    order1_id = f"ORD-{datetime.date.today().strftime('%Y%m%d')}-IND101"
    cursor.execute("""
        INSERT OR REPLACE INTO orders (id, user_id, customer_name, customer_email, customer_phone, total, status, address, city, state, pincode, currency, shipping_fee, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, 'In Production', ?, ?, ?, ?, 'INR', 0.0, 'cod')
    """, (
        order1_id,
        customer_id,
        "Aarav Sharma",
        "customer@painite.studio",
        "+91 98450 12345",
        2998.00,
        "Flat 402, Signature Towers, 12th Main Road, Indiranagar",
        "Bengaluru",
        "Karnataka",
        "560038"
    ))

    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order1_id,))
    cursor.execute("""
        INSERT INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_ind_01", order1_id, "p2", "Noir Studio Oversized Tee", 1499.00, 1, "Onyx Black", "L", "Oversized", "PAINITE ATELIER", ""
    ))
    cursor.execute("""
        INSERT INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_ind_02", order1_id, "p4", "Atelier 280 GSM Custom Heavyweight Blank", 1499.00, 1, "Kora White", "M", "Boxy", "BOMBAY SUB-CULTURE", ""
    ))

    order2_id = f"ORD-{datetime.date.today().strftime('%Y%m%d')}-IND202"
    cursor.execute("""
        INSERT OR REPLACE INTO orders (id, user_id, customer_name, customer_email, customer_phone, total, status, address, city, state, pincode, currency, shipping_fee, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, 'Shipped', ?, ?, ?, ?, 'INR', 0.0, 'upi')
    """, (
        order2_id,
        customer_id,
        "Aarav Sharma",
        "customer@painite.studio",
        "+91 98450 12345",
        1799.00,
        "Bungalow 7, Perry Cross Road, Bandra West",
        "Mumbai",
        "Maharashtra",
        "400050"
    ))

    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order2_id,))
    cursor.execute("""
        INSERT INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_ind_03", order2_id, "p3", "Form / Function Architectural Tee", 1799.00, 1, "Chai Sand", "XL", "Boxy", "NOT JUST A T-SHIRT", ""
    ))

    conn.commit()
    conn.close()
    print("Database successfully seeded with Indian Streetwear & INR catalog.")
