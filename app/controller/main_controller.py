from flask import Blueprint, jsonify, request, render_template
from app.core.extension import bcrypt
from flask_jwt_extended import get_jwt, verify_jwt_in_request, get_jwt_identity
from app.core.database import db

router = Blueprint("main", __name__)

@router.route('/')
def home():
    username = None
    user_role = None
    user_info = None
    try:
        if request.cookies.get('access_token_cookie'):
            # verify_jwt_in_request는 토큰 유효성을 검사하고 예외를 발생시킬 수 있음
            verify_jwt_in_request(locations=['cookies'])
            # 유효한 토큰이면 사용자 ID 가져오기
            username = get_jwt_identity()
            user_info = db.users.find_one({"username":username})

            claims = get_jwt()
            user_role = claims.get('role', 'user')
    except:
        pass
    return render_template(
        'index.html',
        username=username,
        user_role=user_role,
        division = user_info["division"] if user_info else None,
        generation = user_info["generation"] if user_info else None,
        name = user_info["name"] if user_info else None
        )

@router.route('/loginPage')
def login_page():
    return render_template('login.html')

@router.route('/registerPage')
def register_page():
    return render_template('register.html')
