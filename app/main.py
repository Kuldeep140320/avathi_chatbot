from flask import Flask
from flask_session import Session
from flask_cors import CORS
from .routes.chat_routes import register_routes
import os

def create_app(config_object='app.config.DevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Ensure the session directory exists
    os.makedirs(app.config.get('SESSION_FILE_DIR', 'flask_session'), exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    Session(app)

    register_routes(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True , host='0.0.0.0', port=8080)