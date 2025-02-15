from .face_recognition import face_bp
from .chatbot import chatbot_bp

def register_routes(app):
    app.register_blueprint(face_bp, url_prefix="/api/face")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")