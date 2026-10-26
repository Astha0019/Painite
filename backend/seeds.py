import json
import uuid
import datetime
from backend.database import get_db_connection
from backend.auth import hash_password

def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM products")
    if cursor.fetchone()["cnt"] > 0:
        conn.close()
        return

    print("Seeding Painite Studio database...")

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
        "Alex Mercer",
        "customer@painite.studio",
        hash_password("PainiteUser!42"),
        "customer"
    ))

    # 2. Seed Products
    products = [
        {
            "id": "p1",
            "name": "The Essential Tee",
            "description": "Heavyweight 240 GSM combed cotton blank engineered for daily wear with a structured, relaxed drape.",
            "price": 42.00,
            "category": "Core",
            "tag": "BESTSELLER",
            "image": "/static/images/essential-tee.jpg",
            "colors": ["Black", "White", "Slate", "Sage"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Oversized", "Boxy"]
        },
        {
            "id": "p2",
            "name": "Noir Studio Tee",
            "description": "Garment-dyed carbon black blank with double-needle ribbed collar and subtle enzyme wash treatment.",
            "price": 48.00,
            "category": "Studio",
            "tag": "NEW ARRIVAL",
            "image": "/static/images/noir-studio-tee.jpg",
            "colors": ["Black", "Slate", "White"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Classic", "Oversized"]
        },
        {
            "id": "p3",
            "name": "Form / Function Tee",
            "description": "Architectural silhouette featuring drop shoulders, clean lines, and custom typographic chest balance.",
            "price": 55.00,
            "category": "Edition 01",
            "tag": "LIMITED",
            "image": "/static/images/form-function-tee.jpg",
            "colors": ["White", "Sand", "Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "p4",
            "name": "Atelier Heavyweight Blank",
            "description": "Premium dense knit 280 GSM cotton crafted specifically for bespoke studio custom graphics.",
            "price": 50.00,
            "category": "Core",
            "tag": "CORE",
            "image": "/static/images/essential-tee.jpg",
            "colors": ["Black", "White", "Sage", "Sand"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Oversized"]
        },
        {
            "id": "p5",
            "name": "Archival Monolith Tee",
            "description": "Limited studio series exploring proportions, subtle tonal branding, and archival stitching.",
            "price": 62.00,
            "category": "Studio",
            "tag": "LIMITED",
            "image": "/static/images/noir-studio-tee.jpg",
            "colors": ["Black", "Slate"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "p6",
            "name": "Kinetic Raw Hem Tee",
            "description": "Deconstructed relaxed fit with reinforced binding and signature Painite Studio minimal branding.",
            "price": 58.00,
            "category": "Edition 01",
            "tag": "NEW ARRIVAL",
            "image": "/static/images/form-function-tee.jpg",
            "colors": ["White", "Black", "Sand"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Classic", "Relaxed"]
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

    # 3. Seed Sample Orders
    order1_id = f"ORD-{datetime.date.today().strftime('%Y%m%d')}-A101"
    cursor.execute("""
        INSERT INTO orders (id, user_id, customer_name, customer_email, total, status, address, payment_method)
        VALUES (?, ?, ?, ?, ?, 'In Production', ?, 'cod')
    """, (
        order1_id,
        customer_id,
        "Alex Mercer",
        "customer@painite.studio",
        97.00,
        "742 Evergreen Terrace, Suite 4B, New York, NY 10001"
    ))

    cursor.execute("""
        INSERT INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_01", order1_id, "p2", "Noir Studio Tee", 48.00, 1, "Black", "L", "Oversized", "PAINITE STUDIO", ""
    ))
    cursor.execute("""
        INSERT INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_02", order1_id, "p1", "The Essential Tee", 49.00, 1, "White", "M", "Classic", "ATELIER 01", ""
    ))

    order2_id = f"ORD-{datetime.date.today().strftime('%Y%m%d')}-B202"
    cursor.execute("""
        INSERT INTO orders (id, user_id, customer_name, customer_email, total, status, address, payment_method)
        VALUES (?, ?, ?, ?, ?, 'Shipped', ?, 'cod')
    """, (
        order2_id,
        customer_id,
        "Alex Mercer",
        "customer@painite.studio",
        55.00,
        "742 Evergreen Terrace, Suite 4B, New York, NY 10001"
    ))

    cursor.execute("""
        INSERT INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_03", order2_id, "p3", "Form / Function Tee", 55.00, 1, "Sand", "XL", "Boxy", "NOT JUST A TEE", ""
    ))

    conn.commit()
    conn.close()
    print("Database successfully seeded.")
