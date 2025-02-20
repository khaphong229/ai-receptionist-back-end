import os
from typing import Dict, Optional
import easyocr
import cv2
import numpy as np
from ..database import mongo
from ..config import Config
from datetime import datetime
from bson import ObjectId

class OCRService:
    def __init__(self):
        """Initialize OCR Service with EasyOCR"""
        # Initialize EasyOCR with Vietnamese and English
        self.reader = easyocr.Reader(['vi', 'en'], gpu=False)
        
        # Định nghĩa các trường thông tin trên CCCD gắn chip
        self.id_fields = {
            'Số/No': 'id_number',
            'Họ và tên/Full name': 'full_name',
            'Ngày sinh/Date of birth': 'date_of_birth',
            'Giới tính/Sex': 'gender',
            'Quốc tịch/Nationality': 'nationality',
            'Quê quán/Place of origin': 'place_of_origin',
            'Nơi thường trú/Place of residence': 'place_of_residence'
        }

    def preprocess_image(self, image):
        """Tiền xử lý ảnh để tăng chất lượng OCR"""
        # Chuyển sang grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Tăng độ tương phản
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Giảm nhiễu
        denoised = cv2.fastNlMeansDenoising(gray)
        
        return denoised

    def extract_id_info(self, image_path: str) -> Optional[Dict]:
        """Extract information from ID card image"""
        try:
            # read image
            image = cv2.imread(image_path)
            if image is None:
                raise Exception("Cannot read image")

            # Tiền xử lý ảnh
            processed_image = self.preprocess_image(image)

            # Thực hiện OCR
            results = self.reader.readtext(processed_image)
            
            # Khởi tạo dict để lưu thông tin
            extracted_info = {}

            # Khởi tạo biến để theo dõi trạng thái đang xử lý
            is_processing_origin = False
            is_processing_residence = False
            current_origin = []
            current_residence = []
            
            # Xử lý từng dòng text
            for idx, detection in enumerate(results):
                text = detection[1].strip()
                
                # Xử lý số CCCD (12 chữ số)
                if text.isdigit() and len(text) == 12:
                    extracted_info['id_number'] = text
                    continue
                    
                # Xử lý họ tên (thường nằm sau "Họ và tên" hoặc "Full name")
                if ('HỌ VÀ TÊN' in text.upper() or 'FULL NAME' in text.upper()) and idx + 1 < len(results):
                    extracted_info['full_name'] = results[idx + 1][1].strip()
                    continue
                    
                # Xử lý ngày sinh
                if ('Date of bỉrth: ' in text or 'NGÀY SINH' in text.upper() or 'DATE OF BIRTH' in text.upper()) and idx + 1 < len(results):
                    date_text = results[idx + 1][1].strip()
                    # Chuẩn hóa format ngày
                    date_parts = date_text.replace('-', '/').split('/')
                    if len(date_parts) == 3:
                        extracted_info['date_of_birth'] = f"{date_parts[0]}/{date_parts[1]}/{date_parts[2]}"
                    continue
                    
                # Xử lý giới tính
                if 'Nam' in text or 'Nữ' in text or 'NAME' in text.upper() or 'NỮ' in text.upper():
                    # Tìm giới tính trong cùng dòng hoặc dòng tiếp theo
                    if 'NAM' in text.upper() or 'MALE' in text.upper():
                        extracted_info['gender'] = 'Male'
                    elif 'NỮ' in text.upper() or 'FEMALE' in text.upper():
                        extracted_info['gender'] = 'Female'
                    continue
                    
                # Xử lý quốc tịch
                if 'Việt Nam' in text or "NAM" in text.upper() or 'VIỆT' in text.upper() or 'Vietnam' in text or 'VIỆT NAM' in text.upper() or 'VIETNAM' in text.upper():
                    extracted_info['nationality'] = 'Viet Nam'
                    continue
                    
                # Xử lý quê quán
                if ('QUÊ' in text.upper() or 'PLACE OF ORIGIN' in text.upper()):
                    is_processing_origin = True
                    is_processing_residence = False
                    continue

                # Kiểm tra bắt đầu phần nơi thường trú
                if ('NƠI THƯỜNG TRÚ' in text.upper() or 'PLACE OF RESIDENCE' in text.upper()):
                    is_processing_origin = False
                    is_processing_residence = True
                    continue

                # Xử lý các text tiếp theo cho quê quán
                if is_processing_origin:
                    # Kiểm tra text có phải là tiếng Việt hợp lệ
                    if any(c.isalpha() for c in text) and not any(c.isdigit() for c in text):
                        # Loại bỏ các từ khóa không mong muốn
                        if not any(keyword in text.upper() for keyword in ['PLACE', 'DATE', 'SEX', 'NATIONALITY', 'ORIGIN', 'RESIDENCE']):
                            current_origin.append(text)

                # Xử lý các text tiếp theo cho nơi thường trú
                if is_processing_residence:
                    # Kiểm tra text có phải là tiếng Việt hợp lệ
                    if any(c.isalpha() for c in text) and not any(c.isdigit() for c in text):
                        # Loại bỏ các từ khóa không mong muốn
                        if not any(keyword in text.upper() for keyword in ['PLACE', 'DATE', 'SEX', 'NATIONALITY', 'ORIGIN', 'RESIDENCE']):
                            current_residence.append(text)

            # Chuẩn hóa dữ liệu địa chỉ
            if current_origin:
                extracted_info['place_of_origin'] = ', '.join(current_origin)
            if current_residence:
                extracted_info['place_of_residence'] = ', '.join(current_residence)

            # Chuẩn hóa dữ liệu địa chỉ
            for field in ['place_of_origin', 'place_of_residence']:
                if field in extracted_info:
                    # Loại bỏ các ký tự đặc biệt và khoảng trắng thừa
                    extracted_info[field] = ' '.join(extracted_info[field].split())
                    # Chuẩn hóa các từ viết tắt phổ biến
                    extracted_info[field] = extracted_info[field].replace('Tx.', 'Thị xã')
                    extracted_info[field] = extracted_info[field].replace('P.', 'Phường')
                    extracted_info[field] = extracted_info[field].replace('Q.', 'Quận')
                    extracted_info[field] = extracted_info[field].replace('Tp.', 'Thành phố')
                    # Loại bỏ dấu phẩy thừa
                    extracted_info[field] = ', '.join(part.strip() for part in extracted_info[field].split(',') if part.strip())

            return extracted_info
                
        except Exception as e:
            print(f"Error extracting ID info: {str(e)}")
            return None

    def update_customer_info(self, customer_id: str, customer_data: Dict) -> bool:
        """Update customer information in database"""
        try:
            # Remove None values
            update_data = {k: v for k, v in customer_data.items() if v is not None}
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Update customer
            result = mongo.db.customers.update_one(
                {'_id': ObjectId(customer_id)},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating customer info: {str(e)}")
            return False

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
