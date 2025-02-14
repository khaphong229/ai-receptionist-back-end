from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from bson import ObjectId
from ..services.face_service import FaceService
from ..database import mongo
from ..models.customer import Customer  # Add this import
from ..config import Config

face_bp = Blueprint("face_recognition", __name__)
face_service = FaceService()

@face_bp.route("/recognize", methods=["POST"])
def recognize_face():
    if 'image' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No image uploaded'
        }), 400

    try:
        image_file = request.files['image']
        image_data = image_file.read()
        face_embedding = face_service.extract_face_embedding(image)
        
        if face_embedding is None:
            return jsonify({
                'status': 'error',
                'message': 'No face detected in image'
            }), 400

        # Find matching customer
        matching_customer = face_service.find_matching_customer(face_embedding)

        if matching_customer:
            # Save face image
            image_file.seek(0)  # Reset file pointer
            face_image_path = face_service.save_face_image(image_file)
            
            # Update face_images array
            mongo.db.customers.update_one(
                {"_id": matching_customer['_id']},
                {"$push": {"face_images": face_image_path}}
            )
            # Get appointments
            appointments = list(mongo.db.appointments.find(
                {"customer_id": matching_customer['_id'],
                 "status": "confirmed"},
                {"_id": 0}
            ))

            # Save face log
            face_service.save_face_log(
                matching_customer['_id'],
                "face_recognition_log.jpg",
                "matched"
            )

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
            # Save face image for new customer
            image_file.seek(0)
            face_image_path = face_service.save_face_image(image_file)

            # Create new customer
            new_customer = Customer(face_embedding=face_embedding)
            new_customer.face_images = [face_image_path]
            result = mongo.db.customers.insert_one(new_customer.to_dict())
            
            # Save face log
            face_service.save_face_log(
                result.inserted_id,
                "face_recognition_log.jpg",
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


@face_bp.route("/customer/<customer_id>", methods=["PUT"])
def update_customer(customer_id):
    try:
        customer_data = request.json
        
        # Remove fields that shouldn't be updated directly
        customer_data.pop('face_embedding', None)
        customer_data.pop('created_at', None)
        
        result = mongo.db.customers.update_one(
            {"_id": ObjectId(customer_id)},
            {"$set": customer_data}
        )
        
        if result.modified_count > 0:
            return jsonify({
                'status': 'success',
                'message': 'Customer information updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Customer not found'
            }), 404

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating customer: {str(e)}'
        }), 500