from flask import Blueprint, jsonify, request, render_template
from app.core.extension import bcrypt
from app.core.database import db
import uuid

router = Blueprint("admin", __name__, url_prefix="/admin")


@router.route('/admin/signup', methods=['POST'])
def admin_sign_up():
    data = request.get_json()
    username = data.get('username')
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "사용자명과 비밀번호는 필수입니다."}), 400

    if db.users.find_one({"username": username}):
        return jsonify({"error": "이미 존재하는 사용자명입니다."}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    user_data = {
        "public_id": str(uuid.uuid4()),
        "username": username,
        "password": hashed_password,
        "role": "admin"
    }

    db.users.insert_one(user_data)

    return jsonify({"message": "회원가입이 완료되었습니다."}), 201

@router.route('/setting', methods=['GET'])
def admin_require_item_setting_page():
    return render_template("admin/layout.html")