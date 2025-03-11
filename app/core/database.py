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
    return db