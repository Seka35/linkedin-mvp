import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LinkedIn
    LINKEDIN_EMAIL = os.environ.get("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD")
    
    # Apify
    APIFY_API_KEY = os.environ.get("APIFY_API_KEY")
    
    # Database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'data', 'prospects.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or 'dev-key-please-change'
