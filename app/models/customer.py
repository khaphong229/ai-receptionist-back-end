from datetime import datetime
from bson import ObjectId
import numpy as np

class Customer:
    def __init__(self, face_embedding=None, face_embeddings=None):
        """
        Khởi tạo Customer model
        
        Args:
            face_embedding: Single face embedding (legacy support)
            face_embeddings: List of face embeddings (new multi-face support)
        """
        self.face_embeddings = []
        if face_embedding is not None:
            # Convert numpy array to list
            if isinstance(face_embedding, np.ndarray):
                face_embedding = face_embedding.tolist()
            self.face_embeddings.append(face_embedding)
            
        if face_embeddings is not None:
            # Convert numpy arrays to lists
            face_embeddings = [
                emb.tolist() if isinstance(emb, np.ndarray) else emb 
                for emb in face_embeddings
            ]
            self.face_embeddings.extend(face_embeddings)
            
        self.face_images = []
        self.full_name = None
        self.email = None
        self.phone = None
        self.id_number = None
        self.date_of_birth = None
        self.gender = None
        self.nationality = None
        self.place_of_origin = None
        self.place_of_residence = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert customer object to dictionary"""
        return {
            'face_embeddings': self.face_embeddings,
            'face_images': self.face_images,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'id_number': self.id_number,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'nationality': self.nationality,
            'place_of_origin': self.place_of_origin,
            'place_of_residence': self.place_of_residence,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @staticmethod
    def from_dict(data):
        """Create customer object from dictionary"""
        customer = Customer()
        customer.face_embeddings = data.get('face_embeddings', [])
        customer.face_images = data.get('face_images', [])
        customer.full_name = data.get('full_name')
        customer.email = data.get('email')
        customer.phone = data.get('phone')
        customer.id_number = data.get('id_number')
        customer.date_of_birth = data.get('date_of_birth')
        customer.gender = data.get('gender')
        customer.nationality = data.get('nationality')
        customer.place_of_origin = data.get('place_of_origin')
        customer.place_of_residence = data.get('place_of_residence')
        customer.created_at = data.get('created_at', datetime.utcnow())
        customer.updated_at = data.get('updated_at', datetime.utcnow())
        return customer