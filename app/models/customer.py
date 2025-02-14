from datetime import datetime
from bson import ObjectId

class Customer:
    def __init__(self, name=None, face_embedding=None):
        self.name = name
        self.face_embedding = face_embedding
        self.phone = None
        self.email = None
        self.dob = None
        self.gender = None
        self.address = None
        self.face_images = []
        self.id_card = {
            "number": None,
            "type": None,
            "image": None,
            "ocr_text": None
        }
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "name": self.name,
            "face_embedding": self.face_embedding,
            "phone": self.phone,
            "email": self.email,
            "dob": self.dob,
            "gender": self.gender,
            "address": self.address,
            "face_images": self.face_images,
            "id_card": self.id_card,
            "created_at": self.created_at
        }