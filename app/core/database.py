from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv
from pymongo import MongoClient


mongo = None
db = None


def init_db(app):
    global mongo, db
    load_dotenv()  # .env 파일 로드하기
    mongo_uri = os.getenv("MONGO_URI")  # 환경변수에서 URI 읽기

    mongo = PyMongo(app, uri=mongo_uri)
    db = mongo.db

    if db.item_types.count_documents({}) == 0:
        db.item_types.insert_many([
            {"name":"전자기기"},
            {"name":"문구류"},
            {"name":"기타"},
            {"name":"의류"}
        ])
    return db