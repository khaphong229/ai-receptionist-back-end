from flask import Flask
from flask_cors import CORS
from .config import Config
from .database import init_db, mongo
from .routes import register_routes
from .routes.face_recognition import face_bp
from .routes.chatbot import chatbot_bp
from .routes.ocr import ocr_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Cấu hình CORS cho tất cả origins
    CORS(app, 
        resources={r"/api/*": {  # Áp dụng cho tất cả routes bắt đầu bằng /api/
            "origins": "*",  # Cho phép tất cả origins
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True,
            "max_age": 600
        }}
    )

    # Thêm CORS headers cho tất cả responses
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # Initialize MongoDB
    init_db(app)
    mongo.init_app(app)

    # Register blueprints
    app.register_blueprint(face_bp, url_prefix='/api/face', name='face_api')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(ocr_bp, url_prefix='/api/ocr')

    return app