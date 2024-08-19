import openai
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from datetime import datetime
import re
from fuzzywuzzy import fuzz
import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json

# Assume these are imported from your existing codebase
from app.utils.vector_store import retriever
from app.routes.api import APIUtils

# Replace with your actual OpenAI API key
openai.api_key = "your-openai-api-key"

class BookingRequest:
    def __init__(self, chat_history, llm):
        self.chat_history = chat_history
        self.llm = llm
        self.experience_id = None
        self.experience_name = None
        self.check_in = None
        self.check_out = None
        self.is_ready = False
        self.possible_experiences = None

    def get_chat_history(self):
        return self.chat_history

    def get_most_recent_message(self):
        return self.chat_history.messages[-1].content

    def get_booking_state(self):
        return {
            "experience_id": self.experience_id,
            "experience_name": self.experience_name,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "is_ready": self.is_ready,
            "possible_experiences": self.possible_experiences
        }

def convert_chat_history_to_messages(chat_history):
    messages = []
    for message in chat_history.messages:
        if isinstance(message, HumanMessage):
            messages.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            messages.append({"role": "assistant", "content": message.content})
        elif isinstance(message, SystemMessage):
            messages.append({"role": "system", "content": message.content})
    return messages

def initialize_chat():
    chat_history = ChatMessageHistory()
    llm = openai.OpenAI()

    system_message = """
    You are an AI chatbot assisting users in booking travel experiences (rooms). Your tasks are to:
    1. Get the experience (room) the user wants to book.
    2. Confirm the check-in and check-out dates.
    3. Help the user make decisions and provide information about available options.

    Use the provided functions to update the booking information and retrieve necessary data.
    Do not generate any bookings or confirmations yourself. Your role is to collect information and assist the user.
    """
    chat_history.add_message(SystemMessage(content=system_message))

    ai_message = "Welcome! What kind of travel experience or room are you looking to book today?"
    chat_history.add_message(AIMessage(content=ai_message))
    print('\nini chat_history : ' ,chat_history)
    return BookingRequest(chat_history, llm)

def run_booking_assistant(user_input, chat_history=None):
    if not chat_history:
        chatbot = initialize_chat()
    else:
        llm = openai.OpenAI()
        chatbot = BookingRequest(chat_history, llm)
    
    chatbot.chat_history.add_user_message(user_input)
    print('\nconvert chat history :',convert_chat_history_to_messages(chatbot.chat_history))
    if chatbot.possible_experiences:
        selected_experience = None
        try:
            # Check if user input is a number
            selection = int(user_input) - 1
            if 0 <= selection < len(chatbot.possible_experiences):
                selected_experience = chatbot.possible_experiences[selection]
        except ValueError:
            # If not a number, try to match by name
            for exp in chatbot.possible_experiences:
                if fuzz.ratio(user_input.lower(), exp['name'].lower()) > 80:
                    selected_experience = exp
                    break
        
        if selected_experience:
            chatbot.experience_id = selected_experience['id']
            chatbot.experience_name = selected_experience['name']
            chatbot.possible_experiences = None
            chatbot.chat_history.add_ai_message(f"Great! You've selected {chatbot.experience_name}. When would you like to check in and check out?")
            return chatbot.get_most_recent_message(), chatbot.get_booking_state()

    ai_response = chatbot.llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=convert_chat_history_to_messages(chatbot.chat_history),
        functions=functions,
        function_call="auto"
    )
    print('\nai_response :' ,ai_response)

    if ai_response.choices[0].message.content:
        chatbot.chat_history.add_ai_message(ai_response.choices[0].message.content)
    elif ai_response.choices[0].message.function_call:
        function_call = ai_response.choices[0].message.function_call
        function_name = function_call.name
        # arguments = function_call.arguments
        arguments = json.loads(function_call.arguments)

        if function_name == "set_experience":
            set_experience(chatbot, arguments)
        elif function_name == "set_dates":
            set_dates(chatbot, arguments)
        elif function_name == "get_price":
            get_price(chatbot)
        elif function_name == "confirm_booking":
            confirm_booking(chatbot)

        next_ai_message(chatbot)

    return chatbot.get_most_recent_message(), chatbot.get_booking_state()

def set_experience(chatbot, arguments):
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    experience_name = arguments.get("experience_name")
    print('\n exp_name :' ,experience_name)
    possible_experiences = search_experiences(experience_name)
    print('\npossible_experiences :' ,possible_experiences)
    
    if len(possible_experiences) == 1:
        chatbot.experience_id = possible_experiences[0]["id"]
        chatbot.experience_name = possible_experiences[0]["name"]
        chatbot.chat_history.add_ai_message(f"Great! I've found the experience: {chatbot.experience_name}. When would you like to check in and check out?")
    elif len(possible_experiences) > 1:
        chatbot.possible_experiences = possible_experiences
        options = "\n".join([f"{i+1}. {exp['name']}" for i, exp in enumerate(possible_experiences)])
        chatbot.chat_history.add_ai_message(f"I found multiple options matching your request:\n{options}\nWhich one would you like to book? You can reply with the number or the name of the experience.")
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, I couldn't find any experiences matching your request. Could you please try a different search term?")

def set_dates(chatbot, arguments):
    check_in = arguments.get("check_in")
    check_out = arguments.get("check_out")

    if validate_dates(check_in, check_out):
        chatbot.check_in = check_in
        chatbot.check_out = check_out
        chatbot.chat_history.add_ai_message(f"Thank you. I've set your check-in date to {check_in} and check-out date to {check_out}. Would you like me to check the price for these dates?")
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, but the dates you provided are not valid. Please make sure the check-in date is before the check-out date and both are in the future. Could you please provide the dates again?")

def get_price(chatbot):
    if chatbot.experience_id and chatbot.check_in and chatbot.check_out:
        price_response = APIUtils.get_price_by_date(chatbot.experience_id, chatbot.check_in, chatbot.check_out)
        if price_response.get("success"):
            price = price_response.get("total_price")
            chatbot.chat_history.add_ai_message(f"The total price for your stay from {chatbot.check_in} to {chatbot.check_out} is ${price}. Would you like to confirm this booking?")
        else:
            chatbot.chat_history.add_ai_message("I'm sorry, but I couldn't retrieve the price for these dates. Would you like to try different dates?")
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, but I don't have all the necessary information to get the price. Could you please make sure you've selected an experience and provided check-in and check-out dates?")

def confirm_booking(chatbot):
    if chatbot.experience_id and chatbot.check_in and chatbot.check_out:
        chatbot.is_ready = True
        chatbot.chat_history.add_ai_message("Great! Your booking is confirmed. Is there anything else I can help you with?")
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, but I don't have all the necessary information to confirm the booking. Could you please make sure you've selected an experience and provided check-in and check-out dates?")

def next_ai_message(chatbot):
    if chatbot.possible_experiences:
        options = "\n".join([f"{i+1}. {exp['name']}" for i, exp in enumerate(chatbot.possible_experiences)])
        chatbot.chat_history.add_ai_message(f"I found these options matching your request:\n{options}\nWhich one would you like to book? You can reply with the number or the name of the experience.")
    elif not chatbot.experience_id:
        chatbot.chat_history.add_ai_message("What kind of experience or room are you looking for?")
    elif not chatbot.check_in or not chatbot.check_out:
        chatbot.chat_history.add_ai_message("When would you like to check in and check out?")
    elif not chatbot.is_ready:
        chatbot.chat_history.add_ai_message("Would you like me to check the price for these dates?")
def search_experiences(query):
    print('query' ,query)
    # This function should use your existing search functionality
    # For now, we'll use a dummy implementation
    results = retriever.get_relevant_documents(query)
    return [{"id": doc.metadata["eoexperience_primary_key"], "name": doc.metadata["eoexperience_name"]} for doc in results]

def validate_dates(check_in, check_out):
    try:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        today = datetime.now()
        return check_in_date < check_out_date and check_in_date >= today
    except ValueError:
        return False

functions = [
    {
        "name": "set_experience",
        "description": "Set the experience or room the user wants to book",
        "parameters": {
            "type": "object",
            "properties": {
                "experience_name": {
                    "type": "string",
                    "description": "The name of the experience or room"
                }
            },
            "required": ["experience_name"]
        }
    },
    {
        "name": "set_dates",
        "description": "Set the check-in and check-out dates for the booking",
        "parameters": {
            "type": "object",
            "properties": {
                "check_in": {
                    "type": "string",
                    "description": "The check-in date in YYYY-MM-DD format"
                },
                "check_out": {
                    "type": "string",
                    "description": "The check-out date in YYYY-MM-DD format"
                }
            },
            "required": ["check_in", "check_out"]
        }
    },
    {
        "name": "get_price",
        "description": "Get the price for the selected experience and dates"
    },
    {
        "name": "confirm_booking",
        "description": "Confirm the booking with the selected experience and dates"
    }
]

# Example usage
if __name__ == "__main__":
    chat_history = None
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        response, booking_state = run_booking_assistant(user_input, chat_history)
        print("AI:", response)
        print("Booking State:", booking_state)
        chat_history = ChatMessageHistory(message=response)