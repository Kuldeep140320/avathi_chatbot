from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks import get_openai_callback
from app.chains.sequential_chain import sequential_chain,context_analyzer_chain
from app.utils.helpers import get_default_destination, retrieve_and_filter_documents
from app.utils.vector_store import retriever
import logging
from datetime import datetime, date,timedelta
from .booking_manager import BookingManager
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
class TravelAssistant:
    def __init__(self):
        self.booking_manager = BookingManager()
        self.last_activity = {}
        self.conversations ={}
        # self.booking_info = {}
        # self.memory = ConversationBufferWindowMemory(k=5,chat_memory=self.chat_history, input_key="input", output_key="output", return_messages=True)
        self.default_destinations = get_default_destination()
    def get_or_create_conversation(self, user_id):
            if user_id not in self.conversations:
                self.conversations[user_id] = [
                    SystemMessage(content="You are a helpful travel assistant. Your goal is to help users plan their trips and make bookings.")
                ]
            # self.booking_info[user_id]={}
            self.last_activity[user_id] = datetime.now()
            return self.conversations[user_id]
    def generate_response(self, query, relevant_info,user_id):
        try:
            current_booking_state = self.booking_manager.get_current_state()
            print("\ncurrent booking state:\n",current_booking_state,"\nbooking state end\n")
            conversation =self.get_or_create_conversation(user_id)
            chat_history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in conversation])
            with get_openai_callback() as cb:
                response = sequential_chain({
                    "query": query,
                    "chat_history": chat_history_str,
                    "relevant_info": relevant_info,
                    "booking_state": current_booking_state,
                    # "default_destinations": self.default_destinations 
                })
            print('\ncontext_analysis\n' ,response['context_analysis'] ,'\nend')
            suggested_state = response['context_analysis'].split("Suggested Booking State:")[-1].strip().split("\n")[0]
            
            new_state, topic_changed = self.booking_manager.update_booking_state(suggested_state, query, response['context_analysis'])

            # new_state, topic_changed = self.update_booking_state(response['context_analysis'], query, user_id)
            conversation.append(AIMessage(content=response['response']))
            return response['response'], response['context_analysis'],new_state,topic_changed 
        except Exception as e:
            logging.error(f"Error in generate_response: {e}")
            return "An error occurred while generating the response.", "", current_booking_state

    # def update_booking_state(self, context_analysis):
    #     # Extract the suggested booking state from context_analysis
    #     print("\nsuggested booking state from context_analysis\n",context_analysis ,'\nhii\n')
    #     suggested_state = context_analysis.split("Suggested Booking State:")[-1].strip().split("\n")[0]
    #     print("\nsuggested_state:",suggested_state ,"\nend")
    #     if suggested_state in self.booking_manager.STATES:
    #         self.booking_manager.set_state(suggested_state)
    #         return suggested_state
    #     return self.booking_manager.get_current_state()

    def generate_query_response(self, query ,user_id):
        try:
            conversation=self.get_or_create_conversation(user_id)
            conversation.append(HumanMessage(content=query))
            print("\nchat_history\n",conversation ,"\n\nend\nuserid\n")
            print("\nuser id\n",user_id,"\nuser id end")
            context_analysis = context_analyzer_chain.run(
                query=query, 
                chat_history=str(conversation),
                booking_state=self.booking_manager.get_current_state(),
                default_destinations=self.default_destinations 
            )
            print("\nallcontext_analysis:\n" ,context_analysis  ,"\n\nend\n")
            relevant_info, documents = retrieve_and_filter_documents(query, context_analysis)
            response, updated_context_analysis ,new_state ,topic_changed = self.generate_response(query, relevant_info,user_id)
            return {
                'result': response,
                'source_documents': documents,
                'context': relevant_info,
                'context_analysis': updated_context_analysis,
                'current_booking_state': new_state 
            }
        except Exception as e:
            logging.error(f"Error in generate_query_response: {e}")
            return {
                'result': "An error occurred while processing your request.",
                'source_documents': [],
                'current_booking_state': self.booking_manager.get_current_state()
            }
    def cleanup_old_conversations(self ,max_age_minutes=2):
        #  max_age_hours=1
        current_time = datetime.now()
        for user_id, last_activity in list(self.last_activity.items()):
            if (current_time - last_activity) > timedelta(hours=max_age_minutes):
                del self.conversations[user_id]
                del self.last_activity[user_id]
    def run(self , query,user_id):
        print("Starting the Travel Assistant Chatbot...")
        response = self.generate_query_response(query,user_id)
        return response