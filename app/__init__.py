import os
from flask import Flask
from app.core.database import init_db
from app.core.extension import init_extensions, bcrypt, jwt


def create_app(config=None):
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','templates'))
    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = 'test1231245'
    app.config['JWT_SECRET_KEY'] = 'test'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    init_db(app)
    init_extensions(app)

    from app.controller.admin_controller import router as admin_router
    from app.controller.user_controller import router as user_router
    from app.controller.recommended_items_controller import router as recommended_items_router

    app.register_blueprint(admin_router)
    app.register_blueprint(user_router)
    app.register_blueprint(recommended_items_router)

    return app