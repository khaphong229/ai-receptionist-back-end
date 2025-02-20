from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from ..services.ocr_service import OCRService
from ..config import Config
from ..utils.file_handler import save_file
import base64
import io
from PIL import Image
import numpy as np
from datetime import datetime

ocr_bp = Blueprint('ocr', __name__)
ocr_service = OCRService()

@ocr_bp.route('/extract-id', methods=['POST'])
def extract_id():
    """API endpoint to extract information from ID card"""
    try:
        # Check if image is sent as file or base64
        if 'id_image' in request.files:
            # Handle file upload
            id_image = request.files['id_image']
            if id_image.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'No selected file'
                }), 400
            
            # Save ID image
            id_image_path = save_file(id_image, Config.ID_FOLDER)
            
        elif request.is_json and 'image' in request.json:
            # Handle base64 image
            base64_data = request.json['image']
            image_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_data))
            
            # Save image
            image_name = f"id_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
            id_image_path = os.path.join(Config.ID_FOLDER, image_name)
            image.save(id_image_path)
        else:
            return jsonify({
                'status': 'error',
                'message': 'No image provided'
            }), 400
            
        # Extract information from ID
        id_info = ocr_service.extract_id_info(id_image_path)
        
        if not id_info:
            return jsonify({
                'status': 'error',
                'message': 'Failed to extract information from ID'
            }), 400
            
        return jsonify({
            'status': 'success',
            'data': id_info
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@ocr_bp.route('/update-customer', methods=['PUT'])
def update_customer():
    """API endpoint to update customer information"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
            
        customer_id = data.get('customer_id')
        if not customer_id:
            return jsonify({
                'status': 'error',
                'message': 'Customer ID is required'
            }), 400
            
        # Update customer info
        updated = ocr_service.update_customer_info(
            customer_id=customer_id,
            customer_data={
                'id_number': data.get('id_number'),
                'full_name': data.get('full_name'),
                'date_of_birth': data.get('date_of_birth'),
                'gender': data.get('gender'),
                'nationality': data.get('nationality'),
                'place_of_origin': data.get('place_of_origin'),
                'place_of_residence': data.get('place_of_residence'),
                'phone': data.get('phone'),
                'email': data.get('email')
            }
        )
        
        if not updated:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update customer information'
            }), 500
            
        return jsonify({
            'status': 'success',
            'message': 'Customer information updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
