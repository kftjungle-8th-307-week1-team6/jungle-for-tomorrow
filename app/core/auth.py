from functools import wraps

from flask import jsonify, redirect, url_for
from flask_jwt_extended import get_jwt, verify_jwt_in_request, get_jwt_identity


def role_required(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request(locations=['cookies'])
                current_user_id = get_jwt_identity()
            except Exception as e:
                return redirect(url_for('user.login'))
            claims = get_jwt()
            role = claims.get("role", "")

            if role not in allowed_roles:
                return jsonify({"error":"접근 권한이 없습니다."}), 403
            kwargs['user_id'] = current_user_id
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def admin_required():
    return role_required(["admin"])


def user_required():
    return role_required(["admin", "user"])
