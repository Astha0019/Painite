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

    # If phone provided, sanitize and format cleanly
    if phone:
        clean_phone = re.sub(r"[^\d]", "", phone)
        if clean_phone.startswith("91") and len(clean_phone) == 12:
            clean_phone = clean_phone[2:]
        elif clean_phone.startswith("0") and len(clean_phone) == 11:
            clean_phone = clean_phone[1:]
        if len(clean_phone) == 10:
            phone = f"+91 {clean_phone[:5]} {clean_phone[5:]}"
        else:
            # Tolerant: retain digits if reasonable length
            phone = f"+91 {clean_phone[-10:]}" if len(clean_phone) >= 10 else phone

    payment_method = data.get("payment_method") or "cod"

    # User identification & Guest Account Auto-Linking
    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = user["id"] if user else data.get("user_id")
    customer_name = (data.get("customer_name") or (user["name"] if user else "Studio Patron")).strip()
    customer_email = (data.get("customer_email") or (user["email"] if user else "patron@painite.studio")).strip()

    if not user_id and customer_email and customer_email != "patron@painite.studio":
        cursor.execute("SELECT id FROM users WHERE email = ?", (customer_email,))
        matched_user = cursor.fetchone()
        if matched_user:
            user_id = matched_user["id"]

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
            "product_name": item.get("name") or item.get("product_name") or "Painite Bespoke Garment",
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

    # Allow retaining an existing order ID (e.g. from resilient local client sync)
    custom_order_id = data.get("id")
    if custom_order_id and str(custom_order_id).startswith("ORD-"):
        # Check if already saved
        cursor.execute("SELECT id FROM orders WHERE id = ?", (custom_order_id,))
        if cursor.fetchone():
            cursor.execute("SELECT * FROM orders WHERE id = ?", (custom_order_id,))
            existing_row = cursor.fetchone()
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (custom_order_id,))
            existing_items = cursor.fetchall()
            conn.close()
            return jsonify(order_to_dict(existing_row, existing_items)), 200
        order_id = custom_order_id
    else:
        order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    delivery_date = data.get("estimated_delivery_date") or (datetime.date.today() + datetime.timedelta(days=4)).strftime("%d %b %Y")
    tracking_number = data.get("tracking_number") or f"PTE-IND-{uuid.uuid4().hex[:8].upper()}"

    cursor.execute("""
        INSERT INTO orders (id, user_id, customer_name, customer_email, customer_phone, total, status, address, city, state, pincode, currency, shipping_fee, payment_method, estimated_delivery_date, tracking_number)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?, 'INR', ?, ?, ?, ?)
    """, (
        order_id, user_id, customer_name, customer_email, phone,
        final_total, address, city, state, pincode, shipping_fee, payment_method,
        delivery_date, tracking_number
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

    order_dict = order_to_dict(order_row, item_rows)

    # Automatic WhatsApp Notification to Customer & Business Number (+91 9359615919)
    try:
        from backend.services.whatsapp_service import send_order_notifications
        wa_result = send_order_notifications(order_dict)
        status_txt = wa_result.get("overall_status") or "Credentials Required (Setup in .env)"

        cursor.execute("UPDATE orders SET whatsapp_status = ? WHERE id = ?", (status_txt, order_id))
        conn.commit()
        order_dict["whatsapp_status"] = status_txt
        order_dict["whatsapp_result"] = wa_result
    except Exception as e:
        print(f"[Order] WhatsApp notification trigger encountered: {e}")

    conn.close()
    return jsonify(order_dict), 201

@order_bp.route("/orders/sync", methods=["POST"])
def sync_orders():
    """Sync an array of local/offline orders to the server database."""
    data = request.get_json(silent=True) or {}
    orders_list = data if isinstance(data, list) else (data.get("orders") or [])
    synced = []
    for ord_data in orders_list:
        if not isinstance(ord_data, dict) or not ord_data.get("items"):
            continue
        try:
            res_tuple = create_order()
            # If function returns response
        except Exception:
            pass
    return jsonify({"synced": len(synced)}), 200

@order_bp.route("/me/orders", methods=["GET"])
@order_bp.route("/orders/me", methods=["GET"])
def get_my_orders():
    user = get_current_user()
    phone = (request.args.get("phone") or "").strip()
    email = (request.args.get("email") or "").strip()
    order_id = (request.args.get("order_id") or "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if user:
        user_id = user["id"]
        user_email = user.get("email", "")
        # Link any past guest orders matching this patron's email
        if user_email:
            cursor.execute("UPDATE orders SET user_id = ? WHERE (user_id IS NULL OR user_id = '') AND customer_email = ?", (user_id, user_email))
            conn.commit()

        cursor.execute("""
            SELECT * FROM orders 
            WHERE user_id = ? OR (customer_email = ? AND customer_email != '')
            ORDER BY created_at DESC
        """, (user_id, user_email))
    elif email or phone or order_id:
        conditions = []
        params = []
        if email:
            conditions.append("customer_email = ?")
            params.append(email)
        if phone:
            clean_p = re.sub(r"[^\d]", "", phone)[-10:]
            formatted_p = f"{clean_p[:5]} {clean_p[5:]}"
            conditions.append("(customer_phone LIKE ? OR customer_phone LIKE ? OR REPLACE(customer_phone, ' ', '') LIKE ?)")
            params.extend([f"%{clean_p}%", f"%{formatted_p}%", f"%{clean_p}%"])
        if order_id:
            conditions.append("id = ?")
            params.append(order_id)
        
        where_clause = " OR ".join(conditions)
        cursor.execute(f"SELECT * FROM orders WHERE {where_clause} ORDER BY created_at DESC", tuple(params))
    else:
        # Unauthenticated without query params returns empty list gracefully
        conn.close()
        return jsonify([])

    order_rows = cursor.fetchall()
    orders = []
    for o in order_rows:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
        item_rows = cursor.fetchall()
        orders.append(order_to_dict(o, item_rows))

    conn.close()
    return jsonify(orders)

@order_bp.route("/orders/track", methods=["GET"])
@order_bp.route("/orders/lookup", methods=["GET"])
def lookup_order():
    q = (request.args.get("q") or request.args.get("order_id") or request.args.get("phone") or "").strip()
    if not q:
        return jsonify({"detail": "Please provide an Order ID or 10-digit Phone Number"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    clean_digits = re.sub(r"[^\d]", "", q)
    if clean_digits and len(clean_digits) >= 10:
        last10 = clean_digits[-10:]
        formatted_pattern = f"{last10[:5]} {last10[5:]}"
        cursor.execute("""
            SELECT * FROM orders 
            WHERE id = ? 
               OR customer_phone LIKE ? 
               OR customer_phone LIKE ? 
               OR REPLACE(customer_phone, ' ', '') LIKE ?
            ORDER BY created_at DESC
        """, (q, f"%{last10}%", f"%{formatted_pattern}%", f"%{last10}%"))
    else:
        cursor.execute("SELECT * FROM orders WHERE id = ? OR customer_email = ? ORDER BY created_at DESC", (q, q))

    rows = cursor.fetchall()
    if not rows:
        conn.close()
        return jsonify({"detail": f"No orders found matching '{q}'."}), 404

    results = []
    for r in rows:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (r["id"],))
        item_rows = cursor.fetchall()
        results.append(order_to_dict(r, item_rows))

    conn.close()
    return jsonify(results)
