from flask import Blueprint, jsonify, request
from app.core.extension import bcrypt
from app.core.database import db
from flask_jwt_extended import (create_access_token, get_jwt_identity,)
from datetime import timedelta
from app.core.auth import user_required

import uuid

router = Blueprint("my_list", __name__, url_prefix="/my-list")

