from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks import get_openai_callback
from app.chains.sequential_chain import sequential_chain, context_analyzer_chain, ui_analyzer_chain, first_prompt_chain,option_prompt_chain
from app.utils.helpers import get_default_destination, retrieve_and_filter_documents
from app.utils.vector_store import retriever
from .booking_manager import BookingManager
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json
from fuzzywuzzy import fuzz
import logging
from datetime import datetime, date, timedelta

class TravelGuide:
    def __init__(self):
        self.memory = ConversationBufferWindowMemory(k=5)
        self.booking_manager = BookingManager()

    def query(self, input_data):
        try:
            query = input_data.get('query', '')
            # options = input_data.get('options', {})
            # selected_options = input_data.get('selected_options', {})
            # is_first_query = input_data.get('is_first_query', False)
            # selected_option = selected_options.get('option',)
            # is_selected = selected_options.get('is_selected', False)
            # is_second_query = input_data.get('is_second_query', False)
            print('ddd')
            print(query)
            # if is_first_query:
            #     return self.generate_query_response(query)
            # if is_second_query:
            #     return self.generate_query_options(query)
            return self.generate_query_options(query)
            selected_option_by_query = False
            
            if not is_selected:
                selected_option = next((exp_name for exp_name in options.values()
                                    if fuzz.partial_ratio(query.lower(), exp_name.lower()) >= 80), None)
                selected_option_by_query = True
            
            if selected_option_by_query:
                new_state = 'dates'
                return {
                    'guest_data': f"Great! You've selected {selected_option}. When would you like to check in and check out?",
                    'ui_analysis': {
                        "yes_no": False,
                        "date_picker": True,
                        "guest_info_form": False,
                        "login_popup": False,
                        "options_list": False,
                        "payment_link": False
                    },
                    'booking_state': new_state,
                    'selected_option': selected_option,
                }  
            
            # Process the query using the sequential chain
            with get_openai_callback() as cb:
                context = context_analyzer_chain.run(query)
                ui_analysis = ui_analyzer_chain.run(query)
                response = sequential_chain.run(query=query, context=context)
            
            self.memory.save_context({"input": query}, {"output": response})
            
            return {
                'guest_data': response,
                'ui_analysis': json.loads(ui_analysis),
                'token_usage': cb.total_tokens,
            }
        
        except Exception as e:
            logging.error(f"Error in query: {str(e)}")
            return {
                'result': "An error occurred while processing your request.",
            }

    def generate_query_response(self, query):
        try:
            # response = first_prompt_chain.run(query)
            response = first_prompt_chain.run(query=query)
            # response = first_prompt_chain.invoke({"query": query})
            print("\nresponse:",response)
            return {
                'guest_data': response,
                'ui_analysis': {
                    "yes_no": False,
                    "date_picker": False,
                    "guest_info_form": False,
                    "login_popup": False,
                    "options_list": False,
                    "payment_link": False
                },
            }
        except Exception as e:
            logging.error(f"Error generating first query response: {str(e)}")
            return {'error': "An error occurred while processing your request."}
    def generate_query_options(self, query):
        try:
            print("\ngenerate_query_options:\n")
            # context_analysis = context_analyzer_chain.run(query)
            relevant_info, documents = retrieve_and_filter_documents(query, context_analysis='')
            print("\nrelevant_info:\n",relevant_info)
            # previous_context = self.memory.load_context()
            previous_context = self._get_memory_context()
            print('\nprevious_context\n',previous_context ,'\nend\n')
            combined_input = f"{previous_context}\nUser: {query}"

            response = option_prompt_chain.run(
                    query=combined_input, 
                    options=documents,
                )
            self.memory.save_context({"input": query}, {"output": response})
            
            if not documents:
                return {
                    'guest_data': "I'm sorry, but I don't have any specific information about that. Could you please provide more details about your travel preferences or ask about a different destination?",
                    'ui_analysis': {
                        "yes_no": False,
                        "date_picker": False,
                        "guest_info_form": False,
                        "login_popup": False,
                        "options_list": False,
                        "payment_link": False
                    },
                }

            relevant_experiences = {}
            for doc in documents:
                primary_key = doc.metadata.get('eoexperience_primary_key')
                eoexperience_name = doc.metadata.get('eoexperience_name', 'Unknown')
                relevant_experiences[primary_key] = eoexperience_name
            self.memory.save_context({"input": query}, {"output": response})

            return {
                'ai': response,
                'ui_analysis': {
                    "options_list": True,
                    "guest_list":False,
                    "options":relevant_experiences,
                },
            }
        
        except Exception as e:
            logging.error(f"Error generating query options: {str(e)}")
            return {
                'guest_data': "I apologize, but I'm having trouble finding relevant information. Could you please rephrase your query or ask about a different aspect of your travel plans?",
                'ui_analysis': {
                    "yes_no": False,
                    "date_picker": False,
                    "guest_info_form": False,
                    "login_popup": False,
                    "options_list": False,
                    "payment_link": False
                },
            }
    def get_price_by_date(self, exp_id, check_in, check_out):
        price_response = self.booking_manager.get_price_by_date(exp_id, check_in, check_out)
        return price_response
    def _get_memory_context(self):
        context = ""
        for message in self.memory.chat_memory.messages:
            role = "User" if isinstance(message, HumanMessage) else "AI"
            context += f"{role}: {message.content}\n"
        return context
    def run(self, input_data, user_id):
        is_date_selected = input_data.get('is_date_selected', False)
        if not is_date_selected:
            return self.query(input_data)
    
        selected_options = input_data.get('selected_options', {})
        exp_id = selected_options.get('exp_id', False)
        dates = input_data.get('date', {})
        check_in = dates.get('checkIn')
        check_out = dates.get('checkOut')
        if check_in and check_out and exp_id:
            return self.get_price_by_date(exp_id, check_in, check_out)
        
        return {'error': "Insufficient information provided."}