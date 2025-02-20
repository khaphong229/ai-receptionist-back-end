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
        images = []
        
        # Xử lý nhiều ảnh từ form-data
        if 'images[]' in request.files:
            image_files = request.files.getlist('images[]')
            for image_file in image_files:
                image_data = image_file.read()
                image = Image.open(io.BytesIO(image_data))
                images.append(np.array(image))
                
        # Xử lý nhiều ảnh từ base64
        elif request.is_json and 'images' in request.json:
            base64_images = request.json['images']
            for base64_data in base64_images:
                image_data = base64.b64decode(base64_data)
                image = Image.open(io.BytesIO(image_data))
                images.append(np.array(image))
        else:
            return jsonify({
                'status': 'error',
                'message': 'No images provided. Send either files or base64 images.'
            }), 400

        if len(images) < face_service.min_required_images:
            return jsonify({
                'status': 'error',
                'message': f'Please provide at least {face_service.min_required_images} images'
            }), 400

        # Trích xuất embeddings từ tất cả ảnh
        face_embeddings = face_service.extract_face_embeddings(images)
        if not face_embeddings:
            return jsonify({
                'status': 'error',
                'message': 'No faces detected in images'
            }), 400

        # Tìm khách hàng khớp
        match_result = face_service.find_matching_customer(face_embeddings)

        if match_result:
            customer = match_result['customer']
            confidence = match_result['confidence']
            
            # Lưu ảnh mới
            saved_images = []
            for idx, image in enumerate(images):
                image_name = f"face_{str(customer['_id'])}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{idx}.jpg"
                face_image_path = os.path.join(Config.FACE_FOLDER, image_name)
                Image.fromarray(image).save(face_image_path)
                saved_images.append(face_image_path)

            # Cập nhật embeddings
            face_service.update_customer_embeddings(customer['_id'], face_embeddings)
            
            # Cập nhật ảnh
            mongo.db.customers.update_one(
                {"_id": customer['_id']},
                {"$push": {"face_images": {"$each": saved_images}}}
            )

            return jsonify({
                'status': 'success',
                'message': 'Customer found',
                'confidence': float(confidence),
                'customer': {
                    'id': str(customer['_id']),
                    'full_name': customer.get('full_name'),
                    'email': customer.get('email'),
                    'phone': customer.get('phone'),
                    'face_images': customer.get('face_images', [])
                }
            })
        else:
            # Tạo khách hàng mới với nhiều ảnh
            saved_images = []
            for idx, image in enumerate(images):
                image_name = f"face_new_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{idx}.jpg"
                face_image_path = os.path.join(Config.FACE_FOLDER, image_name)
                Image.fromarray(image).save(face_image_path)
                saved_images.append(face_image_path)

            new_customer = Customer(face_embeddings=face_embeddings)
            new_customer.face_images = saved_images
            result = mongo.db.customers.insert_one(new_customer.to_dict())

            return jsonify({
                'status': 'success',
                'message': 'New customer created',
                'customer_id': str(result.inserted_id),
                'face_images': saved_images
            }), 201

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing images: {str(e)}'
        }), 500