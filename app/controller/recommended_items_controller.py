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
    item['author'] = "user123"
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
    
    category = parameter_dict.get('category')
    if category:
        items_cursor = items_collection.find({'category': category})
    else:
        items_cursor = items_collection.find()

    items = list(items_cursor)
    
    for item in items:
        item['_id'] = str(item['_id'])  # ObjectId → String 변환

    categories = ["의료품", "문구/학용품", "서적", "전자기기", "생필품", "가방", "의류", "호신용품", "식품", "기타"]
    
    return render_template("recommended_items/items.j2", 
                           items=items, 
                           parameter_dict=parameter_dict, 
                           categories=categories
                        )


# @router.route('/setting', methods=['GET'])
# def admin_require_item_setting_page():
#     return render_template("admin/layout.html")