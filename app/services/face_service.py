import cv2
import numpy as np
from datetime import datetime
import insightface
from insightface.app import FaceAnalysis
from ..database import mongo
from ..models.customer import Customer
from ..config import Config
from ..utils.file_handler import save_file
import os

class FaceService:
    def __init__(self):
        """
        Khởi tạo FaceService với model InsightFace
        """
        self.face_app = FaceAnalysis(name='buffalo_l')
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        self.similarity_threshold = 0.85  # Ngưỡng so sánh khuôn mặt

    def extract_face_embedding(self, image):
        """
        Trích xuất face embedding từ ảnh
        
        Args:
            image: Ảnh dưới dạng bytes, numpy array hoặc PIL Image
            
        Returns:
            face_embedding: Vector đặc trưng khuôn mặt hoặc None nếu không tìm thấy
        """
        try:
            # Chuyển đổi ảnh sang numpy array nếu cần
            if isinstance(image, (bytes, bytearray)):
                nparr = np.frombuffer(image, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(image, np.ndarray):
                img = image
            else:
                # Nếu là PIL Image
                img = np.array(image)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Phát hiện khuôn mặt
            faces = self.face_app.get(img)
            if not faces:
                return None
                
            # Lấy khuôn mặt lớn nhất nếu có nhiều khuôn mặt
            face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
            return face.embedding.tolist()
            
        except Exception as e:
            print(f"Error in extract_face_embedding: {str(e)}")
            return None

    def compare_faces(self, embedding1, embedding2):
        """
        So sánh hai face embedding
        
        Args:
            embedding1, embedding2: Hai vector đặc trưng khuôn mặt
            
        Returns:
            float: Độ tương đồng (0-1)
        """
        if embedding1 is None or embedding2 is None:
            return 0
            
        # Chuyển về numpy array
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        
        # Tính cosine similarity
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0
            
        cos_sim = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return cos_sim

    def find_matching_customer(self, face_embedding):
        """
        Tìm khách hàng khớp với face embedding trong database
        
        Args:
            face_embedding: Vector đặc trưng khuôn mặt cần tìm
            
        Returns:
            dict: Thông tin khách hàng nếu tìm thấy, None nếu không
        """
        customers = mongo.db.customers.find({})
        best_match = None
        highest_similarity = 0

        for customer in customers:
            if 'face_embedding' in customer:
                similarity = self.compare_faces(face_embedding, customer['face_embedding'])
                if similarity > self.similarity_threshold and similarity > highest_similarity:
                    highest_similarity = similarity
                    best_match = customer

        return best_match

    def save_face_log(self, customer_id, image_path, status):
        """
        Lưu log nhận diện khuôn mặt
        
        Args:
            customer_id: ID của khách hàng
            image_path: Đường dẫn ảnh khuôn mặt
            status: Trạng thái nhận diện ("matched" hoặc "new")
        """
        log = {
            "customer_id": customer_id,
            "image": image_path,
            "recognized_at": datetime.utcnow(),
            "status": status
        }
        mongo.db.face_logs.insert_one(log)

    def save_face_image(self, image_file):
        """
        Lưu ảnh khuôn mặt
        
        Args:
            image_file: File ảnh từ request
            
        Returns:
            str: Đường dẫn tới ảnh đã lưu
        """
        return save_file(image_file, Config.FACE_FOLDER)

    def save_id_image(self, image_file):
        """
        Lưu ảnh CCCD/CMND
        
        Args:
            image_file: File ảnh từ request
            
        Returns:
            str: Đường dẫn tới ảnh đã lưu
        """
        return save_file(image_file, Config.ID_FOLDER)