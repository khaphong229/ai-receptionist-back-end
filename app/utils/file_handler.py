import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

def ensure_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def save_file(file, folder):
    """
    Lưu file và trả về đường dẫn tương đối
    """
    ensure_folder_exists(folder)
    # Tạo tên file unique với timestamp
    filename = secure_filename(file.filename)
    extension = os.path.splitext(filename)[1]
    new_filename = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}{extension}"
    file_path = os.path.join(folder, new_filename)
    file.save(file_path)
    return file_path