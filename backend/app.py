import os
from flask import Flask, jsonify, request, send_from_directory, render_template_string
from backend.config import Config
from backend.database import init_db
from backend.seeds import seed_database
from backend.routes.auth_routes import auth_bp
from backend.routes.product_routes import product_bp
from backend.routes.order_routes import order_bp
from backend.routes.admin_routes import admin_bp
from backend.routes.upload_routes import upload_bp

def create_app():
    # Base directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    static_dir = os.path.join(base_dir, "static")
    panite_files_dir = os.path.join(base_dir, "panite_files")

    app = Flask(__name__, static_folder=static_dir)
    app.config.from_object(Config)

    # Initialize database and run seeds
    init_db()
    seed_database()

    # Enable CORS for all API routes
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    @app.route("/api/<path:dummy>", methods=["OPTIONS"])
    def api_options(dummy):
        return "", 204

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(order_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(upload_bp, url_prefix="/api/upload")

    # API Health Check & Vercel Root Endpoints
    @app.route("/api/health", methods=["GET"])
    @app.route("/api/index", methods=["GET"])
    @app.route("/api/index.py", methods=["GET"])
    @app.route("/api", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Painite Studio API",
            "version": "2.0.0",
            "message": "Painite Studio API is live and operational."
        }), 200

    # Serve static assets from panite_files
    @app.route("/panite_files/<path:filename>")
    def serve_panite_files(filename):
        return send_from_directory(panite_files_dir, filename)

    # Serve uploaded artwork
    @app.route("/static/uploads/<path:filename>")
    def serve_uploads(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    # Public Active Banners
    @app.route("/api/banners", methods=["GET"])
    def public_banners():
        from backend.database import get_db_connection
        from backend.models import banner_to_dict
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM banners WHERE is_active = 1 ORDER BY sort_order ASC, created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([banner_to_dict(r) for r in rows])

    # Public Active Categories
    @app.route("/api/categories", methods=["GET"])
    def public_categories():
        from backend.database import get_db_connection
        from backend.models import category_to_dict
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY display_order ASC, name ASC")
        rows = cursor.fetchall()
        results = []
        for r in rows:
            cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE category = ?", (r["name"],))
            cnt = cursor.fetchone()["cnt"]
            results.append(category_to_dict(r, cnt))
        conn.close()
        return jsonify(results)

    # Public Coupon Validation / Apply
    @app.route("/api/coupons/apply", methods=["POST"])
    def apply_coupon():
        from backend.database import get_db_connection
        from backend.models import coupon_to_dict, format_inr
        data = request.get_json(silent=True) or {}
        code = (data.get("code") or "").strip().upper()
        subtotal = float(data.get("subtotal") or 0.0)

        if not code:
            return jsonify({"detail": "Coupon code is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code,))
        coupon = cursor.fetchone()
        conn.close()

        if not coupon:
            return jsonify({"detail": "Invalid or expired promotional code."}), 404

        min_amt = float(coupon["min_order_amount"])
        if subtotal < min_amt:
            return jsonify({
                "detail": f"Coupon '{code}' requires a minimum cart value of {format_inr(min_amt)}."
            }), 400

        disc_type = coupon["discount_type"]
        disc_val = float(coupon["discount_value"])
        if disc_type == "percentage":
            discount_amount = round((subtotal * disc_val) / 100.0, 2)
            if coupon["max_discount_amount"]:
                max_d = float(coupon["max_discount_amount"])
                if discount_amount > max_d:
                    discount_amount = max_d
        else:
            discount_amount = round(disc_val, 2)
            if discount_amount > subtotal:
                discount_amount = subtotal

        return jsonify({
            "code": code,
            "discount_type": disc_type,
            "discount_value": disc_val,
            "discount_amount": discount_amount,
            "formatted_discount": format_inr(discount_amount),
            "new_total": round(max(0.0, subtotal - discount_amount), 2),
            "message": f"Privilege code '{code}' successfully applied! You saved {format_inr(discount_amount)}."
        })

    # Dedicated Admin Web App Route: Serve admin.html exclusively for /admin and /admin/*
    @app.route("/admin", defaults={"subpath": ""})
    @app.route("/admin/<path:subpath>")
    def serve_admin_app(subpath):
        admin_file = os.path.join(base_dir, "admin.html")
        if os.path.exists(admin_file):
            return send_from_directory(base_dir, "admin.html")
        return jsonify({"detail": "Admin panel template not found"}), 404

    # Fallback to SPA for any non-API client routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        if path == "admin" or path.startswith("admin/"):
            return serve_admin_app(path)
        if path.startswith("api/"):
            return jsonify({"detail": "Endpoint not found"}), 404
        if os.path.exists(os.path.join(base_dir, path)) and not os.path.isdir(os.path.join(base_dir, path)):
            return send_from_directory(base_dir, path)
        # Serve main index / panite.html
        if os.path.exists(os.path.join(base_dir, "index.html")):
            return send_from_directory(base_dir, "index.html")
        return send_from_directory(base_dir, "panite.html")

    return app

if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Painite Studio Full-Stack Server on http://127.0.0.1:{port}")
    application.run(host="0.0.0.0", port=port, debug=True)
