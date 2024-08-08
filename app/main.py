from flask import Flask, request, jsonify
from datetime import datetime, date
from dotenv import load_dotenv
import os
import sys

# Ensure the correct path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chatbot.travel_assistant import TravelAssistant

# Load environment variables
load_dotenv()

# Vector store initialization
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import VECTOR_DB_PATH, EMBEDDING_MODEL

def initialize_vector_store():
    print(VECTOR_DB_PATH, EMBEDDING_MODEL)
    instruct_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_db = FAISS.load_local(VECTOR_DB_PATH, instruct_embeddings, allow_dangerous_deserialization=True)
    return vector_db

vector_db = initialize_vector_store()
retriever = vector_db.as_retriever(search_kwargs={"k": 5})

app = Flask(__name__)

# Initialize TravelAssistant
travel_assistant = TravelAssistant()

@app.route('/query', methods=['POST'])
def process_query():
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({"error": "No query provided in the data field"}), 400

    try:
        result = travel_assistant.run(query)
        return jsonify({"AI": result['result']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)