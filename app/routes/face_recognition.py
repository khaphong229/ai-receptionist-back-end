from flask import Blueprint, request, jsonify
import base64
import io
from PIL import Image
import numpy as np
import os
from bson import ObjectId
from ..services.face_service import FaceService
from ..database import mongo
from ..models.customer import Customer
from ..config import Config
from datetime import datetime

face_bp = Blueprint("face_recognition", __name__)
face_service = FaceService()

@face_bp.route("/recognize", methods=["POST"])
def recognize_face():
    """
    API endpoint để nhận diện khuôn mặt.
    Hỗ trợ cả file upload và base64 image.
    
    Flow:
    1. Nhận ảnh từ request
    2. Trích xuất face embedding
    3. Tìm khách hàng khớp trong database
    4. Nếu tìm thấy: trả về thông tin khách hàng
    5. Nếu không tìm thấy: tạo khách hàng mới
    
    Returns:
        JSON response với thông tin khách hàng hoặc thông báo lỗi
    """
    try:
        # Kiểm tra loại dữ liệu gửi lên
        if 'image' in request.files:
            # Xử lý file upload
            image_file = request.files['image']
            image_data = image_file.read()
        elif request.is_json and 'image' in request.json:
            # Xử lý base64 image
            base64_data = request.json['image']
            image_data = base64.b64decode(base64_data)
        else:
            return jsonify({
                'status': 'error',
                'message': 'No image provided. Send either a file or base64 image.'
            }), 400

        # Chuyển đổi image data thành numpy array
        image = Image.open(io.BytesIO(image_data))
        image_array = np.array(image)
        
        # Trích xuất face embedding
        face_embedding = face_service.extract_face_embedding(image_array)
        if face_embedding is None:
            return jsonify({
                'status': 'error',
                'message': 'No face detected in image'
            }), 400

        # Tìm khách hàng khớp
        matching_customer = face_service.find_matching_customer(face_embedding)

        if matching_customer:
            # Xử lý khách hàng đã tồn tại
            # Lưu ảnh
            image_name = f"face_{str(matching_customer['_id'])}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
            face_image_path = os.path.join(Config.FACE_FOLDER, image_name)
            image.save(face_image_path)
            
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

            return jsonify({
                'status': 'success',
                'message': 'Customer found',
                'customer': {
                    'id': str(matching_customer['_id']),
                    'full_name': matching_customer.get('full_name'),
                    'email': matching_customer.get('email'),
                    'phone': matching_customer.get('phone'),
                    'face_images': matching_customer.get('face_images', []),
                    'id_number': matching_customer.get('id_number'),
                    'nationality': matching_customer.get('nationality'),
                    'place_of_origin': matching_customer.get('place_of_origin'),
                    'place_of_residence': matching_customer.get('place_of_residence'),
                },
                'appointments': appointments
            })
        else:
            # Xử lý khách hàng mới
            image_name = f"face_new_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
            face_image_path = os.path.join(Config.FACE_FOLDER, image_name)
            image.save(face_image_path)

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