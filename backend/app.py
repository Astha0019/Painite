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

    # API Health Check
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Painite Studio API",
            "version": "2.0.0"
        }), 200

    # Serve static assets from panite_files
    @app.route("/panite_files/<path:filename>")
    def serve_panite_files(filename):
        return send_from_directory(panite_files_dir, filename)

    # Serve uploaded artwork
    @app.route("/static/uploads/<path:filename>")
    def serve_uploads(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    # Fallback to SPA for any non-API client routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
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
