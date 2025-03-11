from flask import Blueprint, jsonify, request, render_template
from app.core.extension import bcrypt
from app.core.database import db

router = Blueprint("main", __name__)

@router.route('/')
def home():
    return render_template('index.html')

@router.route('/loginPage')
def login_page():
    return render_template('login.html')

@router.route('/registerPage')
def register_page():
    return render_template('register.html')
