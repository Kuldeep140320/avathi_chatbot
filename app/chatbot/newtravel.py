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
from utils.vector_store import retriever
from routes.api import APIUtils

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
        
        self.price_data = None
        self.room_options = None
        self.selected_room = None
        self.adults = None
        self.children = None
        self.payment_data = None
        
    def get_chat_history(self):
        return self.chat_history
    def update_from_dict(self, data):
        # print("\nupdate_from_dict" ,data)
        self.experience_id = data.get('experience_id')
        self.experience_name = data.get('experience_name')
        self.check_in = data.get('check_in')
        self.check_out = data.get('check_out')
        self.is_ready = data.get('is_ready', False)
        self.possible_experiences = data.get('possible_experiences')
        
        self.price_data = data.get('price_data')
        self.room_options = data.get('room_options')
        self.selected_room = data.get('selected_room')
        self.adults = data.get('adults')
        self.children = data.get('children')
        self.payment_data = data.get('payment_data')

    def get_most_recent_message(self):
        return self.chat_history.messages[-1].content

    def get_booking_state(self):
        return {
            "experience_id": self.experience_id,
            "experience_name": self.experience_name,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "is_ready": self.is_ready,
            "possible_experiences": self.possible_experiences,
            "price_data": self.price_data,
            "room_options": self.room_options,
            "selected_room": self.selected_room,
            "adults": self.adults,
            "children": self.children,
            "payment_data": self.payment_data

        }
def present_room_options(chatbot):
    room_options = []
    # print('\npresent_room_options :',chatbot.room_options)
    # print('\npresent_room_price :',chatbot.price_data)
    for room in chatbot.room_options:
        room_options.append(f"{room['ticket_name']} (INR{room['price_per_ticket_with_tax']} per night")
    
    options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(room_options)])
    # print('options_text',options_text)
    chatbot.chat_history.add_ai_message(f"Here are the available room options present_room_options:\n{options_text}\nWhich room would you like to book? You can reply with the number or the name of the room.")
    
    return options_text

def select_room_or_package(chatbot, room_selection):
    selected_room = None
    try:
        # Check if user input is a number
        selection = int(room_selection) - 1
        if 0 <= selection < len(chatbot.room_options):
            selected_room = chatbot.room_options[selection]
    except ValueError:
        # If not a number, try to match by name
        for room in chatbot.room_options:
            if fuzz.ratio(room_selection.lower(), room['ticket_name'].lower()) > 80:
                selected_room = room
                break
    
    if selected_room:
        chatbot.selected_room = selected_room
        return ask_for_occupancy(chatbot)
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, I couldn't find a room matching your selection. Could you please try again?")
        return present_room_options(chatbot)
def set_occupancy(chatbot, adults, children):
    max_occupancy = chatbot.selected_room['max_occupants_per_room']
    total_guests = adults + children
    if total_guests > max_occupancy:
        chatbot.chat_history.add_ai_message(f"I'm sorry, but the total number of guests ({total_guests}) exceeds the maximum occupancy ({max_occupancy}) for this room. Would you like to select a different room or adjust the number of guests?")
        return "Please choose to either 'select another room' or 'adjust guests'."
    chatbot.adults = adults
    chatbot.children = children
    # Prepare the payload for the get_payment_total API call
    payload = {
        "eoexperience_primary_key": chatbot.experience_id,
        "total_amount": "0",
        "eouser_primary_key": 8553,  # This seems to be a static value, consider making it dynamic if needed
        "date_of_exp": chatbot.check_in,
        "end_date": chatbot.check_out,
        "ticket_details": [
            {
                "ticket_id": chatbot.selected_room['ticket_id'],
                "max_occupants_per_room": max_occupancy,
                "guest_type": [
                    {
                        "qty": adults,
                        "price": next(guest['price_per_ticket'] for guest in chatbot.selected_room['guests'] if guest['type'] == 1),
                        "type": 1,
                    },
                    {
                        "qty": children,
                        "price": next(guest['price_per_ticket'] for guest in chatbot.selected_room['guests'] if guest['type'] == 2),
                        "type": 2,
                    }
                ]
            }
        ],
        "txn_id": "AVATHI" + datetime.now().strftime("%y%m%d%H%M%S"),  # Generate a unique transaction ID
        "universal_coupon_code": "staff"  # Consider making this dynamic if needed
    }
    
    # Call the get_payment_total API
    price_response = APIUtils.get_payment_total(payload)
    total_amount=price_response['data']['total_amount']
    total_without_gst=price_response['data']['total_without_gst']
    discount_coupon=price_response['data']['discount_coupon']
    discount_amount=price_response['data']['discount_amount']
    taxes=price_response['data']['taxes']
    # get_payment_token=APIUtils.get_payment_token()
    get_payment_link=APIUtils.get_payment_link(total_amount)
    payment_link=get_payment_link['result']['paymentLink']
    # print("\ngetpayment total :",price_response)
    if price_response.get("status") == "success":
        payment_data = price_response.get("data")
        chatbot.payment_data = payment_data  # Store the payment data in the chatbot object
        message = f"Great! Here's a summary of your booking:\n"
        message += f"Room: {chatbot.selected_room['ticket_name']}\n"
        message += f"Check-in: {chatbot.check_in}\n"
        message += f"Check-out: {chatbot.check_out}\n"
        message += f"Guests: {chatbot.adults} adults, {chatbot.children} children\n"
        message += f"Amount: ${total_without_gst+discount_amount}\n"
        message += f"Discount Amount: ${discount_amount}\n"
        message += f"Discount Coupon: ${discount_coupon}\n"
        message += f"Included taxes: ${taxes}\n\n"
        message += f"Total amount: ${total_amount}\n"
        
        if payment_link:
            message += f"To complete your booking, please make payment:\n {payment_link}\n\n"
        
        # message += "Would you like to confirm this booking or make any changes?"
        
        chatbot.chat_history.add_ai_message(message)
        # if discount_amount > 0:
        #     chatbot.chat_history.add_ai_message(f"Discount applied: ${discount_amount}")
        
        return "Would you like to confirm this booking or make any changes?"
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, but there was an error calculating the total price for your stay. Would you like to try again or make any changes to your booking?")
        return "Please let me know if you want to try again or make changes."

def ask_for_occupancy(chatbot):
    max_occupancy = chatbot.selected_room['max_occupants_per_room']
    chatbot.chat_history.add_ai_message(f"Great! You've selected the {chatbot.selected_room['ticket_name']}. This room can accommodate up to {max_occupancy} guests.")
    return f"How many adults and children will be staying? (Maximum {max_occupancy} guests in total)"

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
    # print('\nini chat_history : ' ,chat_history)
    return BookingRequest(chat_history, llm)

def run_booking_assistant(user_input, chatbot=None):
    # print('\n chatbot new :', chatbot)
    if not chatbot:
        chatbot = initialize_chat()
    elif isinstance(chatbot, dict):
        chat_history = ChatMessageHistory()
        for message in chatbot.get('chat_history', []):
            if message['role'] == 'user':
                chat_history.add_user_message(message['content'])
            elif message['role'] == 'assistant':
                chat_history.add_ai_message(message['content'])
            elif message['role'] == 'system':
                chat_history.add_system_message(message['content'])
        llm = openai.OpenAI()
        new_chatbot = BookingRequest(chat_history, llm)
        new_chatbot.update_from_dict(chatbot)
        chatbot = new_chatbot
    # print('\nchatbot', chatbot)
    # print("\n chatbot.chat_history :", chatbot.chat_history)
    chatbot.chat_history.add_user_message(user_input)
    # print('\nconvert chat history :', convert_chat_history_to_messages(chatbot.chat_history))
    # print('\n chatbot.possible_experiences : ', chatbot.possible_experiences)
    # print('\n chatbot.selected_room : ', chatbot.selected_room)
    # print('\n chatbot.room_options : ', chatbot.room_options)
    # print('\n chatbot.price_data : ', chatbot.price_data)

    if chatbot.possible_experiences:
        # print('\nchecking exp is selected\n' )
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
    # print("\nchat history msg",convert_chat_history_to_messages(chatbot.chat_history))
    ai_response = chatbot.llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=convert_chat_history_to_messages(chatbot.chat_history),
        functions=functions,
        function_call="auto"
    )
    # print('\nai_response :' ,ai_response)
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
        # elif function_name == "get_price":
            # get_price(chatbot)
        elif function_name == "select_room_or_package":
            select_room_or_package(chatbot, arguments.get("room_selection"))
        elif function_name == "set_occupancy":
            set_occupancy(chatbot, arguments.get("adults"), arguments.get("children"))
        elif function_name == "confirm_booking":
            confirm_booking(chatbot)
    if not chatbot.experience_id:
        next_ai_message(chatbot)

    return chatbot.get_most_recent_message(), chatbot.get_booking_state()

def set_experience(chatbot, arguments):
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    experience_name = arguments.get("experience_name")
    possible_experiences = search_experiences(experience_name)
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
    # print('set dates')
    # print(f"\nSetting dates - check_in: {check_in}, check_out: {check_out}")

    # print(f"Current experience_id: {chatbot.experience_id}")

    # print(check_in ,check_out,chatbot.chat_history.experience_id)
    # print('p')
    if validate_dates(check_in, check_out):
        chatbot.check_in = check_in
        chatbot.check_out = check_out
        # print(check_in ,check_out,chatbot.experience_id)
        if chatbot.experience_id:
            price_info = get_price(chatbot)
            # print(price_info)
            if price_info:
                # print("priceinfo" ,price_info)
                chatbot.chat_history.add_ai_message(f"Thank you. I've set your check-in date to {check_in} and check-out date to {check_out}.\n {price_info} \nPlease select a room from the options above.")
            else:
                chatbot.chat_history.add_ai_message(f"Thank you. I've set your check-in date to {check_in} and check-out date to {check_out}. However, I couldn't retrieve the price for these dates. Would you like to try different dates?")
        else:
            chatbot.chat_history.add_ai_message(f"Thank you. I've set your check-in date to {check_in} and check-out date to {check_out}. Now, let's select an experience for your stay.")
        # chatbot.check_in = check_in
        # chatbot.check_out = check_out
        # chatbot.chat_history.add_ai_message(f"Thank you. I've set your check-in date to {check_in} and check-out date to {check_out}. Would you like me to check the price for these dates?")
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, but the dates you provided are not valid. Please make sure the check-in date is before the check-out date and both are in the future. Could you please provide the dates again?")

def get_price(chatbot):
    if chatbot.experience_id and chatbot.check_in and chatbot.check_out:
        price_response = APIUtils.get_price_by_date(chatbot.experience_id, chatbot.check_in, chatbot.check_out)
        if price_response.get("status") == "success":
            chatbot.price_data = price_response.get("data")
            chatbot.room_options = chatbot.price_data

            chatbot.chat_history.add_ai_message("I've found some room options for your stay. Let me list them for you:")
            return present_room_options(chatbot)
        else:
            chatbot.chat_history.add_ai_message("I'm sorry, but I couldn't retrieve the price information for these dates. Would you like to try different dates?")
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
    elif not chatbot.selected_room:
        # print('\nchatbot.room_options',chatbot.room_options)
        if chatbot.room_options:
            room_options = "\n".join([f"{i+1}. {room['ticket_name']} - ${room['price_per_ticket_with_tax']} per night" for i, room in enumerate(chatbot.room_options)])
            chatbot.chat_history.add_ai_message(f"Here are the available room options nexit ai reso:\n{room_options}\nWhich room would you like to book? You can reply with the number or the name of the room.")
        else:
            chatbot.chat_history.add_ai_message("I'm sorry, but I couldn't find any room options for the selected dates. Would you like to try different dates?")
    elif not chatbot.adults or not chatbot.children:
        chatbot.chat_history.add_ai_message(f"How many adults and children will be staying? (Maximum {chatbot.selected_room['max_occupants_per_room']} guests in total)")
    elif not chatbot.is_ready:
        if chatbot.payment_data:
            total_amount = chatbot.payment_data.get("total_amount")
            taxes = chatbot.payment_data.get("taxes")
            payment_link = chatbot.payment_data.get("paymentLink")
            
            message = f"Great! Here's a summary of your booking:\n"
            message += f"Room: {chatbot.selected_room['ticket_name']}\n"
            message += f"Check-in: {chatbot.check_in}\n"
            message += f"Check-out: {chatbot.check_out}\n"
            message += f"Guests: {chatbot.adults} adults, {chatbot.children} children\n"
            message += f"Total amount: ${total_amount}\n"
            message += f"Included taxes: ${taxes}\n\n"
            
            if payment_link:
                message += f"To complete your booking, please use this payment link: {payment_link}\n\n"
            
            message += "Would you like to confirm this booking or make any changes?"
            
            chatbot.chat_history.add_ai_message(message)
        else:
            chatbot.chat_history.add_ai_message("Would you like me to calculate the total price for your stay?")
    else:
        chatbot.chat_history.add_ai_message("Your booking is confirmed. Is there anything else I can help you with?")
    # if chatbot.possible_experiences:
    #     options = "\n".join([f"{i+1}. {exp['name']}" for i, exp in enumerate(chatbot.possible_experiences)])
    #     chatbot.chat_history.add_ai_message(f"I found these options matching your request:\n{options}\nWhich one would you like to book? You can reply with the name of the experience.")
    # elif not chatbot.experience_id:
    #     chatbot.chat_history.add_ai_message("What kind of experience or room are you looking for?")
    # elif not chatbot.check_in or not chatbot.check_out:
    #     chatbot.chat_history.add_ai_message("When would you like to check in and check out?")
    # elif not chatbot.is_ready:
    #     chatbot.chat_history.add_ai_message("Would you like me to check the price for these dates?")
def search_experiences(query):
    # print('query' ,query)
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
        "description": "Set the experience the user wants to book",
        "parameters": {
            "type": "object",
            "properties": {
                "experience_name": {
                    "type": "string",
                    "description": "The name of the experience "
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
    },
    {
        "name": "select_room_or_package",
        "description": "Select a room or Package from the available options ",
        "parameters": {
            "type": "object",
            "properties": {
                "room_selection": {
                    "type": "string",
                    "description": "The user's room(Package) selection (either  name of the room (Package))"
                }
            },
            "required": ["room_selection"]
        }
    },
    {
        "name": "set_occupancy",
        "description": "Set the number of adults and children for the booking",
        "parameters": {
            "type": "object",
            "properties": {
                "adults": {
                    "type": "integer",
                    "description": "The number of adults"
                },
                "children": {
                    "type": "integer",
                    "description": "The number of children"
                }
            },
            "required": ["adults", "children"]
        }
    }
]

# Example usage
if __name__ == "__main__":
    chatbot = None
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        response, booking_state = run_booking_assistant(user_input, chatbot)
        # print("AI:", response)
        # print("Booking State:", booking_state)
        chatbot = booking_state  # This now stores the dictionary representation
        # print('\n final chatbot :', chatbot)
        
def booking_chat(user_input, chat_state=None):
    chatbot = chat_state if chat_state else None
    response, booking_state = run_booking_assistant(user_input, chatbot)
    return response, booking_state
    