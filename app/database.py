from flask_pymongo import PyMongo
from .config import Config

mongo = PyMongo()

def init_db(app):
    app.config["MONGO_URI"] = Config.MONGO_URI
    mongo.init_app(app)
