from flask_pymongo import PyMongo
from pymongo import MongoClient


mongo = None
db = None


def init_db(app):
    global mongo, db
    global mongo, db
    
    # mongo = MongoClient('localhost', 27017, username="admin", password="adminpassword")
    mongo = PyMongo(app)
    db = mongo.db
    return db

