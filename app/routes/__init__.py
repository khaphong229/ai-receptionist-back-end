from .face_recognition import face_bp
# from .chatbot import chatbot_bp
from .ocr import ocr_bp
# from .ai_face_gen import ai_face_bp
# from .data_analysis import data_analysis_bp

def register_routes(app):
    app.register_blueprint(face_bp, url_prefix="/api/face")
    # app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")
    app.register_blueprint(ocr_bp, url_prefix="/api/ocr")
    # app.register_blueprint(ai_face_bp, url_prefix="/api/ai_face")
    # app.register_blueprint(data_analysis_bp, url_prefix="/api/data")
