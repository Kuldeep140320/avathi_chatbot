from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks import get_openai_callback
from app.chains.sequential_chain import sequential_chain,context_analyzer_chain ,ui_analyzer_chain,first_prompt_chain
from app.utils.helpers import get_default_destination, retrieve_and_filter_documents
from app.utils.vector_store import retriever
import logging
from datetime import datetime, date,timedelta
from .booking_manager import BookingManager
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json
from fuzzywuzzy import fuzz
import sys
from app.routes.api import APIUtils
class TravelAssistant:
    def __init__(self):
        self.booking_manager = BookingManager()
        self.last_activity = {}
        self.conversations ={}
        self.ui_analyzer_chain = ui_analyzer_chain
        self.first_prompt_chain=first_prompt_chain
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
            # print("\ncurrent booking state:\n",current_booking_state,"\nbooking state end\n")
            # print("\relevant_experiences:\n",relevant_experiences,"\relevant_experiences end\n")
            print(relevant_info)
            print('shdfsjdf')
            conversation =self.get_or_create_conversation(user_id)
            chat_history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in conversation])
            first_prompt_chain = first_prompt_chain.run(
                query=query, 
                relevant_info=relevant_info,
                booking_state='initial',
                is_destination_selected=False 
            )
            print(first_prompt_chain)
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

    def generate_query_response(self, query, user_id):
        try:
            conversation = self.get_or_create_conversation(user_id)
            conversation.append(HumanMessage(content=query))
            print("\nchat_history\n", conversation, "\n\nend\nuserid\n")
            print("\nuser id\n", user_id, "\nuser id end")
            context_analysis = context_analyzer_chain.run(
                query=query, 
                chat_history=str(conversation),
                booking_state=self.booking_manager.get_current_state(),
                default_destinations=self.default_destinations 
            )
            print("\nallcontext_analysis:\n", context_analysis, "\n\nend\n")
            relevant_info, documents = retrieve_and_filter_documents(query, context_analysis)
            relevant_experiences = {}
            for doc in documents:
                primary_key = doc.metadata.get('eoexperience_primary_key')
                eoexperience_name = doc.metadata.get('eoexperience_name', 'Unknown')
                relevant_experiences[primary_key] = eoexperience_name
                
            # response, updated_context_analysis, new_state, topic_changed = self.generate_response(query, relevant_info, user_id)
            response = first_prompt_chain.run(
                query=query, 
                relevant_info=relevant_info,
                booking_state='initial',
                is_destination_selected=False 
            )
            ui_analysis = self.ui_analyzer_chain.run(
                response=response,
                context_analysis=context_analysis,
                booking_state='initial',
            )
            print(relevant_experiences)
            print("\nui_analysis:\n", ui_analysis.dict(), "\nui_analysis\n")
            return {
                'result': response,
                'ui_analysis': ui_analysis.dict(),
                'relevant_experiences':relevant_experiences
            }
        except Exception as e:
            logging.error(f"Error in generate_query_response: {e}")
            return {
                'result': "An error occurred while processing your request.",
                'source_documents': [],
                'current_booking_state': self.booking_manager.get_current_state()
            }

    def run(self, input_data, user_id):
        try:
            query = input_data.get('query', '')
            options = input_data.get('options', {})
            selected_options = input_data.get('selected_options', {})
            is_confirmed = input_data.get('is_confirmed', False)
            print(query)
            self.get_or_create_conversation(user_id).append(HumanMessage(content=query))
            
            new_state = self.booking_manager.get_current_state()
            selected_option = selected_options.get('option')
            is_selected = selected_options.get('is_selected', False)
            
            if not is_confirmed and not is_selected:
                print('hii')
                print(selected_option ,query ,options)
                selected_option = next((exp_name for exp_name in options.values()
                                        if fuzz.partial_ratio(query.lower(), exp_name.lower()) >= 80), None)
                            
                print('hii')
                print(selected_option)
                
                if selected_option:
                    new_state = 'dates'
                    return {
                        'guest_data': f"Great! You've selected {selected_option}. When would you like to check in and check out?",
                        'ui_analysis': {
                            "date_picker": True,
                            "guest_info_form": False,
                            "login_popup": False,
                            "options_list": False,
                            "payment_link": False
                        },
                        'booking_state': new_state,
                        'selected_option': selected_option,
                        'is_conformed':True
                    }
                return self.generate_query_response(query, user_id)
                
            
            dates = input_data.get('date', {})
            checkIn = dates.get('checkIn')
            checkOut = dates.get('checkOut')
            exp_id = selected_options.get('exp_id')
            
            if checkIn and checkOut and exp_id:
                price_response = APIUtils.get_price_by_date(exp_id, checkIn, checkOut)
                
                if price_response:
                    # Return the API response directly
                    # if()
                    return {
                        'guest_data': price_response,
                        'ui_analysis': {
                            "date_picker": False,
                            "guest_info_form": False,
                            "login_popup": False,
                            "options_list": True,
                            "payment_link": False
                        },
                        'booking_state': 'select_room',
                    }
                else:
                    return {
                        'result': "I'm sorry, but I couldn't retrieve the price information at this time. Would you like to try again or choose different dates?",
                        'ui_analysis': {
                            "date_picker": True,
                            "guest_info_form": False,
                            "login_popup": False,
                            "options_list": False,
                            "payment_link": False
                        },
                        'booking_state': new_state,
                    }
            
            # If we don't have all the necessary information, generate a response based on the query
            return self.generate_query_response(query, user_id)

        except Exception as e:
            logging.error(f"Error in run method: {e}")
            return {
                'result': "An error occurred while processing your request.",
                'current_booking_state': self.booking_manager.get_current_state()
            }
