from flask import Blueprint, jsonify, request, render_template
from app.core.extension import bcrypt
from app.core.database import db
from bson import ObjectId
from bson.errors import InvalidId
import uuid

router = Blueprint("recommended_items", __name__, url_prefix="/recommended-items")



@router.route('/item', methods=['GET'])
def get_item():
    parameter_dict = request.args.to_dict()  
    object_id = parameter_dict.get('id')
    item = db.items.find_one({'_id': object_id})
    item['_id'] = str(item['_id'])
    return jsonify(item)


@router.route('/item', methods=['POST'])
def create_item():
    item = request.json
    item['_id'] = uuid.uuid4().hex
    item['shipped_count'] = 0
    item['author'] = "user123"
    item['essential'] = False
    db.items.insert_one(item)
    return jsonify({'message': 'success'})


# 아이템을 삭제합니다.
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


# 아이템을 수정합니다. # action="{{ url_for('recommended_items.edit_item') }}" method="POST"
@router.route('/item/<object_id>', methods=['PUT'])
def edit_item(object_id):
    # object_id 무효하면 거르기    
    try:
        item_obj_id = ObjectId(object_id)
    except InvalidId:
        return jsonify({"result": "failure", "reason": "Invalid ObjectId format"}), 400 
    
    item = request.json
    item['_id'] = item_obj_id
    updated_result = db.items.update_one({"_id": item_obj_id}, {"$set": item})
    # -. row 하나만 영향받아야 하므로 result.updated_count 가 1이면 result = success를 보냄
    if updated_result.modified_count > 0 or updated_result.upserted_id:
        return jsonify({"result": "success"})
    else:
        return jsonify({"result": "failure", "reason": "업데이트 오류! Flask 콘솔 참조."}), 500


@router.route('/list', methods=['GET'])
def recommended_items_page():
    parameter_dict = request.args.to_dict()    
    items_collection = db.items    
    
    # recommended_items 컬렉션에서 모든 아이템을 조회
    # 단, 'category' 파라미터가 있으면 필터링, 없으면 전체 조회
    category = parameter_dict.get('category')
    if category:
        items_cursor = items_collection.find({'category': category})
    else:
        items_cursor = items_collection.find()

    items = list(items_cursor)
    
    # ObjectId를 문자열로 변환 (템플릿에서 id attribute에 사용)
    for item in items:
        item['_id'] = str(item['_id'])
        
    # 카테고리 목록을 한 곳에서 관리
    categories = ["의료품", "문구/학용품", "서적", "전자기기", "생필품", "가방", "의류", "호신용품", "식품", "기타"]
    
    return render_template("recommended_items/items.j2", 
                           items=items, 
                           parameter_dict=parameter_dict, 
                           categories=categories
                        )

# @router.route('/setting', methods=['GET'])
# def admin_require_item_setting_page():
#     return render_template("admin/layout.html")