import uuid
import datetime
import re
from flask import Blueprint, request, jsonify, g
from backend.database import get_db_connection
from backend.models import order_to_dict
from backend.auth import get_current_user, require_auth

order_bp = Blueprint("orders", __name__)

@order_bp.route("/orders", methods=["POST"])
def create_order():
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    items = data.get("items") or []
    if not items or not isinstance(items, list):
        return jsonify({"detail": "Shopping bag is empty. Please add items before placing order."}), 400

    address = (data.get("address") or "").strip()
    if not address:
        return jsonify({"detail": "Delivery address is required."}), 400

    city = (data.get("city") or "").strip()
    state = (data.get("state") or "").strip()
    pincode = (data.get("pincode") or "").strip()
    phone = (data.get("customer_phone") or data.get("phone") or "").strip()

    # If pincode provided, validate 6 digits Indian PIN code
    if pincode and not re.match(r"^\d{6}$", pincode):
        return jsonify({"detail": "Please enter a valid 6-digit Indian PIN code."}), 400

    # If phone provided, sanitize and check 10 digits
    if phone:
        clean_phone = re.sub(r"[^\d]", "", phone)
        if clean_phone.startswith("91") and len(clean_phone) == 12:
            clean_phone = clean_phone[2:]
        if len(clean_phone) != 10:
            return jsonify({"detail": "Please enter a valid 10-digit Indian mobile number."}), 400
        phone = f"+91 {clean_phone[:5]} {clean_phone[5:]}"

    payment_method = data.get("payment_method") or "cod"

    # User identification
    user_id = user["id"] if user else None
    customer_name = (data.get("customer_name") or (user["name"] if user else "Studio Patron")).strip()
    customer_email = (data.get("customer_email") or (user["email"] if user else "patron@painite.studio")).strip()

    # Calculate and verify total in INR
    items_total = 0.0
    processed_items = []
    for item in items:
        qty = int(item.get("quantity") or 1)
        price = float(item.get("price") or 0.0)
        items_total += price * qty
        processed_items.append({
            "id": f"item_{uuid.uuid4().hex[:10]}",
            "product_id": item.get("id") or item.get("product_id") or "custom",
            "product_name": item.get("name") or "Painite Bespoke Garment",
            "price": price,
            "quantity": qty,
            "color": item.get("color") or "Onyx Black",
            "size": item.get("size") or "M",
            "style": item.get("style") or "Oversized",
            "custom_text": item.get("custom_text") or item.get("text") or "",
            "artwork_url": item.get("artwork_url") or item.get("uploaded") or ""
        })

    # Free shipping on ₹999+ in India
    shipping_fee = 0.0 if items_total >= 999.0 else 99.0
    final_total = round(items_total + shipping_fee, 2)

    order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (id, user_id, customer_name, customer_email, customer_phone, total, status, address, city, state, pincode, currency, shipping_fee, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?, 'INR', ?, ?)
    """, (
        order_id, user_id, customer_name, customer_email, phone,
        final_total, address, city, state, pincode, shipping_fee, payment_method
    ))

    for item in processed_items:
        cursor.execute("""
            INSERT INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["id"], order_id, item["product_id"], item["product_name"],
            item["price"], item["quantity"], item["color"], item["size"],
            item["style"], item["custom_text"], item["artwork_url"]
        ))

    conn.commit()

    # Fetch created order with items
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order_row = cursor.fetchone()
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    item_rows = cursor.fetchall()
    conn.close()

    return jsonify(order_to_dict(order_row, item_rows)), 201

@order_bp.route("/me/orders", methods=["GET"])
@order_bp.route("/orders/me", methods=["GET"])
@require_auth
def get_my_orders():
    user_id = g.current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    order_rows = cursor.fetchall()

    orders = []
    for o in order_rows:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
        item_rows = cursor.fetchall()
        orders.append(order_to_dict(o, item_rows))

    conn.close()
    return jsonify(orders)
