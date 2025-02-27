from flask import Flask
from flask_cors import CORS
from .config import Config
from .database import init_db, mongo
from .routes import register_routes

def create_app():
    app = Flask(__name__,
        static_folder='../static',  # Đường dẫn tương đối đến thư mục static
        static_url_path='/static'   # URL prefix cho static files
    )
    app.config.from_object(Config)

    # Cấu hình CORS cho tất cả origins
    CORS(app, 
        resources={r"/api/*": {  # Áp dụng cho tất cả routes bắt đầu bằng /api/
            "origins": "*",  # Cho phép tất cả origins
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
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

    # Register all routes
    register_routes(app)

    return app