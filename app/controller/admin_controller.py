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
@admin_required()
def item_list():

    # 페이지 번호 가져오기 (기본값 1)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 페이지네이션 계산
    skip_count = (page - 1) * per_page

    # 아이템 가져오기
    items = list(db.items.find({'is_required': True}).skip(skip_count).limit(per_page))
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
@admin_required()
def add_item():
    name = request.form.get('item_name')
    type_id = request.form.get('category')
    quantity = request.form.get('quantity', 1, type=int)

    if not name or not type_id:
        flash('모든 필드를 입력해주세요.', 'error')
        return redirect(url_for('admin.item_list'))

    type_doc = db.item_types.find_one({"_id": ObjectId(type_id)})
    type_name = type_doc['name'] if type_doc else "알 수 없음"

    db.items.insert_one({
        "item_name": name,
        "category": type_name,
        "quantity": quantity,
        "is_required" : True,
        "is_recommended" : False,
    })
    return redirect(url_for('admin.item_list'))


@router.route('/items/<string:id>/edit', methods=['POST'])
@admin_required()
def edit_item(id):
    name = request.form.get('item_name')
    type_id = request.form.get('category')
    quantity = request.form.get('quantity', 1, type=int)

    if not name or not type_id:
        flash('모든 필드를 입력해주세요.', 'error')
        return redirect(url_for('admin.item_list'))

    type_doc = db.item_types.find_one({"_id": ObjectId(type_id)})
    type_name = type_doc['name'] if type_doc else "알 수 없음"

    db.items.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "item_name": name,
            "category": type_name,
            "quantity": quantity,
            "is_required": True,
            "is_recommended": False,
        }}
    )

    return redirect(url_for('admin.item_list'))

@router.route('/items/<string:id>/delete')
@admin_required()
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


@router.route('/item-types/add', methods=['POST'])
@admin_required()
def add_item_type():
    """새 항목 종류 추가"""
    name = request.form.get('name')
    if name:
        db.item_types.insert_one({"name": name})
        flash("항목 종류가 추가되었습니다.", "success")
    return redirect(url_for('admin.item_list'))


@router.route('/item-types/<id>/edit', methods=['POST'])
@admin_required()
def edit_item_type(id):
    """항목 종류 수정 및 관련 아이템 업데이트"""
    name = request.form.get('name')
    if name:
        # 기존 항목 이름 가져오기
        old_type = db.item_types.find_one({"_id": ObjectId(id)})

        # 항목 이름 업데이트
        db.item_types.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"name": name}}
        )

        # 해당 항목을 사용하는 모든 아이템 업데이트
        if old_type:
            db.items.update_many(
                {"type": old_type["name"]},
                {"$set": {"category": name}}
            )

        flash("항목 종류가 수정되었습니다.", "success")
    return redirect(url_for('admin.item_list'))


@router.route('/item-types/<id>/delete', methods=['GET'])
@admin_required()
def delete_item_type(id):
    """항목 종류 삭제 및 관련 아이템 '기타'로 변경"""
    # 삭제하려는 항목 정보 가져오기
    item_type = db.item_types.find_one({"_id": ObjectId(id)})

    # '기타' 항목인 경우 삭제 방지
    if item_type and item_type["name"] == "기타":
        flash("'기타' 항목은 삭제할 수 없습니다.", "error")
        return redirect(url_for('admin.item_list'))

    # 기타 항목 ID 찾기
    other_type = db.item_types.find_one({"name": "기타"})

    if not other_type:
        # 기타 항목이 없으면 생성
        other_type_id = db.item_types.insert_one({"name": "기타"}).inserted_id
    else:
        other_type_id = other_type["_id"]

    if item_type:
        # 해당 항목을 사용하는 모든 아이템을 '기타'로 변경
        db.items.update_many(
            {"type": item_type["name"]},
            {"$set": {"category": "기타"}}
        )

        # 항목 삭제
        db.item_types.delete_one({"_id": ObjectId(id)})
        flash("항목 종류가 삭제되었고, 관련 아이템은 '기타' 항목으로 변경되었습니다.", "success")

    return redirect(url_for('admin.item_list'))


@router.route('/items/<id>/data', methods=['GET'])
@admin_required()
def get_item_data(id):
    """아이템 데이터 JSON으로 반환"""
    item = db.items.find_one({"_id": ObjectId(id)})
    if item:
        # ObjectId는 JSON 직렬화가 불가능하므로 문자열로 변환
        item['_id'] = str(item['_id'])
        if 'type_id' in item and item['type_id']:
            item['type_id'] = str(item['type_id'])
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404


@router.route('/items/batch-delete', methods=['POST'])
@admin_required()  # 관리자만 접근 가능
def batch_delete_items():
    item_ids = request.json.get('item_ids', [])

    if not item_ids:
        return jsonify({"result": "failure", "reason": "No items selected"}), 400

    try:
        # ObjectId로 변환
        object_ids = [ObjectId(id) for id in item_ids]

        # 아이템 논리적 삭제 (is_deleted = True로 설정)
        result = db.items.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": {"is_deleted": True}}
        )

        return jsonify({
            "result": "success",
            "deleted_count": result.deleted_count
        })
    except Exception as e:
        return jsonify({"result": "failure", "reason": str(e)}), 500