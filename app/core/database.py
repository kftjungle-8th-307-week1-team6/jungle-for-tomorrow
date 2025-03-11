from flask_pymongo import PyMongo
from pymongo import MongoClient


mongo = None
db = None


def init_db(app):
    global mongo, db
    global mongo, db
    mongo = PyMongo(app, uri="mongodb://localhost:27017/jungle_tommorow")
    db = mongo.db

    if db.item_types.count_documents({}) == 0:
        db.item_types.insert_many([
            {"name":"전자기기"},
            {"name":"문구류"},
            {"name":"기타"},
            {"name":"의류"}
        ])
    return db