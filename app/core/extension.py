from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

bcrypt = Bcrypt()
jwt = JWTManager()

def init_extensions(app):
    bcrypt.init_app(app)
    jwt.init_app(app)