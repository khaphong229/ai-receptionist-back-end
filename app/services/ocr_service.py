# import easyocr

# reader = easyocr.Reader(["en"])

# def extract_text(image):
#     result = reader.readtext(image.read(), detail=0)
#     return " ".join(result)

import os
from typing import Dict, Optional
import easyocr
from ultralytics import YOLO
import numpy as np
import cv2
from ..database import mongo
from ..config import Config
from datetime import datetime

class OCRService:
    def __init__(self):
        """Initialize OCR Service with EasyOCR and YOLO"""
        # Initialize EasyOCR
        self.reader = easyocr.Reader(['vi', 'en'], gpu=False)
        
        # Initialize YOLO for ID card detection
        self.yolo = YOLO('yolov8n.pt')
        
        self.id_fields = {
            'Số': 'id_number',
            'Họ và tên': 'full_name',
            'Ngày sinh': 'date_of_birth',
            'Giới tính': 'gender',
            'Quê quán': 'place_of_origin',
            'Nơi thường trú': 'place_of_residence'
        }

    def extract_id_info(self, image_path: str) -> Optional[Dict]:
        """
        Extract information from ID card image
        
        Args:
            image_path: Path to the ID card image
            
        Returns:
            Dict: Extracted information or None if failed
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise Exception("Cannot read image")

            # Detect ID card in image
            results = self.yolo(image)
            boxes = results[0].boxes

            # If ID card detected, crop the image
            if len(boxes) > 0:
                box = boxes[0].xyxy[0].cpu().numpy()  # Get first detection
                x1, y1, x2, y2 = map(int, box)
                image = image[y1:y2, x1:x2]

            # Perform OCR
            results = self.reader.readtext(image)
            
            # Process extracted text
            extracted_info = {}
            current_field = None
            
            for detection in results:
                text = detection[1].strip()
                
                # Skip empty text
                if not text:
                    continue
                
                # Check if text is a field name
                for field_name, field_key in self.id_fields.items():
                    if field_name in text:
                        current_field = field_key
                        # Extract value if it's in the same line
                        value = text.replace(field_name, '').strip(':/ ')
                        if value:
                            extracted_info[current_field] = value
                        break
                else:
                    # If text is not a field name and we have a current field
                    if current_field and current_field not in extracted_info:
                        extracted_info[current_field] = text
                        current_field = None
            
            # Clean and validate extracted data
            if 'id_number' not in extracted_info:
                return None
                
            # Format date of birth if present
            if 'date_of_birth' in extracted_info:
                try:
                    dob = datetime.strptime(extracted_info['date_of_birth'], '%d/%m/%Y')
                    extracted_info['date_of_birth'] = dob
                except:
                    pass
            
            return extracted_info
            
        except Exception as e:
            print(f"Error extracting ID info: {str(e)}")
            return None

    def save_customer_info(self, id_info: Dict, id_image_path: str) -> Optional[str]:
        """
        Save extracted customer information to database
        
        Args:
            id_info: Extracted ID information
            id_image_path: Path to ID card image
            
        Returns:
            str: Customer ID if successful, None if failed
        """
        try:
            # Prepare customer data
            customer_data = {
                'id_number': id_info.get('id_number'),
                'full_name': id_info.get('full_name'),
                'date_of_birth': id_info.get('date_of_birth'),
                'gender': id_info.get('gender'),
                'place_of_origin': id_info.get('place_of_origin'),
                'place_of_residence': id_info.get('place_of_residence'),
                'id_image': id_image_path,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Check if customer already exists
            existing_customer = mongo.db.customers.find_one({
                'id_number': id_info['id_number']
            })
            
            if existing_customer:
                # Update existing customer
                mongo.db.customers.update_one(
                    {'_id': existing_customer['_id']},
                    {'$set': {
                        **customer_data,
                        'updated_at': datetime.utcnow()
                    }}
                )
                return str(existing_customer['_id'])
            else:
                # Insert new customer
                result = mongo.db.customers.insert_one(customer_data)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"Error saving customer info: {str(e)}")
            return None
