from flask import Blueprint, request, jsonify, session,current_app
from uuid import uuid4
from app.chatbot.travel_assistant import TravelAssistant
from app.chatbot.travel import TravelGuide
from app.chatbot.newtravel import booking_chat
chat_bp = Blueprint('chat', __name__)
# travel_assistant = TravelAssistant()
from datetime import timedelta
from app.routes.api import APIUtils

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
    query = data.get('query',"")
    chat_history=data.get('chat_history',{})
    # chat_history['chat_history']=data.get('conversation_history',{})
    # try:
    result, new_chat_state ,conversation_history= booking_chat(query, chat_history)
    response = {
        'ai': result,
        'chat_history': new_chat_state,
        # "conversation_history":conversation_history
    }
    return jsonify(response)
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500
    
@chat_bp.route('/payment_token', methods=['POST'])
def payment_token():
    try:
        token = APIUtils.get_payment_token()
       
        return jsonify(token['access_token'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500