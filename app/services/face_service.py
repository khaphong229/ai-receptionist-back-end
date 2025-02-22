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
        # Tăng kích thước detect mặc định
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        self.similarity_threshold = 0.6
        self.min_required_images = 3  # Số ảnh tối thiểu để training
        self.max_faces_per_person = 10  # Số ảnh tối đa cho mỗi người

    def extract_face_embeddings(self, images):
        """
        Trích xuất embeddings với chất lượng cao
        """
        embeddings = []
        for img in images:
            try:
                if isinstance(img, (bytes, bytearray)):
                    nparr = np.frombuffer(img, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                elif not isinstance(img, np.ndarray):
                    img = np.array(img)
                
                # Chuẩn hóa ảnh
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                # Đảm bảo ảnh có kích thước phù hợp
                min_size = 640
                height, width = img.shape[:2]
                scale = min_size / min(height, width)
                if scale > 1:
                    img = cv2.resize(img, (int(width * scale), int(height * scale)))

                # Detect faces
                faces = self.face_app.get(img)
                
                if faces:
                    # Lọc faces có độ tin cậy cao
                    quality_faces = []
                    for face in faces:
                        # Kiểm tra kích thước khuôn mặt
                        bbox = face.bbox
                        face_width = bbox[2] - bbox[0]
                        face_height = bbox[3] - bbox[1]
                        min_face_size = min(face_width, face_height)
                        
                        # Chỉ lấy faces đủ lớn và có độ tin cậy cao
                        if min_face_size >= 80 and face.det_score >= 0.5:
                            quality_faces.append(face)

                    if quality_faces:
                        # Chọn mặt rõ nhất
                        best_face = max(quality_faces, key=lambda x: x.det_score)
                        embeddings.append(best_face.embedding)
                        
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
        Tìm khách hàng khớp với face embeddings
        Cải thiện độ chính xác bằng cách:
        1. So sánh với tất cả embeddings đã lưu
        2. Tính điểm trung bình của top matches
        3. Áp dụng voting để quyết định
        """
        try:
            customers = list(mongo.db.customers.find())
            if not customers:
                return None

            best_matches = []
            
            # So sánh với từng customer
            for customer in customers:
                stored_embeddings = customer.get('face_embeddings', [])
                if not stored_embeddings:
                    continue

                match_scores = []
                # So sánh từng embedding mới với tất cả embedding đã lưu
                for new_emb in face_embeddings:
                    scores = []
                    for stored_emb in stored_embeddings:
                        similarity = self.compare_faces(new_emb, stored_emb)
                        scores.append(similarity)
                    # Lấy điểm cao nhất cho embedding này
                    match_scores.append(max(scores))

                # Tính điểm trung bình của top 3 matches
                top_scores = sorted(match_scores, reverse=True)[:3]
                avg_score = sum(top_scores) / len(top_scores)

                if avg_score > self.similarity_threshold:
                    best_matches.append({
                        'customer': customer,
                        'confidence': avg_score
                    })

            if best_matches:
                # Chọn customer có điểm cao nhất
                best_match = max(best_matches, key=lambda x: x['confidence'])
                if best_match['confidence'] > 0.7:  # Thêm ngưỡng tin cậy cao
                    return best_match

            return None

        except Exception as e:
            print(f"Error finding matching customer: {str(e)}")
            return None

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
        So sánh hai face embedding với độ chính xác cao
        """
        if embedding1 is None or embedding2 is None:
            return 0
            
        # Chuyển về numpy array và normalize
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        
        # L2 normalization
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Tính cosine similarity và áp dụng sigmoid
        cos_sim = np.dot(embedding1, embedding2)
        similarity = 1 / (1 + np.exp(-12 * (cos_sim - 0.4)))
        
        return float(similarity)

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