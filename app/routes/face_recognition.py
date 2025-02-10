from flask import Blueprint, request, jsonify
from app.services.face_service import process_face
from app.database import mongo

face_bp = Blueprint("face_recognition", __name__)

@face_bp.route("/recognize", methods=["POST"])
def recognize_face():
    image = request.files["image"]
    result = process_face(image)

    # Lưu log vào MongoDB
    mongo.db.face_logs.insert_one(result)

    return jsonify({"status": "success", "data": result})
