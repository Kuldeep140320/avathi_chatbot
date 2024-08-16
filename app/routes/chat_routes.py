from flask import Blueprint, request, jsonify, session
from uuid import uuid4
from app.chatbot.travel_assistant import TravelAssistant
from app.chatbot.travel import TravelGuide
chat_bp = Blueprint('chat', __name__)
# travel_assistant = TravelAssistant()
travel_assistant = TravelGuide()

@chat_bp.route('/query', methods=['POST'])
def process_query():
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({"error": "No query provided in the data field"}), 400
    
    if 'user_id' not in session:
        session['user_id'] = str(uuid4())
        
    user_id = session['user_id']

    try:
        result = travel_assistant.run(data, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    