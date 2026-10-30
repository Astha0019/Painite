from flask import Blueprint, request, jsonify
from backend.database import get_db_connection
from backend.models import product_to_dict

product_bp = Blueprint("products", __name__)

@product_bp.route("", methods=["GET"])
def get_products():
    search = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "All").strip()
    gender = (request.args.get("gender") or "All").strip()
    size = (request.args.get("size") or "All").strip()
    price_range = (request.args.get("price") or request.args.get("price_range") or "All").strip().lower()
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    sort = (request.args.get("sort") or "featured").strip().lower()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    # 1. Search Query
    if search:
        query += " AND (name LIKE ? OR description LIKE ? OR category LIKE ? OR tag LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    # 2. Gender Filter: Men, Women, Unisex
    if gender and gender.lower() != "all":
        g_lower = gender.lower()
        if g_lower == "men":
            query += " AND (LOWER(gender) = 'men' OR LOWER(gender) = 'unisex')"
        elif g_lower == "women":
            query += " AND (LOWER(gender) = 'women' OR LOWER(gender) = 'unisex')"
        elif g_lower == "unisex":
            query += " AND LOWER(gender) = 'unisex'"
        else:
            query += " AND LOWER(gender) = LOWER(?)"
            params.append(gender)

    # 3. Category Filter: Oversized T-Shirts, Graphic T-Shirts, Jackets, Minimal & Core
    if category and category.lower() != "all":
        cat_lower = category.lower()
        if "oversized" in cat_lower:
            query += " AND LOWER(category) LIKE '%oversized%'"
        elif "graphic" in cat_lower or "anime" in cat_lower:
            query += " AND (LOWER(category) LIKE '%graphic%' OR LOWER(category) LIKE '%anime%')"
        elif "jacket" in cat_lower:
            query += " AND LOWER(category) LIKE '%jacket%'"
        elif "minimal" in cat_lower or "core" in cat_lower:
            query += " AND (LOWER(category) LIKE '%minimal%' OR LOWER(category) LIKE '%core%')"
        else:
            query += " AND (LOWER(category) = LOWER(?) OR LOWER(collection) = LOWER(?))"
            params.extend([category, category])

    # 4. Size Filter: S, M, L, XL, XXL
    if size and size.lower() != "all":
        query += " AND (sizes LIKE ? OR sizes LIKE ?)"
        params.extend([f'%"{size}"%', f'%{size}%'])

    # 5. Price Range Filter: under-999, 1000-1499, 1500-2000
    if price_range and price_range != "all":
        if price_range in ["under-999", "under_999", "<999"]:
            query += " AND price <= 999.0"
        elif price_range in ["1000-1499", "1000_1499"]:
            query += " AND price >= 1000.0 AND price <= 1499.0"
        elif price_range in ["1500-2000", "1500_2000"]:
            query += " AND price >= 1500.0 AND price <= 2000.0"

    # Direct min/max price overrides if supplied
    if min_price:
        try:
            query += " AND price >= ?"
            params.append(float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            query += " AND price <= ?"
            params.append(float(max_price))
        except ValueError:
            pass

    # 6. Sorting
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
