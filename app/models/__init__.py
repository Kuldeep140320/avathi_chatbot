from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object
db = SQLAlchemy()

# Import all models here to ensure they are registered with SQLAlchemy
from app.models.experience_model import Experience
