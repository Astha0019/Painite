import json
import re

def format_inr(amount):
    """
    Format currency according to Indian English (en-IN) numbering system.
    Example: 999 -> ₹999, 1499 -> ₹1,499, 2499 -> ₹2,499, 150000 -> ₹1,50,000
    """
    val = round(float(amount or 0.0), 2)
    if val.is_integer():
        s = str(int(val))
    else:
        s = f"{val:.2f}"
    
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = ("." + parts[1]) if len(parts) > 1 else ""

    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        remaining = re.sub(r"(\d)(?=(\d{2})+(?!\d))", r"\1,", remaining)
        formatted_num = remaining + "," + last_three
    else:
        formatted_num = integer_part

    return f"₹{formatted_num}{decimal_part}"

def user_to_dict(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "created_at": row["created_at"]
    }

def product_to_dict(row):
    if not row:
        return None
    
    colors = row["colors"]
    if isinstance(colors, str):
        try:
            colors = json.loads(colors)
        except Exception:
            colors = ["Onyx Black", "Kora White"]

    sizes = row["sizes"]
    if isinstance(sizes, str):
        try:
            sizes = json.loads(sizes)
        except Exception:
            sizes = ["S", "M", "L", "XL"]

    styles = row["styles"]
    if isinstance(styles, str):
        try:
            styles = json.loads(styles)
        except Exception:
            styles = ["Oversized", "Boxy"]

    price_val = float(row["price"])
    original_price_val = float(row["original_price"]) if ("original_price" in row.keys() and row["original_price"] is not None) else None
    
    # Calculate discount percent if not stored or if 0
    discount_val = 0
    if "discount_pct" in row.keys() and row["discount_pct"]:
        discount_val = int(row["discount_pct"])
    elif original_price_val and original_price_val > price_val:
        discount_val = round(((original_price_val - price_val) / original_price_val) * 100)

    gender_val = row["gender"] if "gender" in row.keys() and row["gender"] else "Unisex"
    collection_val = row["collection"] if "collection" in row.keys() and row["collection"] else "Streetwear"
    color_hex_val = row["color_hex"] if "color_hex" in row.keys() and row["color_hex"] else "#101114"

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"] or "",
        "price": price_val,
        "original_price": original_price_val,
        "currency": "INR",
        "formatted_price": format_inr(price_val),
        "formatted_original_price": format_inr(original_price_val) if original_price_val else None,
        "discount_pct": discount_val,
        "category": row["category"],
        "gender": gender_val,
        "collection": collection_val,
        "tag": row["tag"] or "",
        "image": row["image"],
        "color_hex": color_hex_val,
        "colors": colors,
        "sizes": sizes,
        "styles": styles,
        "in_stock": bool(row["in_stock"]),
        "created_at": row["created_at"]
    }

def order_item_to_dict(row):
    if not row:
        return None
    price_val = float(row["price"])
    return {
        "id": row["id"],
        "order_id": row["order_id"],
        "product_id": row["product_id"],
        "product_name": row["product_name"],
        "price": price_val,
        "currency": "INR",
        "formatted_price": format_inr(price_val),
        "quantity": int(row["quantity"]),
        "color": row["color"],
        "size": row["size"],
        "style": row["style"],
        "custom_text": row["custom_text"],
        "artwork_url": row["artwork_url"],
        "created_at": row["created_at"]
    }

def order_to_dict(order_row, item_rows=None):
    if not order_row:
        return None
    
    items = []
    if item_rows is not None:
        items = [order_item_to_dict(r) for r in item_rows]

    total_val = float(order_row["total"])
    currency = order_row["currency"] if "currency" in order_row.keys() else "INR"
    phone = order_row["customer_phone"] if "customer_phone" in order_row.keys() else ""
    city = order_row["city"] if "city" in order_row.keys() else ""
    state = order_row["state"] if "state" in order_row.keys() else ""
    pincode = order_row["pincode"] if "pincode" in order_row.keys() else ""
    shipping_fee = float(order_row["shipping_fee"]) if "shipping_fee" in order_row.keys() else 0.0

    return {
        "id": order_row["id"],
        "user_id": order_row["user_id"],
        "customer_name": order_row["customer_name"],
        "customer_email": order_row["customer_email"],
        "customer_phone": phone,
        "total": total_val,
        "currency": currency,
        "formatted_total": format_inr(total_val),
        "status": order_row["status"],
        "address": order_row["address"],
        "city": city,
        "state": state,
        "pincode": pincode,
        "shipping_fee": shipping_fee,
        "payment_method": order_row["payment_method"],
        "created_at": order_row["created_at"],
        "items": items
    }
