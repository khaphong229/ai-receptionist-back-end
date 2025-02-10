import cv2
import numpy as np

def process_face(image):
    image_np = np.frombuffer(image.read(), np.uint8)
    img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    
    # Code nhận diện khuôn mặt tại đây (dùng InsightFace)
    
    return {"message": "Face recognized", "confidence": 0.95}
