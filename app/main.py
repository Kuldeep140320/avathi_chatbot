
from flask import Flask
from flask_session import Session
from flask_cors import CORS
from dotenv import load_dotenv
import os ,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from app.routes.chat_routes import chat_bp, travel_assistant

load_dotenv()

def create_app():
    app = Flask(__name__)
    # CORS(app)
    # CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'fallback_secret_key')
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)

    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    # scheduler = BackgroundScheduler()
    # scheduler.add_job(func=travel_assistant.cleanup_old_conversations, trigger="interval", minutes=1)
    # scheduler.start()

    return app
app = create_app()
if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=8080)
# from flask import Flask, request, jsonify,session
# from flask_session import Session
# from uuid import uuid4
# from datetime import datetime, date,timedelta
# from dotenv import load_dotenv
# import os
# import sys
# from flask_cors import CORS  # Add this import
# from apscheduler.schedulers.background import BackgroundScheduler

# # Ensure the correct path for imports
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from app.chatbot.travel_assistant import TravelAssistant
# from app.config import VECTOR_DB_PATH, EMBEDDING_MODEL

# # Load environment variables
# load_dotenv()

# # Vector store initialization
# from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings

# def initialize_vector_store():
#     print(VECTOR_DB_PATH, EMBEDDING_MODEL)
#     instruct_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
#     vector_db = FAISS.load_local(VECTOR_DB_PATH, instruct_embeddings, allow_dangerous_deserialization=True)
#     return vector_db

# vector_db = initialize_vector_store()
# retriever = vector_db.as_retriever(search_kwargs={"k": 5})

# app = Flask(__name__)
# CORS(app)
# app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'fallback_secret_key')
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)
# # CORS(app, resources={r"/query": {"origins": "http://localhost:3000"}})

# # Initialize TravelAssistant
# travel_assistant = TravelAssistant()
# scheduler =BackgroundScheduler()
# scheduler.add_job(func=travel_assistant.cleanup_old_conversations,trigger="interval", minutes=5)
# scheduler.start()

# @app.route('/query', methods=['POST'])
# def process_query():
#     data = request.json
#     query = data.get('query')

#     if not query:
#         return jsonify({"error": "No query provided in the data field"}), 400
#     if 'user_id' not in session:
#         session['user_id'] = str(uuid4())
        
#     user_id = session['user_id']

#     try:
#         result = travel_assistant.run(query,user_id)
#         return jsonify({"AI": result['result']})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     # app.run(debug=True)
#     app.run(debug=True, host='0.0.0.0', port=8080)