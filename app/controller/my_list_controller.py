from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from app.core.extension import bcrypt
from app.core.database import db
from flask_jwt_extended import (create_access_token, get_jwt_identity,get_jwt)
from datetime import timedelta
from app.core.auth import user_required
from bson.objectid import ObjectId

import uuid

router = Blueprint("my_list", __name__, url_prefix="/my-list")

@router.route('/check-list', methods=['GET'])
@user_required()
def items(user_id=None):
    # 현재 페이지와 페이지당 항목 수 가져오기
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 필터링 조건 가져오기
    filter_type = request.args.get('filter', 'all')
    item_type = request.args.get('type', 'all')
    user_oid = ObjectId(user_id)

    user = db.users.find_one({"_id": user_oid})
    user_name = user.get('name')
    user_division = user.get('division')
    user_generation = user.get('generation')
    checked_items = user.get('checked_items', [])
    saved_item_ids = user.get('saved_items', [])

    query = {
        "$or": [
            {"_id": {"$in": saved_item_ids}},  # 사용자가 저장한 아이템
            {"is_required": True}  # 필수 아이템은 항상 표시
        ],
        "is_deleted": {"$ne": True}
    }

    # 필터링 적용
    if filter_type == 'required':
        query["is_required"] = True
    elif filter_type == 'recommended':
        query = {
            "$and": [
                {"_id": {"$in": saved_item_ids}},
                {"is_recommended": True},
                {"is_deleted": {"$ne": True}}  # 삭제된 아이템 제외
            ]
        }
    elif filter_type == 'normal':
        query = {
            "$and": [
                {"_id": {"$in": saved_item_ids}},
                {"is_required": False},
                {"is_recommended": False},
                {"is_deleted": {"$ne": True}}  # 삭제된 아이템 제외
            ]
        }
    # 아이템 타입 가져오기
    item_types = list(db.item_types.find())

    # 종류별 필터링 - 동적으로 적용
    if item_type != 'all':
        # 선택된 타입 ID에 해당하는 타입 이름 찾기
        for type_doc in item_types:
            if str(type_doc['_id']) == item_type or type_doc['name'] == item_type:
                query["category"] = type_doc['name']
                break

    # MongoDB에서 데이터 가져오기 (페이지네이션 적용)
    total_items = db.items.count_documents(query)
    items = list(db.items.find(query).sort([
        ("is_required", -1),  # 필수 아이템 우선 (내림차순)
        ("is_recommended", -1),  # 추천 아이템 다음 (내림차순)
        ("shipped_count", -1)  # 배송 횟수 높은 순 (내림차순)
    ]).skip((page - 1) * per_page).limit(per_page))

    # 전체 페이지 수 계산
    total_pages = (total_items + per_page - 1) // per_page

    return render_template(
        'my_item/my_item.html',
        user_name=user_name,
        user_division=user_division,
        user_generation=user_generation,
        items=items,
        item_types=item_types,
        filter=filter_type,
        item_type=item_type,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        checked_items=checked_items
    )


@router.route('/items/add', methods=["POST"])
@user_required()
def add_item(user_id=None):
    name = request.form.get('item_name')
    type_id = request.form.get('category')
    quantity = int(request.form.get('quantity', 1))
    # 종류 이름 가져오기
    type_doc = db.item_types.find_one({"_id": ObjectId(type_id)})
    type_name = type_doc['name'] if type_doc else "알 수 없음"

    result = db.items.insert_one({
        "item_name": name,
        "category": type_name,
        "quantity": quantity,
        "is_required": False,
        "is_recommended": False,
        "user_id": user_id
    })

    item_id = result.inserted_id

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"saved_items": item_id}}
    )

    return redirect(url_for('my_list.items'))


# 준비물 수정 API
@router.route('/items/<string:id>/edit', methods=['POST'])
@user_required()
def edit_item(id, user_id=None):
    name = request.form.get('item_name')
    type_id = request.form.get('category')
    quantity = int(request.form.get('quantity', 1))
    item = db.items.find_one({"_id": ObjectId(id)})

    if item and (item.get('is_required') or item.get('is_recommended')):
        flash('필수 또는 추천 항목은 수정할 수 없습니다.', 'error')
        return redirect(url_for('my_list.items'))
    # 종류 이름 가져오기
    type_doc = db.item_types.find_one({"_id": ObjectId(type_id)})
    type_name = type_doc['name'] if type_doc else "알 수 없음"

    db.items.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "item_name": name,
            "category": type_name,
            "quantity": quantity,
            "is_required": False,
            "is_recommended": False,
        }}
    )

    return redirect(url_for('my_list.items'))


# 준비물 삭제 API
@router.route('/items/<string:id>/delete', methods=['GET'])
@user_required()
def delete_item(id, user_id=None):
    try:
        item_oid = ObjectId(id)
        user_oid = ObjectId(user_id)

        item = db.items.find_one({"_id": item_oid})

        if item and item.get('is_required'):
            flash('필수 항목은 삭제할 수 없습니다.', 'error')
            return redirect(url_for('my_list.items'))
        db.users.update_one(
            {"_id":user_oid},
            {"$pull": {"saved_items": item_oid}}
        )
        # 추천 항목인 경우 shipped_count 감소
        if item and item.get('is_recommended'):
            # shipped_count가 있고 1보다 크면 1 감소
            if 'shipped_count' in item and item['shipped_count'] > 0:
                db.items.update_one(
                    {"_id": item_oid},
                    {"$inc": {"shipped_count": -1}}
                )
        # 추천 항목이 아닌 경우에만 DB에서 완전히 삭제
        elif item:
            db.items.delete_one({"_id": item_oid})

        return redirect(url_for('my_list.items'))
    except Exception as e:
        flash(f'삭제 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('my_list.items'))


@router.route("/items/<string:id>/check", methods=['POST'])
@user_required()
def check_item(id, user_id=None):
    try:
        data = request.json
        is_checked = data.get('checked', False)

        user_oid = ObjectId(user_id)

        if is_checked:
            db.users.update_one(
                {"_id": user_oid},
                {"$addToSet": {"checked_items": ObjectId(id)}}
            )
        else:
            db.users.update_one(
                {"_id": user_oid},
                {"$pull": {"checked_items": ObjectId(id)}}
            )

        return jsonify({"success": True}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500