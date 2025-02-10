from flask import Blueprint, request, jsonify
from app.services.ocr_service import extract_text

ocr_bp = Blueprint("ocr", __name__)

@ocr_bp.route("/extract", methods=["POST"])
def extract_ocr():
    image = request.files["image"]
    text = extract_text(image)
    return jsonify({"text": text})
