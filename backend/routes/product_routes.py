from flask import Blueprint, request, jsonify
from backend.database import get_db_connection
from backend.models import product_to_dict

product_bp = Blueprint("products", __name__)

@product_bp.route("", methods=["GET"])
def get_products():
    search = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "All").strip()
    sort = (request.args.get("sort") or "featured").strip().lower()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    if category and category.lower() != "all":
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)

    # Sorting
    if sort == "price-asc":
        query += " ORDER BY price ASC"
    elif sort == "price-desc":
        query += " ORDER BY price DESC"
    elif sort == "name":
        query += " ORDER BY name ASC"
    else:  # featured / default
        query += " ORDER BY created_at DESC"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    products = [product_to_dict(r) for r in rows]
    return jsonify(products)

@product_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"detail": "Product not found"}), 404

    return jsonify(product_to_dict(row))
