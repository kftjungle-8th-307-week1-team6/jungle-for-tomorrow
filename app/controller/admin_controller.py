from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from app.core.extension import bcrypt
from app.core.database import db
from bson.objectid import ObjectId
from app.core.auth import admin_required
import uuid

router = Blueprint("admin", __name__, url_prefix="/admin")


@router.route('/admin/signup', methods=['POST'])
# @admin_required()
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

@router.route('/items', methods=['GET'])
# @admin_required()
def item_list():
    # 페이지 번호 가져오기 (기본값 1)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 페이지네이션 계산
    skip_count = (page - 1) * per_page

    # 아이템 가져오기
    items = list(db.items.find().skip(skip_count).limit(per_page))
    total_items = db.items.count_documents({})
    total_pages = (total_items + per_page - 1) // per_page

    item_types = list(db.item_types.find({}))

    return render_template(
        "admin/items.html",
        items=items,
        item_types=item_types,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.route('/items/add', methods=["POST"])
# @admin_required()
def add_item():
    name = request.form.get('name')
    type_id = request.form.get('type')
    quantity = request.form.get('quantity', 1, type=int)

    if not name or not type_id:
        flash('모든 필드를 입력해주세요.', 'error')
        return redirect(url_for('admin.item_list'))

    type_doc = db.item_types.find_one({"_id": ObjectId(type_id)})
    type_name = type_doc['name'] if type_doc else "알 수 없음"

    db.items.insert_one({
        "name": name,
        "type": type_name,
        "quantity": quantity,
        "is_required" : True,
        "is_recommended" : False,
    })
    return redirect(url_for('admin.item_list'))


@router.route('/items/<string:id>/edit', methods=['POST'])
# @admin_required()
def edit_item(id):
    name = request.form.get('name')
    type_id = request.form.get('type')
    quantity = request.form.get('quantity', 1, type=int)

    if not name or not type_id:
        flash('모든 필드를 입력해주세요.', 'error')
        return redirect(url_for('admin.item_list'))

    type_doc = db.item_types.find_one({"_id": ObjectId(type_id)})
    type_name = type_doc['name'] if type_doc else "알 수 없음"

    db.items.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "name": name,
            "type": type_name,
            "quantity": quantity,
            "is_required": True,
            "is_recommended": False,
        }}
    )

    return redirect(url_for('admin.item_list'))

@router.route('/items/<string:id>/delete')
# @admin_required()
def delete_item(id):
    try:
        result = db.items.delete_one({"_id": ObjectId(id)})
        if result.deleted_count > 0:
            flash('항목이 성공적으로 삭제되었습니다.', 'success')
        else:
            flash('항목을 찾을 수 없습니다.', 'error')
    except Exception as e:
        flash(f"항목 삭제 중 오류가 발생했습니다.: {str(e)}", 'error')
    return redirect(url_for('admin.item_list'))
