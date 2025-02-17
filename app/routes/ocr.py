from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from ..services.ocr_service import OCRService
from ..config import Config
from ..utils.file_handler import save_file

ocr_bp = Blueprint('ocr', __name__)
ocr_service = OCRService()

@ocr_bp.route('/extract-id', methods=['POST'])
def extract_id():
    """API endpoint to extract information from ID card"""
    try:
        # Check if image file is present
        if 'id_image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image file provided'
            }), 400
            
        id_image = request.files['id_image']
        
        if id_image.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No selected file'
            }), 400
            
        # Save ID image
        id_image_path = save_file(id_image, Config.ID_FOLDER)
        
        if not id_image_path:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save image'
            }), 500
            
        # Extract information from ID
        id_info = ocr_service.extract_id_info(id_image_path)
        
        if not id_info:
            return jsonify({
                'status': 'error',
                'message': 'Failed to extract information from ID'
            }), 400
            
        # Save customer information
        customer_id = ocr_service.save_customer_info(id_info, id_image_path)
        
        if not customer_id:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save customer information'
            }), 500
            
        return jsonify({
            'status': 'success',
            'data': {
                'customer_id': customer_id,
                'id_info': id_info
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
