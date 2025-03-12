from functools import wraps

from flask import jsonify, redirect, url_for
from flask_jwt_extended import get_jwt, verify_jwt_in_request, get_jwt_identity


def role_required(allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request(locations=['cookies'])
                claims = get_jwt()
                role = claims.get("role", "")
                user_id = claims.get("user_id")
                if role not in allowed_roles:
                    return jsonify({"error":"접근 권한이 없습니다."}), 403
                import inspect
                sig = inspect.signature(fn)
                if 'user_id' in sig.parameters:
                    kwargs['user_id'] = user_id

                return fn(*args, **kwargs)
            except Exception as e:
                print(f"this {e}")
                return redirect(url_for('main.login_page'))
        return decorator
    return wrapper


def admin_required():
    return role_required(["admin"])


def user_required():
    return role_required(["admin", "user"])
