from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                return jsonify({"error": "유효하지 않은 토큰입ㅈ니다.", "details": str(e)}), 401
            claims = get_jwt()
            role = claims.get("role", "")

            if role not in allowed_roles:
                return jsonify({"error":"접근 권한이 없습니다."}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper


def admin_required():
    return role_required(["admin"])


def user_required():
    return role_required(["admin", "user"])
