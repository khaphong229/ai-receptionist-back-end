import cv2
import numpy as np
from datetime import datetime
import insightface
from insightface.app import FaceAnalysis
from ..database import mongo
from ..models.customer import Customer
from ..config import Config
from utils.file_handler import save_file

class FaceService:
    def __init__(self):
        self.face_app = FaceAnalysis(name='buffalo_l')
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        self.similarity_threshold = 0.5

    def extract_face_embedding(self, image):
        """Extract face embedding from image"""
        if isinstance(image, (bytes, bytearray)):
            nparr = np.frombuffer(image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            img = image

        faces = self.face_app.get(img)
        if not faces:
            return None
            
        # Get the largest face if multiple faces detected
        face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
        return face.embedding.tolist()

    def compare_faces(self, embedding1, embedding2):
        """Compare two face embeddings"""
        if embedding1 is None or embedding2 is None:
            return 0
        return np.dot(embedding1, embedding2)

    def find_matching_customer(self, face_embedding):
        """Find matching customer in database"""
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
        """Save face recognition log"""
        log = {
            "customer_id": customer_id,
            "image": image_path,
            "recognized_at": datetime.utcnow(),
            "status": status
        }
        mongo.db.face_logs.insert_one(log)

    def save_face_image(self, image_file):
        """Lưu ảnh khuôn mặt và trả về đường dẫn"""
        return save_file(image_file, Config.FACE_FOLDER)

    def save_id_image(self, image_file):
        """Lưu ảnh CCCD/CMND và trả về đường dẫn"""
        return save_file(image_file, Config.ID_FOLDER)