from .face_recognition import face_bp

def register_routes(app):
    app.register_blueprint(face_bp, url_prefix="/api/face")
