import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "painite-studio-super-secret-production-key-2026")
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "painite.db"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "static", "uploads"))
    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}
    TOKEN_EXPIRY_HOURS = 72

    # Meta WhatsApp Business Cloud API Configuration
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    WHATSAPP_BUSINESS_NUMBER = os.getenv("WHATSAPP_BUSINESS_NUMBER", "919359615919").strip()
    WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0").strip()
    WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME", "").strip()

