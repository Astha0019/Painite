from flask import Blueprint, request, jsonify
from backend.database import get_db_connection
from backend.models import product_to_dict

product_bp = Blueprint("products", __name__)

@product_bp.route("", methods=["GET"])
def get_products():
    search = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "All").strip()
    gender = (request.args.get("gender") or "").strip()
    collection = (request.args.get("collection") or "").strip()
    color = (request.args.get("color") or "").strip()
    sort = (request.args.get("sort") or "featured").strip().lower()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR description LIKE ? OR category LIKE ? OR collection LIKE ? OR gender LIKE ? OR tag LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard, wildcard, wildcard])

    # Gender filter
    if gender and gender.lower() != "all":
        if gender.lower() == "men":
            query += " AND (LOWER(gender) = 'men' OR LOWER(gender) = 'unisex')"
        elif gender.lower() == "women":
            query += " AND (LOWER(gender) = 'women' OR LOWER(gender) = 'unisex')"
        else:
            query += " AND LOWER(gender) = LOWER(?)"
            params.append(gender)

    # Category / Collection filter
    if category and category.lower() != "all":
        cat_lower = category.lower()
        if cat_lower in ["men", "women"]:
            query += f" AND (LOWER(gender) = '{cat_lower}' OR LOWER(gender) = 'unisex')"
        elif cat_lower in ["core", "studio", "edition 01", "customizable"]:
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category)
        else:
            query += " AND (LOWER(category) = LOWER(?) OR LOWER(collection) = LOWER(?))"
            params.extend([category, category])

    if collection and collection.lower() != "all":
        query += " AND LOWER(collection) = LOWER(?)"
        params.append(collection)

    if color and color.lower() != "all":
        query += " AND (colors LIKE ? OR name LIKE ?)"
        params.extend([f"%{color}%", f"%{color}%"])

    # Sorting
    if sort == "price-asc":
        query += " ORDER BY price ASC"
    elif sort == "price-desc":
        query += " ORDER BY price DESC"
    elif sort == "discount":
        query += " ORDER BY discount_pct DESC, price ASC"
    elif sort == "name":
        query += " ORDER BY name ASC"
    else:  # featured / default
        query += " ORDER BY CASE WHEN tag LIKE '%BESTSELLER%' THEN 1 WHEN tag LIKE '%NEW%' THEN 2 ELSE 3 END, id ASC"

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
