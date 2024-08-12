from flask import Blueprint, request, jsonify, session
from uuid import uuid4
from app.chatbot.travel_assistant import TravelAssistant

chat_bp = Blueprint('chat', __name__)
travel_assistant = TravelAssistant()

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
        result = travel_assistant.run(query, user_id)
        return jsonify({
            "ai": result['result'],
            "ui_analysis": result['ui_analysis'],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
