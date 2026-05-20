import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'green-motive-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///students.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
        'pool_timeout': 20,
        'pool_size': 5,
        'max_overflow': 10,
        'connect_args': {'connect_timeout': 10}
    }
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads'))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    FACE_TOLERANCE = 0.6
    DETECTION_THRESHOLD = 0.5
