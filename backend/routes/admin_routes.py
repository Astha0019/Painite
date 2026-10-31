import uuid
import json
import datetime
from flask import Blueprint, request, jsonify
from backend.database import get_db_connection
from backend.models import (
    order_to_dict, product_to_dict, user_to_dict,
    category_to_dict, coupon_to_dict, banner_to_dict, format_inr
)
from backend.auth import get_current_user

admin_bp = Blueprint("admin", __name__)

def check_admin_access():
    user = get_current_user()
    if not user:
        return False, jsonify({"detail": "Authentication required. Please sign in as an administrator."}), 401
    if user.get("role") != "admin":
        return False, jsonify({"detail": "Administrator privileges required."}), 403
    return True, user, 200

@admin_bp.before_request
def require_admin():
    if request.method == "OPTIONS":
        return None
    ok, resp, code = check_admin_access()
    if not ok:
        return resp, code

# =============================================================================
# 1. ANALYTICS & STATS
# =============================================================================

@admin_bp.route("/stats", methods=["GET"])
def get_stats():
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

    # Low stock items (< 15 units)
    cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE stock_quantity < 15 OR in_stock = 0")
    low_stock_count = int(cursor.fetchone()["cnt"])

    # Average Order Value (AOV)
    aov = (revenue / orders_count) if orders_count > 0 else 0.0

    conn.close()
    return jsonify({
        "revenue": round(revenue, 2),
        "currency": "INR",
        "formatted_revenue": format_inr(revenue),
        "orders": orders_count,
        "products": products_count,
        "customers": customers_count,
        "low_stock_count": low_stock_count,
        "aov": round(aov, 2),
        "formatted_aov": format_inr(aov)
    })

@admin_bp.route("/analytics", methods=["GET"])
def get_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Category Sales breakdown
    cursor.execute("""
        SELECT p.category, COUNT(oi.id) as units_sold, COALESCE(SUM(oi.price * oi.quantity), 0) as sales_volume
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        GROUP BY p.category
        ORDER BY sales_volume DESC
    """)
    category_sales = []
    for row in cursor.fetchall():
        category_sales.append({
            "category": row["category"],
            "units_sold": row["units_sold"],
            "sales_volume": round(float(row["sales_volume"]), 2),
            "formatted_volume": format_inr(row["sales_volume"])
        })

    # Orders by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM orders
        GROUP BY status
    """)
    status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    # Recent 7 days revenue trend
    cursor.execute("""
        SELECT DATE(created_at) as order_date, COALESCE(SUM(total), 0) as daily_revenue, COUNT(*) as daily_orders
        FROM orders
        WHERE status != 'Cancelled'
        GROUP BY DATE(created_at)
        ORDER BY order_date DESC
        LIMIT 7
    """)
    trend_rows = cursor.fetchall()
    daily_trend = []
    for r in reversed(trend_rows):
        daily_trend.append({
            "date": r["order_date"],
            "revenue": round(float(r["daily_revenue"]), 2),
            "orders": r["daily_orders"]
        })

    # Top 5 Bestselling Products
    cursor.execute("""
        SELECT p.id, p.name, p.category, p.price, p.image, p.stock_quantity,
               COALESCE(SUM(oi.quantity), 0) as total_sold
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        GROUP BY p.id
        ORDER BY total_sold DESC, p.price DESC
        LIMIT 5
    """)
    top_products = []
    for row in cursor.fetchall():
        top_products.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": float(row["price"]),
            "formatted_price": format_inr(row["price"]),
            "image": row["image"],
            "stock_quantity": row["stock_quantity"],
            "total_sold": row["total_sold"]
        })

    conn.close()
    return jsonify({
        "category_sales": category_sales,
        "status_distribution": status_counts,
        "daily_trend": daily_trend,
        "top_products": top_products
    })

# =============================================================================
# 2. PRODUCTS & INVENTORY MANAGEMENT
# =============================================================================

@admin_bp.route("/products", methods=["GET"])
def get_admin_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY created_at DESC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([product_to_dict(r) for r in rows])

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
    image = data.get("image") or "/static/images/products/mc01.jpg"
    description = data.get("description") or "Painite atelier bespoke garment."
    color_hex = data.get("color_hex") or "#101114"
    colors = data.get("colors") or ["Onyx Black", "Kora White"]
    sizes = data.get("sizes") or ["S", "M", "L", "XL", "XXL"]
    styles = data.get("styles") or ["Oversized", "Boxy"]
    stock_quantity = int(data.get("stock_quantity", 25))

    if not name:
        return jsonify({"detail": "Product name is required"}), 400
    try:
        price = float(price)
        if price <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"detail": "Valid product price is required"}), 400

    # Enforce Luxury Price Caps
    is_jacket = "jacket" in category.lower() or "jacket" in name.lower()
    if is_jacket:
        if price > 2000.0:
            msg = "Price Violation: Jacket prices must never exceed ₹2,000."
            return jsonify({"detail": msg, "error": msg}), 400
    else:
        if price > 1500.0:
            msg = "Price Violation: T-shirt and apparel prices must never exceed ₹1,500."
            return jsonify({"detail": msg, "error": msg}), 400

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
            colors, sizes, styles, in_stock, stock_quantity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        prod_id, name, description, price, orig_price_val, discount_pct,
        category, gender, collection, tag, image, color_hex,
        colors_json, sizes_json, styles_json, stock_quantity
    ))
    conn.commit()

    cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
    row = cursor.fetchone()
    conn.close()

    return jsonify(product_to_dict(row)), 201

@admin_bp.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"detail": "Product not found"}), 404

    name = (data.get("name") or existing["name"]).strip()
    price = data.get("price", existing["price"])
    original_price = data.get("original_price", existing["original_price"])
    category = (data.get("category") or existing["category"]).strip()
    gender = (data.get("gender") or existing["gender"]).strip()
    collection = (data.get("collection") or existing["collection"]).strip()
    tag = data.get("tag", existing["tag"])
    image = data.get("image", existing["image"])
    description = data.get("description", existing["description"])
    color_hex = data.get("color_hex", existing["color_hex"])
    stock_quantity = int(data.get("stock_quantity", existing["stock_quantity"] or 0))
    in_stock = int(data.get("in_stock", 1 if stock_quantity > 0 else 0))

    try:
        price = float(price)
        if price <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        conn.close()
        return jsonify({"detail": "Valid product price is required"}), 400

    # Price caps enforcement
    is_jacket = "jacket" in category.lower() or "jacket" in name.lower()
    if is_jacket and price > 2000.0:
        conn.close()
        msg = "Price Violation: Jacket prices must never exceed ₹2,000."
        return jsonify({"detail": msg, "error": msg}), 400
    elif not is_jacket and price > 1500.0:
        conn.close()
        msg = "Price Violation: T-shirt and apparel prices must never exceed ₹1,500."
        return jsonify({"detail": msg, "error": msg}), 400

    orig_price_val = None
    discount_pct = 0
    if original_price:
        try:
            orig_price_val = float(original_price)
            if orig_price_val > price:
                discount_pct = round(((orig_price_val - price) / orig_price_val) * 100)
        except (TypeError, ValueError):
            pass

    colors = data.get("colors")
    colors_json = json.dumps(colors) if colors is not None else existing["colors"]

    sizes = data.get("sizes")
    sizes_json = json.dumps(sizes) if sizes is not None else existing["sizes"]

    styles = data.get("styles")
    styles_json = json.dumps(styles) if styles is not None else existing["styles"]

    cursor.execute("""
        UPDATE products SET
            name = ?, description = ?, price = ?, original_price = ?,
            discount_pct = ?, category = ?, gender = ?, collection = ?,
            tag = ?, image = ?, color_hex = ?, colors = ?, sizes = ?,
            styles = ?, in_stock = ?, stock_quantity = ?
        WHERE id = ?
    """, (
        name, description, price, orig_price_val, discount_pct,
        category, gender, collection, tag, image, color_hex,
        colors_json, sizes_json, styles_json, in_stock, stock_quantity,
        product_id
    ))
    conn.commit()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return jsonify(product_to_dict(updated_row)), 200

@admin_bp.route("/products/<product_id>/stock", methods=["PATCH"])
def update_product_stock(product_id):
    data = request.get_json(silent=True) or {}
    stock_quantity = data.get("stock_quantity")
    in_stock = data.get("in_stock")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"detail": "Product not found"}), 404

    new_stock = int(stock_quantity) if stock_quantity is not None else int(row["stock_quantity"] or 0)
    new_in_stock = int(in_stock) if in_stock is not None else (1 if new_stock > 0 else 0)

    cursor.execute("UPDATE products SET stock_quantity = ?, in_stock = ? WHERE id = ?", (new_stock, new_in_stock, product_id))
    conn.commit()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return jsonify(product_to_dict(updated_row)), 200

@admin_bp.route("/products/<product_id>/price", methods=["PATCH"])
def update_product_price(product_id):
    data = request.get_json(silent=True) or {}
    price = data.get("price")
    original_price = data.get("original_price")

    if price is None:
        return jsonify({"detail": "Price is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"detail": "Product not found"}), 404

    try:
        price = float(price)
        if price <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        conn.close()
        return jsonify({"detail": "Valid price is required"}), 400

    cat = row["category"]
    is_jacket = "jacket" in cat.lower() or "jacket" in row["name"].lower()
    if is_jacket and price > 2000.0:
        conn.close()
        msg = "Price Violation: Jacket prices must never exceed ₹2,000."
        return jsonify({"detail": msg, "error": msg}), 400
    elif not is_jacket and price > 1500.0:
        conn.close()
        msg = "Price Violation: T-shirt and apparel prices must never exceed ₹1,500."
        return jsonify({"detail": msg, "error": msg}), 400

    orig_price_val = float(original_price) if original_price else row["original_price"]
    discount_pct = 0
    if orig_price_val and orig_price_val > price:
        discount_pct = round(((orig_price_val - price) / orig_price_val) * 100)

    cursor.execute("UPDATE products SET price = ?, original_price = ?, discount_pct = ? WHERE id = ?", (price, orig_price_val, discount_pct, product_id))
    conn.commit()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return jsonify(product_to_dict(updated_row)), 200

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

# =============================================================================
# 3. CATEGORIES MANAGEMENT
# =============================================================================

@admin_bp.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY display_order ASC, name ASC")
    cat_rows = cursor.fetchall()

    results = []
    for c in cat_rows:
        cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE category = ?", (c["name"],))
        p_cnt = cursor.fetchone()["cnt"]
        results.append(category_to_dict(c, p_cnt))

    conn.close()
    return jsonify(results)

@admin_bp.route("/categories", methods=["POST"])
def add_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    display_order = int(data.get("display_order", 0))

    if not name:
        return jsonify({"detail": "Category name is required"}), 400

    cat_id = f"cat_{uuid.uuid4().hex[:6]}"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO categories (id, name, description, display_order)
            VALUES (?, ?, ?, ?)
        """, (cat_id, name, description, display_order))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"detail": f"Category already exists: {e}"}), 400

    cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    row = cursor.fetchone()
    conn.close()
    return jsonify(category_to_dict(row, 0)), 201

@admin_bp.route("/categories/<category_id>", methods=["PUT"])
def update_category(category_id):
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"detail": "Category not found"}), 404

    name = (data.get("name") or row["name"]).strip()
    description = data.get("description", row["description"])
    display_order = int(data.get("display_order", row["display_order"]))
    is_active = int(data.get("is_active", row["is_active"]))

    # If name changed, optionally update existing products category
    old_name = row["name"]
    if name != old_name:
        cursor.execute("UPDATE products SET category = ? WHERE category = ?", (name, old_name))

    cursor.execute("""
        UPDATE categories SET name = ?, description = ?, display_order = ?, is_active = ?
        WHERE id = ?
    """, (name, description, display_order, is_active, category_id))
    conn.commit()

    cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    updated_row = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE category = ?", (name,))
    p_cnt = cursor.fetchone()["cnt"]
    conn.close()

    return jsonify(category_to_dict(updated_row, p_cnt)), 200

@admin_bp.route("/categories/<category_id>", methods=["DELETE"])
def delete_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"detail": "Category not found"}), 404

    # Check if products exist in category
    cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE category = ?", (row["name"],))
    cnt = cursor.fetchone()["cnt"]
    if cnt > 0:
        conn.close()
        return jsonify({"detail": f"Cannot delete category: {cnt} products are assigned to it. Reassign products first."}), 400

    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Category removed successfully"}), 200

# =============================================================================
# 4. ORDERS, PAYMENTS & FULFILLMENT
# =============================================================================

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

    valid_statuses = [
        "Confirmed", "Packed", "Shipped", "Out for Delivery", "Delivered",
        "Pending", "In Production", "Quality Check", "Cancelled"
    ]
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

    order_dict = order_to_dict(order_row, item_rows)

    # Dispatch WhatsApp lifecycle status notification to customer (+91 9359615919)
    try:
        from backend.services.whatsapp_service import send_order_status_notification
        wa_res = send_order_status_notification(order_dict, status)
        new_wa_status = wa_res.get("status") or f"Updated ({status})"
        cursor.execute("UPDATE orders SET whatsapp_status = ? WHERE id = ?", (new_wa_status, order_id))
        conn.commit()
        order_dict["whatsapp_status"] = new_wa_status
        order_dict["wa_link"] = wa_res.get("wa_link", "")
        order_dict["whatsapp_result"] = wa_res
    except Exception as e:
        print(f"[Admin] WhatsApp status notification error: {e}")

    conn.close()
    return jsonify(order_dict)

@admin_bp.route("/orders/<order_id>/payment", methods=["PATCH"])
def update_order_payment(order_id):
    data = request.get_json(silent=True) or {}
    payment_status = data.get("payment_status")
    valid_payment_statuses = ["Paid", "Pending", "Failed", "Refunded"]
    if not payment_status or payment_status not in valid_payment_statuses:
        return jsonify({"detail": f"Invalid payment status. Must be: {', '.join(valid_payment_statuses)}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"detail": "Order not found"}), 404

    cursor.execute("UPDATE orders SET payment_status = ? WHERE id = ?", (payment_status, order_id))
    conn.commit()

    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order_row = cursor.fetchone()
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    item_rows = cursor.fetchall()
    order_dict = order_to_dict(order_row, item_rows)

    # Dispatch WhatsApp notification for payment status update
    try:
        from backend.services.whatsapp_service import send_order_status_notification
        wa_res = send_order_status_notification(order_dict, f"Payment {payment_status}")
        new_wa_status = wa_res.get("status") or f"Payment ({payment_status})"
        cursor.execute("UPDATE orders SET whatsapp_status = ? WHERE id = ?", (new_wa_status, order_id))
        conn.commit()
        order_dict["whatsapp_status"] = new_wa_status
        order_dict["wa_link"] = wa_res.get("wa_link", "")
    except Exception as e:
        print(f"[Admin] WhatsApp payment notification error: {e}")

    conn.close()
    return jsonify(order_dict), 200

@admin_bp.route("/orders/<order_id>/tracking", methods=["PATCH"])
def update_order_tracking(order_id):
    data = request.get_json(silent=True) or {}
    tracking_number = data.get("tracking_number", "").strip()
    delivery_date = data.get("estimated_delivery_date", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"detail": "Order not found"}), 404

    cursor.execute("""
        UPDATE orders SET tracking_number = ?, estimated_delivery_date = ?
        WHERE id = ?
    """, (tracking_number, delivery_date, order_id))
    conn.commit()

    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order_row = cursor.fetchone()
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    item_rows = cursor.fetchall()
    order_dict = order_to_dict(order_row, item_rows)

    # Dispatch WhatsApp notification for courier tracking update
    try:
        from backend.services.whatsapp_service import send_order_status_notification
        wa_res = send_order_status_notification(order_dict, "Tracking Updated")
        new_wa_status = wa_res.get("status") or "Tracking Assigned"
        cursor.execute("UPDATE orders SET whatsapp_status = ? WHERE id = ?", (new_wa_status, order_id))
        conn.commit()
        order_dict["whatsapp_status"] = new_wa_status
        order_dict["wa_link"] = wa_res.get("wa_link", "")
    except Exception as e:
        print(f"[Admin] WhatsApp tracking notification error: {e}")

    conn.close()
    return jsonify(order_dict), 200

@admin_bp.route("/orders/<order_id>/notify", methods=["POST"])
def send_order_full_update(order_id):
    """
    Sends the complete, comprehensive all-in-one order status, tracking, and delivery
    update report directly to the customer's WhatsApp.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        conn.close()
        return jsonify({"detail": "Order not found"}), 404

    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    item_rows = cursor.fetchall()
    order_dict = order_to_dict(order_row, item_rows)

    from backend.services.whatsapp_service import send_complete_order_update_notification
    wa_res = send_complete_order_update_notification(order_dict)

    new_wa_status = wa_res.get("status") or "Update Dispatched"
    cursor.execute("UPDATE orders SET whatsapp_status = ? WHERE id = ?", (new_wa_status, order_id))
    conn.commit()
    conn.close()

    order_dict["whatsapp_status"] = new_wa_status
    order_dict["wa_link"] = wa_res.get("wa_link", "")

    return jsonify({
        "success": True,
        "message": f"Complete order update sent to patron {order_dict['customer_name']}!",
        "status": new_wa_status,
        "wa_link": wa_res.get("wa_link", ""),
        "order": order_dict
    }), 200

@admin_bp.route("/orders/notify-all", methods=["POST"])
def send_all_orders_updates():
    """
    Broadcasts the latest order updates to customers across all active orders.
    """
    data = request.get_json(silent=True) or {}
    order_ids = data.get("order_ids")

    conn = get_db_connection()
    cursor = conn.cursor()

    if order_ids and isinstance(order_ids, list):
        placeholders = ",".join(["?"] * len(order_ids))
        cursor.execute(f"SELECT * FROM orders WHERE id IN ({placeholders})", order_ids)
    else:
        # Default to all active (non-delivered, non-cancelled) orders
        cursor.execute("SELECT * FROM orders WHERE status NOT IN ('Delivered', 'Cancelled') ORDER BY created_at DESC LIMIT 25")

    orders = cursor.fetchall()

    from backend.services.whatsapp_service import send_complete_order_update_notification
    results = []

    for o in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
        item_rows = cursor.fetchall()
        order_dict = order_to_dict(o, item_rows)
        wa_res = send_complete_order_update_notification(order_dict)
        results.append({
            "order_id": o["id"],
            "customer_phone": order_dict["customer_phone"],
            "status": wa_res.get("status"),
            "wa_link": wa_res.get("wa_link")
        })

    conn.close()
    return jsonify({
        "success": True,
        "total_notified": len(results),
        "results": results
    }), 200

# =============================================================================
# 5. CUSTOMERS MANAGEMENT
# =============================================================================

@admin_bp.route("/customers", methods=["GET"])
def get_customers():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.name, u.email, u.created_at,
               COUNT(o.id) as total_orders,
               COALESCE(SUM(o.total), 0) as total_spent,
               MAX(o.created_at) as last_order_date,
               MAX(o.customer_phone) as phone,
               MAX(o.city) as city
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id AND o.status != 'Cancelled'
        WHERE u.role = 'customer'
        GROUP BY u.id
        ORDER BY total_spent DESC, total_orders DESC
    """)
    rows = cursor.fetchall()
    customers = []
    for r in rows:
        customers.append({
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "phone": r["phone"] or "Not provided",
            "city": r["city"] or "India",
            "total_orders": r["total_orders"],
            "total_spent": round(float(r["total_spent"]), 2),
            "formatted_spent": format_inr(r["total_spent"]),
            "last_order_date": r["last_order_date"],
            "created_at": r["created_at"]
        })
    conn.close()
    return jsonify(customers)

# =============================================================================
# 6. COUPONS & DISCOUNTS MANAGEMENT
# =============================================================================

@admin_bp.route("/coupons", methods=["GET"])
def get_coupons():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([coupon_to_dict(r) for r in rows])

@admin_bp.route("/coupons", methods=["POST"])
def add_coupon():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()
    discount_type = (data.get("discount_type") or "percentage").strip().lower()
    discount_value = data.get("discount_value")
    min_order_amount = float(data.get("min_order_amount", 0.0))
    max_discount_amount = data.get("max_discount_amount")
    expires_at = data.get("expires_at", "2026-12-31")

    if not code:
        return jsonify({"detail": "Coupon code is required"}), 400
    try:
        discount_value = float(discount_value)
        if discount_value <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"detail": "Valid discount value is required"}), 400

    max_disc_val = float(max_discount_amount) if max_discount_amount else None
    coupon_id = f"cpn_{uuid.uuid4().hex[:6]}"

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO coupons (id, code, discount_type, discount_value, min_order_amount, max_discount_amount, is_active, usage_count, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?)
        """, (coupon_id, code, discount_type, discount_value, min_order_amount, max_disc_val, expires_at))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"detail": f"Coupon code already exists: {e}"}), 400

    cursor.execute("SELECT * FROM coupons WHERE id = ?", (coupon_id,))
    row = cursor.fetchone()
    conn.close()
    return jsonify(coupon_to_dict(row)), 201

@admin_bp.route("/coupons/<coupon_id>/toggle", methods=["PATCH"])
def toggle_coupon(coupon_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coupons WHERE id = ?", (coupon_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"detail": "Coupon not found"}), 404

    new_state = 0 if row["is_active"] else 1
    cursor.execute("UPDATE coupons SET is_active = ? WHERE id = ?", (new_state, coupon_id))
    conn.commit()

    cursor.execute("SELECT * FROM coupons WHERE id = ?", (coupon_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return jsonify(coupon_to_dict(updated_row)), 200

@admin_bp.route("/coupons/<coupon_id>", methods=["DELETE"])
def delete_coupon(coupon_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM coupons WHERE id = ?", (coupon_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Coupon deleted successfully"}), 200

# =============================================================================
# 7. WEBSITE BANNERS & ANNOUNCEMENTS MANAGEMENT
# =============================================================================

@admin_bp.route("/banners", methods=["GET"])
def get_admin_banners():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM banners ORDER BY sort_order ASC, created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([banner_to_dict(r) for r in rows])

@admin_bp.route("/banners", methods=["POST"])
def add_banner():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    subtitle = (data.get("subtitle") or "").strip()
    badge_text = (data.get("badge_text") or "").strip()
    button_text = (data.get("button_text") or "Explore Collection").strip()
    button_link = (data.get("button_link") or "#/shop").strip()
    image_url = data.get("image_url") or ""
    bg_gradient = data.get("bg_gradient") or "linear-gradient(135deg, rgba(250,247,242,0.95), rgba(252,238,233,0.85))"
    position = (data.get("position") or "hero").strip()
    sort_order = int(data.get("sort_order", 0))

    if not title:
        return jsonify({"detail": "Banner title is required"}), 400

    banner_id = f"bnr_{uuid.uuid4().hex[:6]}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO banners (id, title, subtitle, badge_text, button_text, button_link, image_url, bg_gradient, position, is_active, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (banner_id, title, subtitle, badge_text, button_text, button_link, image_url, bg_gradient, position, sort_order))
    conn.commit()

    cursor.execute("SELECT * FROM banners WHERE id = ?", (banner_id,))
    row = cursor.fetchone()
    conn.close()
    return jsonify(banner_to_dict(row)), 201

@admin_bp.route("/banners/<banner_id>", methods=["PUT"])
def update_banner(banner_id):
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM banners WHERE id = ?", (banner_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"detail": "Banner not found"}), 404

    title = (data.get("title") or row["title"]).strip()
    subtitle = data.get("subtitle", row["subtitle"])
    badge_text = data.get("badge_text", row["badge_text"])
    button_text = data.get("button_text", row["button_text"])
    button_link = data.get("button_link", row["button_link"])
    image_url = data.get("image_url", row["image_url"])
    bg_gradient = data.get("bg_gradient", row["bg_gradient"])
    position = data.get("position", row["position"])
    sort_order = int(data.get("sort_order", row["sort_order"]))
    is_active = int(data.get("is_active", row["is_active"]))

    cursor.execute("""
        UPDATE banners SET
            title = ?, subtitle = ?, badge_text = ?, button_text = ?,
            button_link = ?, image_url = ?, bg_gradient = ?, position = ?,
            sort_order = ?, is_active = ?
        WHERE id = ?
    """, (title, subtitle, badge_text, button_text, button_link, image_url, bg_gradient, position, sort_order, is_active, banner_id))
    conn.commit()

    cursor.execute("SELECT * FROM banners WHERE id = ?", (banner_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return jsonify(banner_to_dict(updated_row)), 200

@admin_bp.route("/banners/<banner_id>/toggle", methods=["PATCH"])
def toggle_banner(banner_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM banners WHERE id = ?", (banner_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"detail": "Banner not found"}), 404

    new_state = 0 if row["is_active"] else 1
    cursor.execute("UPDATE banners SET is_active = ? WHERE id = ?", (new_state, banner_id))
    conn.commit()

    cursor.execute("SELECT * FROM banners WHERE id = ?", (banner_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return jsonify(banner_to_dict(updated_row)), 200

@admin_bp.route("/banners/<banner_id>", methods=["DELETE"])
def delete_banner(banner_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banners WHERE id = ?", (banner_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Banner deleted successfully"}), 200

# =============================================================================
# 8. WHATSAPP MESSAGING SYSTEM MANAGEMENT
# =============================================================================

@admin_bp.route("/whatsapp/status", methods=["GET"])
def get_whatsapp_status():
    from backend.services.whatsapp_service import get_whatsapp_system_status
    return jsonify(get_whatsapp_system_status()), 200

@admin_bp.route("/whatsapp/settings", methods=["POST"])
def save_whatsapp_settings():
    from backend.services.whatsapp_service import update_whatsapp_settings
    data = request.get_json(silent=True) or {}
    updated = update_whatsapp_settings(
        business_number=data.get("business_number"),
        phone_number_id=data.get("phone_number_id"),
        access_token=data.get("access_token"),
        api_version=data.get("api_version"),
        template_name=data.get("template_name")
    )
    return jsonify(updated), 200

@admin_bp.route("/whatsapp/send", methods=["POST"])
def send_whatsapp_message():
    from backend.services.whatsapp_service import send_custom_whatsapp
    data = request.get_json(silent=True) or {}
    recipient_phone = data.get("phone") or data.get("recipient_phone")
    recipient_name = data.get("name") or data.get("recipient_name") or "Valued Patron"
    message_text = data.get("message") or data.get("message_text")
    order_id = data.get("order_id")

    if not recipient_phone or not message_text:
        return jsonify({"detail": "Phone number and message text are required"}), 400

    result = send_custom_whatsapp(
        recipient_phone=recipient_phone,
        recipient_name=recipient_name,
        message_text=message_text,
        order_id=order_id,
        message_type="admin_custom"
    )
    return jsonify(result), 200

@admin_bp.route("/whatsapp/test", methods=["POST"])
def send_whatsapp_test():
    from backend.services.whatsapp_service import send_custom_whatsapp
    data = request.get_json(silent=True) or {}
    phone = data.get("phone")
    if not phone:
        return jsonify({"detail": "Recipient phone number is required"}), 400

    test_message = (
        "✨ *PAINITE ATELIER — WHATSAPP TEST* ✨\n\n"
        "This is an automated test from PAINITE Executive Studio.\n"
        "Your WhatsApp Business Messaging System is operational and connected!\n\n"
        "— _PAINITE Concierge Support: +91 9359615919_"
    )
    result = send_custom_whatsapp(
        recipient_phone=phone,
        recipient_name="Studio Admin",
        message_text=test_message,
        message_type="test"
    )
    return jsonify(result), 200

@admin_bp.route("/whatsapp/logs", methods=["GET"])
def get_whatsapp_logs():
    from backend.services.whatsapp_service import get_recent_whatsapp_logs
    logs = get_recent_whatsapp_logs(limit=100)
    return jsonify(logs), 200
