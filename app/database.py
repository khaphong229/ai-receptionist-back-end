from flask_pymongo import PyMongo
from .config import Config

mongo = PyMongo()
customers = None

def init_db(app):
    global customers
    app.config["MONGO_URI"] = Config.MONGO_URI
    mongo.init_app(app)
    customers = mongo.db.customers