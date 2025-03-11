from flask import Blueprint, jsonify, request
from app.core.extension import bcrypt
from app.core.database import db
from flask_jwt_extended import (create_access_token, get_jwt_identity,)
from datetime import timedelta
from app.core.auth import user_required

import uuid

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
    data = request.get_json()
    username = data.get('username')
    password = data.get("password")

    if not username or not password:
        return jsonify({"error":"사용자명과 비밀번호는 필수입니다."}), 400

    if db.users.find_one({"username": username}):
        return jsonify({"error":"이미 존재하는 사용자명입니다."}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    user_data = {
        "public_id": str(uuid.uuid4()),
        "username" : username,
        "password" : hashed_password,
        "role": "user"
    }

    db.users.insert_one(user_data)

    return jsonify({"message" : "회원가입이 완료되었습니다."}), 201


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