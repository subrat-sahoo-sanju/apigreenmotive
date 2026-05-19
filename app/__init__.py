from flask import Flask
from flask_cors import CORS
from .config import Config
from .models import db
from .routes import api
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app)
    
    db.init_app(app)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    
    app.register_blueprint(api, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
    
    return app
