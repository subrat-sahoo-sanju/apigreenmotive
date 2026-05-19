import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'green-motive-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///students.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    FACE_TOLERANCE = 0.6
    DETECTION_THRESHOLD = 0.5
