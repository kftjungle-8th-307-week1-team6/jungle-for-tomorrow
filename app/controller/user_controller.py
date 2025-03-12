import uuid
from flask import Blueprint, jsonify, request, flash, redirect, url_for, render_template
from app.core.extension import bcrypt
from app.core.database import db
from flask_jwt_extended import (create_access_token, get_jwt_identity, create_refresh_token, get_jwt)
from datetime import timedelta, datetime
from app.core.auth import user_required
from bson.objectid import ObjectId

router = Blueprint("user", __name__, url_prefix="/user")


@router.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        if not username or not password:
            return jsonify({"msg": "사용자명과 비밀번호를 모두 입력해주세요"}), 400

        user = db.users.find_one({"username": username})

        if not user or not bcrypt.check_password_hash(user["password"], password):
            flash("잘못된 사용자명 또는 비밀번호 입니다.", "error")
            return redirect(url_for('main.login_page'))

        user_role = user.get("role", "user")

        if user_role not in ["admin", "user"]:
            user_role = "user"
        # 사용자 ID를 문자열로 변환하여 토큰에 포함
        user_id = str(user["_id"])

        additional_claims = {
            "role": user_role,
            "user_id": user_id  # 사용자 ID 추가
        }
        access_token = create_access_token(
            identity=username,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=1)
        )

        response = redirect(url_for('main.home'))

        response.set_cookie(
            'access_token_cookie',
            access_token,
            httponly=True,
            max_age=3600,
            secure=False,
            samesite='Lax'
        )
        return response

    except Exception as e:
        print(f"로그인 오류: {str(e)}")
        return redirect(url_for('main.login_page'))


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
        "username": id,
        "password": hashed_password,
        "name": name,
        "nickname": nickname,
        "division": division,
        "generation": int(generation),
        "role": "user"
    }

    result = db.users.insert_one(user_data)

    return render_template('registerResult.html', inserted_id=result.inserted_id)


@router.route('/logout', methods=['GET'])
def logout():
    response = redirect(url_for('main.login_page'))
    response.delete_cookie('access_token_cookie')
    flash("로그아웃 되었습니다.", "success")
    return response

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


@router.route('/management', methods=['GET'])
@user_required()
def profile():
    try:
        # JWT 토큰에서 사용자 ID 가져오기
        current_user = get_jwt_identity()
        user_details = db.users.find_one({"username": current_user})

        if not user_details:
            return jsonify({"error": "사용자 정보를 찾을 수 없습니다."}), 404

        # 사용자 정보 템플릿에 전달
        return render_template(
            'user/user_info.j2',
            user_details=user_details,
            error=request.args.get('error')
        )
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@router.route('/update_profile', methods=['POST'])
@user_required()
def update_profile(user_id=None):
    try:
        # 폼 데이터 가져오기
        name = request.form.get('name', '')
        nickname = request.form.get('nickname', '')
        generation = request.form.get('generation', '')
        division = request.form.get('division', '')

        # 입력 유효성 검사
        if not name or not nickname:
            return redirect(url_for('user.profile', error='이름과 닉네임은 필수 입력 항목입니다.'))

        # 사용자 정보 업데이트
        update_data = {
            "name": name,
            "nickname": nickname,
            "division": division
        }

        # 기수가 입력된 경우에만 업데이트
        if generation:
            try:
                update_data["generation"] = int(generation)
            except ValueError:
                return redirect(url_for('user.profile', error='기수는 숫자로 입력해주세요.'))

        # 데이터베이스 업데이트
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        # 성공 메시지와 함께 홈페이지로 리다이렉트
        flash('프로필이 성공적으로 업데이트되었습니다.', 'success')
        return redirect(url_for('main.home'))

    except Exception as e:
        # 오류 발생 시 프로필 페이지로 리다이렉트
        return redirect(url_for('user.profile', error=f'프로필 업데이트 중 오류가 발생했습니다: {str(e)}'))
