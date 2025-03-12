from flask import Blueprint, jsonify, request, render_template
from app.core.extension import bcrypt
from app.core.database import db
from flask_jwt_extended import (create_access_token, get_jwt_identity,)
from datetime import timedelta
from app.core.auth import user_required
import uuid
from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dbyurucamp1

router = Blueprint("user", __name__, url_prefix="/user")


@router.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"msg": "사용자명과 비밀번호를 모두 입력해주세요"}), 400

    user = db.users.find_one({"username": username})

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"msg": "잘못된 사용자명 또는 비밀번호입니다."}), 401

    user_role = user.get("role", "user")

    if user_role not in ["admin", "user"]:
        user_role = "user"

    additional_claims = {"role": user_role}
    access_token = create_access_token(
        identity=username,
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=1)
    )

    return jsonify({
        "access_token": access_token,
        "role": user_role
    }), 200


@router.route('/signup', methods=['POST'])
def sign_up():
    name = request.form["name"]
    id = request.form["id"]
    pw = request.form["pw"]
    nickname = request.form["nickname"]
    division = request.form["division"]
    generation = request.form["generation"]
    hashed_password = bcrypt.generate_password_hash(pw).decode('utf-8')

    user_data = {
        "user_id": id,
        "user_pw": hashed_password,
        "name": name,
        "nickname": nickname,
        "division": division,
        "generation": int(generation),
        "role": "user"
    }

    result = db.users.insert_one(user_data)

    return render_template('registerResult.html', inserted_id=result.inserted_id)


@router.route('/info', methods=['GET'])
@user_required() # 데코레이터를 이용해 API의 권한을 설정합니다. user_required() 는 유저 및 Admin이 확인 가능하며, admin_required()는 admin만 확인 가능합니다.
def get_user_info():

    current_user = get_jwt_identity()

    user = db.users.find_one({"username": current_user})

    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다."}),404

    user_info = {
        "username" : user["username"],
        "role" : user.get("role", "user"),
    }

    return jsonify(user_info), 200

@router.route('/idCheck', methods=['POST'])
def idCheck():
    id_receive = request.form['id']    
    element = db.users.find_one({'user_id':id_receive})
    return jsonify({'result':element is None})

@router.route('/nicknameCheck', methods=['POST'])
def nicknameCheck():
    nickname_receive = request.form['nickname']    
    element = db.users.find_one({'nickname':nickname_receive})
    return jsonify({'result':element is None})