from flask import Blueprint, jsonify, request, render_template, flash
from app.core.extension import bcrypt
from app.core.database import db
from bson import ObjectId
from bson.errors import InvalidId
from flask_jwt_extended import (verify_jwt_in_request, get_jwt_identity,)
import uuid

from app.core.auth import user_required

router = Blueprint("recommended_items", __name__, url_prefix="/recommended-items")


@router.route('/item', methods=['GET'])
def get_item():
    parameter_dict = request.args.to_dict()  
    object_id = parameter_dict.get('id')
    
    # _id 값을 ObjectId로 변환 (유효성 검사 포함)
    try:
        object_id = ObjectId(object_id)
    except (InvalidId, TypeError):
        return jsonify({"result": "failure", "reason": "Invalid ObjectId format"}), 400

    item = db.items.find_one({'_id': object_id})
    
    if not item:
        return jsonify({"result": "failure", "reason": "Item not found"}), 404

    item['_id'] = str(item['_id'])  # JSON 변환을 위해 문자열로 변환
    return jsonify(item)


@router.route('/item', methods=['POST'])
def create_item():
    item = request.json
    item['_id'] = ObjectId()  # ObjectId 생성 (UUID 대신)
    item['shipped_count'] = 0

    # author_generation을 int로 변환 (문자열일 경우)
    try:
        item['author_generation'] = int(item.get('author_generation', 5))
    except ValueError:
        return jsonify({'message': 'Invalid author_generation value, must be an integer'}), 400
    
    item['essential'] = False
    db.items.insert_one(item)
    return jsonify({'message': 'success', 'id': str(item['_id'])})  # ID 반환


@router.route('/item/<object_id>', methods=['DELETE'])
def delete_item(object_id):
    try:
        item_obj_id = ObjectId(object_id)
    except InvalidId:
        return jsonify({"result": "failure", "reason": "Invalid ObjectId format"}), 400 

    deleted_result = db.items.delete_one({"_id": item_obj_id})
    if deleted_result.deleted_count > 0:
        return jsonify({"result": "success"})
    else:
        return jsonify({"result": "failure", "reason": "삭제 오류! Flask 콘솔 참조."}), 500


# 아이템을 수정합니다. # action="{{ url_for('recommended_items.edit_item') }}" method=""
@router.route('/item/<object_id>', methods=['PUT'])
def edit_item(object_id):
    try:
        item_obj_id = ObjectId(object_id)
    except InvalidId:
        return jsonify({"result": "failure", "reason": "Invalid ObjectId format"}), 400 

    item = request.json
    
    # 클라이언트가 _id를 보냈다면 제거 (URL path랑 이게 충돌할 수도 있으므로)
    if '_id' in item: del item['_id'] 

    updated_result = db.items.update_one({"_id": item_obj_id}, {"$set": item})

    if updated_result.modified_count > 0:
        return jsonify({"result": "success"})
    else:
        return jsonify({"result": "failure", "reason": "업데이트 오류! Flask 콘솔 참조."}), 500
    
@router.route('/list', methods=['GET'])
def recommended_items_page():
    parameter_dict = request.args.to_dict()
    items_collection = db.items
    current_user = None
    user_details = None
    search_query = {}

    # JWT 처리
    try:
        verify_jwt_in_request(optional=True)
        current_user = get_jwt_identity()
        user_details = db.users.find_one({"username": current_user})
    except Exception:
        pass

    # 필터 처리
    category = parameter_dict.get('category')
    if category:
        search_query['category'] = category

    search_keyword = parameter_dict.get('search', '').strip()
    search_field = parameter_dict.get('search_field', '')
    if search_keyword and search_field in ['item_name', 'description', 'author']:
        search_query[search_field] = {"$regex": search_keyword, "$options": "i"}

    # 페이지네이션 처리
    page = int(parameter_dict.get('page', 1))
    per_page = int(parameter_dict.get('per_page', 10))
    skip = (page - 1) * per_page

    # 전체 문서 수 및 총 페이지 수 계산
    total_items = items_collection.count_documents(search_query)
    total_pages = (total_items // per_page) + (1 if total_items % per_page > 0 else 0)

    # 남아 있는 문서 개수에 따라 limit 조정
    remaining_items = max(0, total_items - skip)
    limit_value = min(per_page, remaining_items)

    # 아이템 조회 (내림차순 정렬 + 페이지네이션)
    items_cursor = items_collection.find(search_query).sort("shipped_count", -1).skip(skip).limit(limit_value)
    items = list(items_cursor)

    # ObjectId 변환
    for item in items:
        item['_id'] = str(item['_id'])

    # 페이지 범위 계산
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    
    if end_page - start_page < 4:
        if page < 3:
            end_page = min(5, total_pages)
        else:
            start_page = max(1, end_page - 4)
    pages_range = range(start_page, end_page + 1)

    categories = ["의료품", "문구/학용품", "서적", "전자기기", "생필품", "가방", "의류", "호신용품", "식품", "기타"]

    return render_template(
        "recommended_items/items.j2",
        items=items,
        parameter_dict=parameter_dict,
        categories=categories,
        current_user=current_user,
        user_details=user_details,
        pagination={
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'start_page': start_page,
            'end_page': end_page,
            'pages_range': pages_range,
            'has_prev': page > 1,
            'prev_num': page - 1,
            'has_next': page < total_pages,
            'next_num': page + 1
        }
    )


# @router.route('/list', methods=['GET'])
# def recommended_items_page():
#     parameter_dict = request.args.to_dict()
#     items_collection = db.items
#     current_user = None
#     user_details = None
#     search_query = {} # 필요할 때만 사용, 필터링 조건을 담음 => 없으면 전체 조회

#     # JWT
#     try:
#         verify_jwt_in_request(optional=True)
#         current_user = get_jwt_identity()
#         print(current_user)
#         user_details = db.users.find_one({"username": current_user})
#     except Exception:
#         pass

#     # 1. 카테고리 필터
#     category = parameter_dict.get('category')
#     if category:
#         search_query['category'] = category
    
#     # 2. 검색 조건
#     search_keyword = parameter_dict.get('search', '').strip()
#     search_field = parameter_dict.get('search_field', '')
#     if search_keyword and search_field in ['item_name', 'description', 'author']:
#         search_query[search_field] = {"$regex": search_keyword, "$options": "i"}

#     # 페이지네이션 파라미터
#     page = int(parameter_dict.get('page', 1))
#     per_page = int(parameter_dict.get('per_page', 10))
#     skip = (page - 1) * per_page

#     # 전체 문서 수 및 페이지 계산
#     total_items = items_collection.count_documents(search_query)
#     total_pages = (total_items + per_page - 1) // per_page  # 올림 계산

#     # 아이템 조회 && 페이지네이션
#     items_cursor = items_collection.find(search_query).sort("shipped_count", -1).skip(skip).limit(per_page)
#     items = list(items_cursor)

#     # ObjectId 변환 
#     for item in items:
#         item['_id'] = str(item['_id'])

#     # 페이지 범위 계산 ==> Jinja2 템플릿 페이지에서 사용할 것.
#     start_page = max(1, page - 2)
#     end_page = min(total_pages, page + 2)
    
#     # 페이지 범위 조정 로직
#     if end_page - start_page < 4:
#         if page < 3:
#             end_page = min(5, total_pages)
#         else:
#             start_page = max(1, end_page - 4)
#     pages_range = range(start_page, end_page + 1)

#     categories = ["의료품", "문구/학용품", "서적", "전자기기", "생필품", "가방", "의류", "호신용품", "식품", "기타"]

#     return render_template(
#         "recommended_items/items.j2",
#         items=items,
#         parameter_dict=parameter_dict,
#         categories=categories,
#         current_user=current_user,
#         user_details=user_details,
#         pagination={
#             'page': page,
#             'per_page': per_page,
#             'total_items': total_items,
#             'total_pages': total_pages,
#             'start_page': start_page,
#             'end_page': end_page,
#             'pages_range': pages_range,
#             'has_prev': page > 1,
#             'prev_num': page - 1,
#             'has_next': page < total_pages,
#             'next_num': page + 1
#         }
#     )

# @router.route('/setting', methods=['GET'])
# def admin_require_item_setting_page():
#     return render_template("admin/layout.html")

@router.route('/item/<string:item_id>/save', methods=['POST'])
def save_item(item_id):    
    current_user = None
    user_id_string = ""

    # JWT => User의 ObjectId를 가져옴
    try:
        verify_jwt_in_request(optional=True)
        current_user = get_jwt_identity()
        user_details = db.users.find_one({"username": current_user})
        user_id_string = str(user_details['_id'])
    except Exception:
        pass

    # User의 ObjectId를 담은 string을 ObjectId로 변환
    #   => User의 saved_items 필드에 아이템을 추가
    try:
        user_id = user_id_string

        item_oid = ObjectId(item_id)
        user_oid = ObjectId(user_id)

        item = db.items.find_one({"_id": item_oid})
        if not item:
            flash("아이템을 찾을 수 없습니다.","error")
            return jsonify({"result": "failure"})
        db.users.update_one(
            {"_id": user_oid},
            {"$addToSet": {"saved_items": item_oid}}
        )

        # 해당 id의 아이템의 'shipped_count'를 1 증가시킴
        db.items.update_one({"_id": item_oid}, {"$inc": {"shipped_count": 1}})    

        flash("아이템이 내 준비물 목록에 추가되었습니다.", "success")
        return jsonify({"result": "success", "item_id": item_id, "shipped_count": item['shipped_count']+1 })
    
    except Exception as e:
        flash(f"오류가 발생했습니다.: {str(e)}", "error")
        return jsonify({"result": "failure"})