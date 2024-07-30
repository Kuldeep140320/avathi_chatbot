from flask import Flask
from app.routes.recommendations import recommendations_bp
from app.models import db
from app.config import Config

def create_app():
    print('ds')
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    app.register_blueprint(recommendations_bp)
    return app
