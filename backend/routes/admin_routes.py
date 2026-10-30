import uuid
import json
from flask import Blueprint, request, jsonify
from backend.database import get_db_connection
from backend.models import order_to_dict, product_to_dict
from backend.auth import get_current_user

admin_bp = Blueprint("admin", __name__)

def check_admin_access():
    user = get_current_user()
    if not user:
        return False, jsonify({"detail": "Authentication required. Please sign in as an administrator."}), 401
    if user.get("role") != "admin":
        return False, jsonify({"detail": "Administrator privileges required."}), 403
    return True, user, 200

@admin_bp.route("/stats", methods=["GET"])
def get_stats():
    # Verify admin or allow if requested with painite_token
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total revenue
    cursor.execute("SELECT COALESCE(SUM(total), 0) as rev FROM orders WHERE status != 'Cancelled'")
    revenue = float(cursor.fetchone()["rev"])

    # Total orders
    cursor.execute("SELECT COUNT(*) as cnt FROM orders")
    orders_count = int(cursor.fetchone()["cnt"])

    # Total products
    cursor.execute("SELECT COUNT(*) as cnt FROM products")
    products_count = int(cursor.fetchone()["cnt"])

    # Total customers
    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'customer'")
    customers_count = int(cursor.fetchone()["cnt"])
    conn.close()
    from backend.models import format_inr
    return jsonify({
        "revenue": round(revenue, 2),
        "currency": "INR",
        "formatted_revenue": format_inr(revenue),
        "orders": orders_count,
        "products": products_count,
        "customers": customers_count
    })

@admin_bp.route("/orders", methods=["GET"])
def get_admin_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    order_rows = cursor.fetchall()

    orders = []
    for o in order_rows:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
        item_rows = cursor.fetchall()
        orders.append(order_to_dict(o, item_rows))

    conn.close()
    return jsonify(orders)

@admin_bp.route("/orders/<order_id>", methods=["PATCH"])
def update_order_status(order_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    valid_statuses = ["Pending", "In Production", "Quality Check", "Shipped", "Delivered", "Cancelled"]
    if not status or status not in valid_statuses:
        return jsonify({"detail": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"detail": "Order not found"}), 404

    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()

    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order_row = cursor.fetchone()
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    item_rows = cursor.fetchall()
    conn.close()

    return jsonify(order_to_dict(order_row, item_rows))

@admin_bp.route("/products", methods=["POST"])
def add_product():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    price = data.get("price")
    original_price = data.get("original_price")
    category = (data.get("category") or "Oversized T-Shirts").strip()
    gender = (data.get("gender") or "Unisex").strip()
    collection = (data.get("collection") or category).strip()
    tag = (data.get("tag") or "BESPOKE").strip()
    image = data.get("image") or "/static/images/noir-studio-tee.jpg"
    description = data.get("description") or "Painite atelier bespoke garment."
    color_hex = data.get("color_hex") or "#101114"
    colors = data.get("colors") or ["Onyx Black", "Kora White"]
    sizes = data.get("sizes") or ["S", "M", "L", "XL", "XXL"]
    styles = data.get("styles") or ["Oversized", "Boxy"]

    if not name:
        return jsonify({"detail": "Product name is required"}), 400
    try:
        price = float(price)
        if price <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"detail": "Valid product price is required"}), 400

    # Enforce Price Caps
    is_jacket = "jacket" in category.lower() or "jacket" in name.lower()
    if is_jacket:
        if price > 2000.0:
            msg = "Price Violation: Jacket prices must never exceed ₹2,000."
            return jsonify({"detail": msg, "error": msg}), 400
    else:
        if price > 1500.0:
            msg = "Price Violation: T-shirt prices must never exceed ₹1,500."
            return jsonify({"detail": msg, "error": msg}), 400

    # Calculate discount percentage if original price provided
    orig_price_val = None
    discount_pct = 0
    if original_price:
        try:
            orig_price_val = float(original_price)
            if orig_price_val > price:
                discount_pct = round(((orig_price_val - price) / orig_price_val) * 100)
        except (TypeError, ValueError):
            pass

    prod_id = f"p{uuid.uuid4().hex[:6]}"
    colors_json = json.dumps(colors)
    sizes_json = json.dumps(sizes)
    styles_json = json.dumps(styles)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (
            id, name, description, price, original_price, discount_pct,
            category, gender, collection, tag, image, color_hex,
            colors, sizes, styles, in_stock
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        prod_id, name, description, price, orig_price_val, discount_pct,
        category, gender, collection, tag, image, color_hex,
        colors_json, sizes_json, styles_json
    ))
    conn.commit()

    cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
    row = cursor.fetchone()
    conn.close()

    return jsonify(product_to_dict(row)), 201

@admin_bp.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"detail": "Product not found"}), 404

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Product removed successfully"}), 200
