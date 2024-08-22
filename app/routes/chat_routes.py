from flask import Blueprint, request, jsonify, session,current_app
from uuid import uuid4
from app.chatbot.travel_assistant import TravelAssistant
from app.chatbot.travel import TravelGuide
from app.chatbot.newtravel import booking_chat
chat_bp = Blueprint('chat', __name__)
# travel_assistant = TravelAssistant()
from datetime import timedelta

travel_assistant = TravelGuide()
import time
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
    
    
@chat_bp.route('/query2', methods=['POST'])
def process_query2():
    data = request.json
    query = data.get('query')
    clear_session=data.get('clear_session',False)
    if clear_session:
        session.clear()
        return jsonify({"message": "Session cleared"}), 200
    # Get the chat state from the session, or initialize a new one
    chat_state = session.get('chat_state', None)
    last_activity=session.get('last_activity',0)
    if time.time()-last_activity >300:
        session.clear()
        chat_state=None
    try:
        result, new_chat_state = booking_chat(query, chat_state)
        
        # Save the new chat state in the session
        session['chat_state'] = new_chat_state
        session['last_activity']=time.time()
        session.permanent=True
        current_app.permanent_session_lifetime = timedelta(minutes=2)
        response = {
            'ai': result,
            'chat_state': new_chat_state
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500