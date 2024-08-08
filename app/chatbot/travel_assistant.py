from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks import get_openai_callback
from app.chains.sequential_chain import sequential_chain,context_analyzer_chain
from app.utils.helpers import get_default_destination, retrieve_and_filter_documents
from app.utils.vector_store import retriever
import logging
from .booking_manager import BookingManager
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
class TravelAssistant:
    def __init__(self):
        # print('hii')
        self.booking_manager = BookingManager()
        self.chat_history = ChatMessageHistory()

        # self.memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history", input_key="input")
        self.memory = ConversationBufferWindowMemory(k=5,chat_memory=self.chat_history, input_key="input", output_key="output", return_messages=True)
        self.current_booking_state = self.booking_manager.get_current_state()
        self.default_destinations = get_default_destination()
        self.chat_history.add_message(SystemMessage(content="You are a helpful travel assistant. Your goal is to help users plan their trips and make bookings."))

    def generate_response(self, query, relevant_info):
        try:
            current_booking_state = self.booking_manager.get_current_state()
            chat_history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in self.chat_history.messages])

            with get_openai_callback() as cb:
                response = sequential_chain({
                    "query": query,
                    "chat_history": chat_history_str,
                    "relevant_info": relevant_info,
                    "booking_state": current_booking_state,
                    "default_destinations": get_default_destination()
                })
            
            # print(f"\nContext Analysis:\n {response['context_analysis']}")
            # print(f"\nClassification: {response['classification']}")
            # print(f"Total Tokens: {cb.total_tokens}")
            # print(f"Total Cost (USD): ${cb.total_cost}")
            # print('\nresponse\n',response)
            self.current_booking_state = self.update_booking_state(response['context_analysis'])
            print(f"Updated Booking State: {self.current_booking_state}")
            self.chat_history.add_message(AIMessage(content=response['response']))

            return response['response'], response['context_analysis']
        except Exception as e:
            logging.error(f"Error in generate_response: {e}")
            return "An error occurred while generating the response.", ""

    def update_booking_state(self, context_analysis):
        # Extract the suggested booking state from context_analysis
        suggested_state = context_analysis.split("Suggested Booking State:")[-1].strip().split("\n")[0]
        return suggested_state if suggested_state in self.booking_manager.STATES else self.booking_manager.get_current_state()

    def generate_query_response(self, query):
        print('\ngenerate_query_response:',query )
        try:
            self.chat_history.add_message(HumanMessage(content=query))

            # chat_history = self.memory.load_memory_variables({})["chat_history"]
            # print("\nchat_history\n",chat_history)
            context_analysis = context_analyzer_chain.run(
                query=query, 
                chat_history=str(self.chat_history.messages),
                booking_state=self.booking_manager.get_current_state(),
                default_destinations=get_default_destination()
            )
            print("\nallcontext_analysis:" ,context_analysis)
            relevant_info, documents = retrieve_and_filter_documents(query, context_analysis)
            # print("context_analysis:\n" ,context_analysis)
            response, updated_context_analysis = self.generate_response(query, relevant_info)
            
            # self.memory.save_context({"input": query}, {"output": response})
            
            return {
                'result': response,
                'source_documents': documents,
                'context': relevant_info,
                'context_analysis': updated_context_analysis,
                'current_booking_state': self.booking_manager.get_current_state()
            }
        except Exception as e:
            logging.error(f"Error in generate_query_response: {e}")
            return {
                'result': "An error occurred while processing your request.",
                'source_documents': [],
                'current_booking_state': self.booking_manager.get_current_state()
            }

    def run(self , query: str = None):
        print("Starting the Travel Assistant Chatbot...")
        # print("\nquery:\n",query,"\nquery\n")
        # print(f"Default destinations: {self.default_destinations}")
        response = self.generate_query_response(query)
        return response
    # def get_chat_history(self):
    #     return self.chat_history.messages