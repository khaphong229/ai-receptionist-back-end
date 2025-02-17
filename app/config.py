import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/ai_receptionist")

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    FACE_FOLDER = os.getenv("UPLOAD_FOLDER", "faces")
    ID_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads/ids")

    # Thay đổi cấu hình Chatbot
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-key")
    OPENAI_MODEL = "gpt-3.5-turbo"  # Model rẻ nhất, phù hợp nhất
    
    # Cấu hình cho Local LLM (GPT4All)
    GPT4ALL_MODEL = "orca-mini-3b-gguf2-q4_0.gguf"  # Smaller, faster model
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "orca-mini-3b-gguf2-q4_0.gguf")
    
    # Thư mục chứa vector store và dữ liệu training
    VECTOR_STORE_PATH = "app/data/vector_store"
    KNOWLEDGE_DIR = "app/data/knowledge"

    # Thêm cấu hình cho OCR
    OCR_LANG = 'vi'  # Ngôn ngữ OCR