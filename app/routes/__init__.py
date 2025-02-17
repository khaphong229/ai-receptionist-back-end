from .face_recognition import face_bp
from .chatbot import chatbot_bp
from .ocr import ocr_bp

def register_routes(app):
    app.register_blueprint(face_bp, url_prefix="/api/face")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(ocr_bp, url_prefix="/api/ocr")