from datetime import datetime
from bson import ObjectId

class Customer:
    def __init__(self, full_name=None, face_embedding=None):
        self.full_name = full_name
        self.face_embedding = face_embedding
        self.phone = None
        self.email = None
        self.date_of_birth = None
        self.gender = None
        self.address = None
        self.face_images = []
        self.id_number = None
        self.nationality = None
        self.place_of_origin = None
        self.place_of_residence = None
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "full_name": self.full_name,
            "face_embedding": self.face_embedding,
            "phone": self.phone,
            "email": self.email,
            "date_of_birth": self.date_of_birth,
            "gender": self.gender,
            "address": self.address,
            "face_images": self.face_images,
            "id_number": self.id_number,
            "nationality": self.nationality,
            "place_of_origin": self.place_of_origin,
            "place_of_residence": self.place_of_residence,
            "created_at": self.created_at
        }