import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "painite-studio-super-secret-production-key-2026")
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "painite.db"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "static", "uploads"))
    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}
    TOKEN_EXPIRY_HOURS = 72
