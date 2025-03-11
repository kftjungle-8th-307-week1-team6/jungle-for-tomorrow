from flask_pymongo import PyMongo
from pymongo import MongoClient


mongo = None
db = None


def init_db(app):
    global mongo, db
    global mongo, db
    mongo = PyMongo(app, uri="mongodb://localhost:27017/jungle_tommorow")
    db = mongo.db
    return db

