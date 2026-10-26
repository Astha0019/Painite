import json

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
            colors = ["Black", "White"]

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
            styles = ["Classic", "Oversized"]

    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"] or "",
        "price": float(row["price"]),
        "category": row["category"],
        "tag": row["tag"] or "",
        "image": row["image"],
        "colors": colors,
        "sizes": sizes,
        "styles": styles,
        "in_stock": bool(row["in_stock"]),
        "created_at": row["created_at"]
    }

def order_item_to_dict(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "order_id": row["order_id"],
        "product_id": row["product_id"],
        "product_name": row["product_name"],
        "price": float(row["price"]),
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

    return {
        "id": order_row["id"],
        "user_id": order_row["user_id"],
        "customer_name": order_row["customer_name"],
        "customer_email": order_row["customer_email"],
        "total": float(order_row["total"]),
        "status": order_row["status"],
        "address": order_row["address"],
        "payment_method": order_row["payment_method"],
        "created_at": order_row["created_at"],
        "items": items
    }
