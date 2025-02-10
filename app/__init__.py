from flask import Flask
from flask_cors import CORS
from .config import Config
from .database import init_db
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)  # Cho phép FE truy cập API
    init_db(app)  # Kết nối MongoDB

    register_routes(app)  # Import API routes

    return app
