from flask import request, jsonify, session, current_app
from uuid import uuid4
import time
from app.chatbot.travel import TravelGuide
from app.chatbot.newtravel import booking_chat
from app.routes.api import APIUtils

class ChatBot:
    def __init__(self):
        self.travel_assistant = TravelGuide()

    def init_session(self):
        if 'user_id' not in session:
            session['user_id'] = str(uuid4())
        if 'chats' not in session:
            session['chats'] = {}

    def process_query2(self):
        data = request.json
        query = data.get('query')
        chat_id = data.get('chat_id')
        clear_session = data.get('clear_session', False)
        history = data.get('history')
        current_app.logger.info(f"Session at start: {dict(session)}")

        if clear_session:
            if chat_id and chat_id in session['chats']:
                del session['chats'][chat_id]
            else:
                session['chats'] = {}
            return jsonify({"message": "Chat cleared"}), 200

        if not chat_id:
            return jsonify({"error": "No chat_id provided"}), 400

        chat_state = session['chats'].get(chat_id, {})
        last_activity = chat_state.get('last_activity', 0)

        current_app.logger.info(f"Retrieved chat_state for chat_id {chat_id}: {chat_state}")

        if time.time() - last_activity > 300:
            chat_state = {}
            current_app.logger.info(f"Chat state cleared for chat_id {chat_id} due to inactivity")

        try:
            result, new_chat_state = booking_chat(query, history)

            current_app.logger.info(f"Before update - Session for chat_id {chat_id}: {chat_state}")
            new_chat_state['last_activity'] = time.time()
            session['chats'][chat_id] = new_chat_state
            current_app.logger.info(f"After update - Session for chat_id {chat_id}: {new_chat_state}")

            response = {
                'ai': result,
                'chat_state': new_chat_state
            }
            return jsonify(response)
        except Exception as e:
            current_app.logger.error(f"Error in process_query2 for chat_id {chat_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def check_session(self):
        current_app.logger.info(f"Current session: {dict(session)}")
        return jsonify(dict(session))

    def generate_chatid(self):
        chat_id = str(uuid4())
        session['chats'][chat_id] = {'last_activity': time.time()}
        return jsonify({"chat_id": chat_id})

    def check_route(self):
        token = APIUtils.get_payment_token()
        return jsonify(dict(token))

def register_routes(app):
    chatbot = ChatBot()

    @app.before_request
    def before_request():
        chatbot.init_session()

    @app.route('/api/chat/query', methods=['POST'])
    def query():
        return chatbot.process_query()

    @app.route('/api/chat/query2', methods=['POST'])
    def query2():
        return chatbot.process_query2()

    @app.route('/api/chat/check_session', methods=['GET'])
    def check_session():
        return chatbot.check_session()

    @app.route('/api/chat/check_route', methods=['POST'])
    def check_route():
        return chatbot.check_route()

    @app.route('/api/chat/generate_chatid', methods=['POST'])
    def generate_chatid():
        return chatbot.generate_chatid()