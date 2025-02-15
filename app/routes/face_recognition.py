from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from bson import ObjectId
from ..services.face_service import FaceService
from ..database import mongo
from ..models.customer import Customer
from ..config import Config

face_bp = Blueprint("face_recognition", __name__)
face_service = FaceService()

@face_bp.route("/recognize", methods=["POST"])
def recognize_face():
    """
    API endpoint để nhận diện khuôn mặt.
    
    Flow:
    1. Nhận ảnh từ request
    2. Trích xuất face embedding
    3. Tìm khách hàng khớp trong database
    4. Nếu tìm thấy: trả về thông tin khách hàng
    5. Nếu không tìm thấy: tạo khách hàng mới
    
    Returns:
        JSON response với thông tin khách hàng hoặc thông báo lỗi
    """
    # Kiểm tra có file ảnh trong request không
    if 'image' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No image uploaded'
        }), 400

    try:
        # Đọc và xử lý ảnh
        image_file = request.files['image']
        image_data = image_file.read()
        
        # Trích xuất face embedding
        face_embedding = face_service.extract_face_embedding(image_data)
        if face_embedding is None:
            return jsonify({
                'status': 'error',
                'message': 'No face detected in image'
            }), 400

        # Tìm khách hàng khớp
        matching_customer = face_service.find_matching_customer(face_embedding)

        if matching_customer:
            # Xử lý khách hàng đã tồn tại
            image_file.seek(0)  # Reset con trỏ file để đọc lại
            face_image_path = face_service.save_face_image(image_file)
            
            # Cập nhật mảng ảnh khuôn mặt
            mongo.db.customers.update_one(
                {"_id": matching_customer['_id']},
                {"$push": {"face_images": face_image_path}}
            )

            # Lấy thông tin lịch hẹn
            appointments = list(mongo.db.appointments.find(
                {"customer_id": matching_customer['_id'],
                 "status": "confirmed"},
                {"_id": 0}
            ))

            # Lưu log nhận diện
            face_service.save_face_log(
                matching_customer['_id'],
                face_image_path,
                "matched"
            )

            # Trả về thông tin khách hàng
            return jsonify({
                'status': 'success',
                'message': 'Customer found',
                'customer': {
                    'id': str(matching_customer['_id']),
                    'name': matching_customer.get('name'),
                    'email': matching_customer.get('email'),
                    'phone': matching_customer.get('phone'),
                    'face_images': matching_customer.get('face_images', []),
                    'id_card': matching_customer.get('id_card'),
                },
                'appointments': appointments
            })
        else:
            # Xử lý khách hàng mới
            image_file.seek(0)
            face_image_path = face_service.save_face_image(image_file)

            # Tạo khách hàng mới
            new_customer = Customer(face_embedding=face_embedding)
            new_customer.face_images = [face_image_path]
            result = mongo.db.customers.insert_one(new_customer.to_dict())
            
            # Lưu log nhận diện
            face_service.save_face_log(
                result.inserted_id,
                face_image_path,
                "new"
            )

            # Trả về thông tin khách hàng mới
            return jsonify({
                'status': 'success',
                'message': 'New customer created',
                'customer_id': str(result.inserted_id),
                'face_image': face_image_path
            }), 201

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing image: {str(e)}'
        }), 500