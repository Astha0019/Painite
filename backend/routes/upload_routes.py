import os
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from backend.config import Config

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"detail": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"detail": "No file selected for uploading"}), 400

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else ""

    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({"detail": f"File type not allowed. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"}), 400

    # Ensure upload folder exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    unique_filename = f"art_{uuid.uuid4().hex[:12]}.{ext}"
    destination_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)

    if ext in ["png", "jpg", "jpeg", "webp"]:
        try:
            # Verify and optimize image with Pillow
            img = Image.open(file.stream)
            img.verify()
            file.stream.seek(0)
            
            # Reopen for saving
            img = Image.open(file.stream)
            # Max dimension clamp for studio performance
            max_size = (2000, 2000)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(destination_path)
        except Exception as e:
            return jsonify({"detail": f"Invalid or corrupt image file: {str(e)}"}), 400
    else:
        # SVG or raw allowed format
        file.save(destination_path)

    relative_url = f"/static/uploads/{unique_filename}"
    return jsonify({
        "url": relative_url,
        "filename": unique_filename,
        "message": "Artwork uploaded successfully"
    }), 201
