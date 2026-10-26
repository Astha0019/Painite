import uuid
import re
from flask import Blueprint, request, jsonify, g
from backend.database import get_db_connection
from backend.models import user_to_dict
from backend.auth import hash_password, verify_password, create_token, require_auth

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "customer")
    if role not in ["customer", "admin"]:
        role = "customer"

    if not name:
        return jsonify({"detail": "Name is required"}), 400
    if not email or not EMAIL_REGEX.match(email):
        return jsonify({"detail": "A valid email address is required"}), 400
    if len(password) < 6:
        return jsonify({"detail": "Password must be at least 6 characters"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"detail": "An account with this email already exists"}), 409

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    pwd_hash = hash_password(password)

    cursor.execute(
        "INSERT INTO users (id, name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, email, pwd_hash, role)
    )
    conn.commit()

    cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE id = ?", (user_id,))
    user = user_to_dict(cursor.fetchone())
    conn.close()

    token = create_token(user["id"], user["email"], user["role"])
    return jsonify({
        "token": token,
        "user": user,
        "message": "Account created successfully"
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"detail": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, password_hash, role, created_at FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if not row or not verify_password(password, row["password_hash"]):
        return jsonify({"detail": "Invalid email or password"}), 401

    user = user_to_dict(row)
    token = create_token(user["id"], user["email"], user["role"])
    return jsonify({
        "token": token,
        "user": user,
        "message": "Signed in successfully"
    }), 200

@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    return jsonify(g.current_user)

@auth_bp.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Successfully signed out"}), 200
