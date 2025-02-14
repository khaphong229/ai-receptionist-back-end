from flask import Flask
from flask_cors import CORS
from .config import Config
from .database import init_db, mongo
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    init_db(app)  # Initialize MongoDB connection
    register_routes(app)

    return app