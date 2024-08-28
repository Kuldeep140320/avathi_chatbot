import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "vector_store_new_10")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")



class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'dbname')
    DB_USER = os.getenv('DB_USER', 'user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'your_fallback_secret_key_here')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

# Table Configuration
TABLES_CONFIG = {
    # 'processed_guideData_overView': ['id',
    #     'Location_id', 'introduction','best_time_to_visit','status','overview_title','updated_how_to_get_to'
    # ],
        'eoexperience': ['primary_key, name, description, location, pin_code, is_stay, price, latitude, longitude, display_priority'
    ],

    # Add other tables and their fields here
}


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False