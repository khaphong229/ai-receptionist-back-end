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
        self.similarity_threshold = 0.85
        self.min_required_images = 3  # Số ảnh tối thiểu để training
        self.max_faces_per_person = 10  # Số ảnh tối đa cho mỗi người

    def extract_face_embeddings(self, images):
        """
        Trích xuất embeddings từ nhiều ảnh
        
        Args:
            images: List các ảnh (numpy arrays)
            
        Returns:
            List[np.array]: Danh sách các embedding
        """
        embeddings = []
        for img in images:
            try:
                if isinstance(img, (bytes, bytearray)):
                    nparr = np.frombuffer(img, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                elif not isinstance(img, np.ndarray):
                    img = np.array(img)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                faces = self.face_app.get(img)
                if faces:
                    # Lấy khuôn mặt lớn nhất
                    face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
                    embeddings.append(face.embedding)
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                continue
                
        return embeddings

    def get_average_embedding(self, embeddings):
        """Tính embedding trung bình từ nhiều ảnh"""
        if not embeddings:
            return None
        avg_embedding = np.mean(embeddings, axis=0)
        return avg_embedding.tolist()

    def find_matching_customer(self, face_embeddings):
        """
        Tìm khách hàng khớp với nhiều face embeddings
        
        Args:
            face_embeddings: List các face embedding
            
        Returns:
            dict: Thông tin khách hàng và độ tin cậy
        """
        if not face_embeddings:
            return None

        customers = mongo.db.customers.find({})
        best_match = None
        highest_confidence = 0
        
        # Tính embedding trung bình
        avg_embedding = self.get_average_embedding(face_embeddings)

        for customer in customers:
            if 'face_embeddings' in customer:
                # Tính độ tương đồng với tất cả embeddings của khách hàng
                similarities = []
                for stored_embedding in customer['face_embeddings']:
                    similarity = self.compare_faces(avg_embedding, stored_embedding)
                    similarities.append(similarity)
                
                # Lấy độ tin cậy trung bình
                if similarities:
                    avg_similarity = np.mean(similarities)
                    if avg_similarity > self.similarity_threshold and avg_similarity > highest_confidence:
                        highest_confidence = avg_similarity
                        best_match = {
                            'customer': customer,
                            'confidence': avg_similarity
                        }

        return best_match

    def update_customer_embeddings(self, customer_id, new_embeddings):
        """Cập nhật embeddings cho khách hàng"""
        try:
            current = mongo.db.customers.find_one({'_id': customer_id})
            if current and 'face_embeddings' in current:
                existing_embeddings = current['face_embeddings']
                # Giới hạn số lượng embeddings
                total_embeddings = existing_embeddings + new_embeddings
                if len(total_embeddings) > self.max_faces_per_person:
                    total_embeddings = total_embeddings[:self.max_faces_per_person]
                
                mongo.db.customers.update_one(
                    {'_id': customer_id},
                    {'$set': {'face_embeddings': total_embeddings}}
                )
            else:
                mongo.db.customers.update_one(
                    {'_id': customer_id},
                    {'$set': {'face_embeddings': new_embeddings}}
                )
            return True
        except Exception as e:
            print(f"Error updating embeddings: {str(e)}")
            return False

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