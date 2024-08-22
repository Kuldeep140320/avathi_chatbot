from flask import request, jsonify, session, current_app
from uuid import uuid4
import time
from app.chatbot.travel import TravelGuide
from app.chatbot.newtravel import booking_chat

class ChatBot:
    def __init__(self):
        self.travel_assistant = TravelGuide()

    def init_session(self):
        if 'user_id' not in session:
            session['user_id'] = str(uuid4())
        if 'chat_state' not in session:
            session['chat_state'] = None
        if 'last_activity' not in session:
            session['last_activity'] = time.time()

    def process_query(self):
        data = request.json
        query = data.get('query')

        if not query:
            return jsonify({"error": "No query provided in the data field"}), 400
        
        user_id = session['user_id']

        try:
            result = self.travel_assistant.run(data, user_id)
            return jsonify(result)
        except Exception as e:
            current_app.logger.error(f"Error in process_query: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def process_query2(self):
        data = request.json
        query = data.get('query')
        clear_session = data.get('clear_session', False)

        current_app.logger.info(f"Session at start: {dict(session)}")

        if clear_session:
            session.clear()
            session['user_id'] = str(uuid4())
            return jsonify({"message": "Session cleared"}), 200

        chat_state = session.get('chat_state')
        last_activity = session.get('last_activity', 0)

        current_app.logger.info(f"Retrieved chat_state: {chat_state}")
        current_app.logger.info(f"Retrieved last_activity: {last_activity}")

        if time.time() - last_activity > 300:
            session.clear()
            session['user_id'] = str(uuid4())
            chat_state = None
            current_app.logger.info("Session cleared due to inactivity")

        try:
            result, new_chat_state = booking_chat(query, chat_state)
            
            current_app.logger.info(f"Before update - Session: {dict(session)}")
            session['chat_state'] = new_chat_state
            session['last_activity'] = time.time()
            current_app.logger.info(f"After update - Session: {dict(session)}")

            response = {
                'ai': result,
                'chat_state': new_chat_state
            }
            return jsonify(response)
        except Exception as e:
            current_app.logger.error(f"Error in process_query2: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def check_session(self):
        current_app.logger.info(f"Current session: {dict(session)}")
        return jsonify(dict(session))

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
        # return('hiii')
        return chatbot.process_query2()

    @app.route('/api/chat/check_session', methods=['GET'])
    def check_session():
        return chatbot.check_session()