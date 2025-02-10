from flask import Blueprint, request, jsonify
from app.services.chatbot_service import generate_response
from app.database import mongo

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/ask", methods=["POST"])
def ask_chatbot():
    data = request.json
    question = data.get("question", "")

    response = generate_response(question)

    # Lưu vào MongoDB
    mongo.db.chat_history.insert_one({
        "question": question,
        "response": response
    })

    return jsonify({"response": response})
