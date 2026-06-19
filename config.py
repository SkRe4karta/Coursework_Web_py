import os
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-for-peregovorki-987654')
    
    # Database URL configuration with SQLite fallback
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'peregovorki.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folders configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'app', 'uploads'))
    # Max file size limit: default is 16MB
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'png', 'jpg', 'jpeg', 'zip'}
