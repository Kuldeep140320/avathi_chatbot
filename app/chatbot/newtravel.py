import openai
from langchain.memory import ChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from datetime import datetime
import re
from fuzzywuzzy import fuzz
import sys,os
import json
from app.utils.vector_store import retriever
from app.routes.api import APIUtils
from app.config import OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

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
        # self.room_options = None
        self.selected_room = None
        self.adults = None
        self.children = None
        self.payment_data = None
        self.options=[]
        self.date_picker=False
        self.guest_type=False
        self.current_step=None
        self.show_login_popup=False
        self.is_stay=False
        self.is_event=False
        self.user_auth={}
        
    def set_current_step(self,current_step):
        self.current_step=current_step
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
        # self.room_options = data.get('room_options')
        self.selected_room = data.get('selected_room')
        self.adults = data.get('adults')
        self.children = data.get('children')
        self.payment_data = data.get('payment_data')
        self.options = []
        self.date_picker=False
        self.guest_type=False
        self.current_step=data.get('current_step')
        self.show_login_popup=False
        self.user_auth=data.get('user_auth',{})
        self.is_stay=data.get('is_stay')
        self.is_event=data.get('is_event')
    def add_option(self, option):
        self.options.append(option)
    def clear_options(self):
        self.options.clear()

    def get_most_recent_message(self):
        return self.chat_history.messages[-1].content
    def get_booking_state(self):
        return {
            "experience_id": self.experience_id,
            "experience_name": self.experience_name,
            "options":self.options,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "is_ready": self.is_ready,
            "possible_experiences": self.possible_experiences,
            "price_data": self.price_data,
            # "room_options": self.room_options,
            "selected_room": self.selected_room,
            "adults": self.adults,
            "children": self.children,
            "payment_data": self.payment_data,
            "date_picker":self.date_picker,
            "guest_type":self.guest_type,
            "current_step":self.current_step,
            "show_login_popup":self.show_login_popup,
            "user_auth":self.user_auth,
            "is_event":self.is_event,
            "is_stay":self.is_stay,
            
        }
def present_room_options(chatbot):
    for room in chatbot.price_data:
        chatbot.add_option(f"{room['ticket_name']}")
    return chatbot

def select_room_or_package(chatbot, room_selection,selected_room = None):
    if not chatbot.price_data:
        return None
    if not selected_room:
        options = "\n".join([f"{exp['ticket_id']}: {exp['ticket_name']}" for exp in chatbot.price_data])
        selected_room_id = select_single_option(chatbot, room_selection,options)
        for room in chatbot.price_data:
            if str(selected_room_id).strip() == str(room['ticket_id']):
                selected_room = room
                break
    
    if selected_room:
        chatbot.selected_room = selected_room
        chatbot.current_step="set_occupancy"
        
        return ask_for_occupancy(chatbot)
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, I couldn't find a room matching your selection. Could you please try again?")
        return present_room_options(chatbot)
    
def calculate_price_and_payment(chatbot):
    # Prepare the payload for the get_payment_total API call
    user_data = chatbot.user_auth
    if 'user_key' in user_data and user_data['user_key']:
        user_key=user_data['user_key']
    else:
        user_key=""
    payload = {
        "eoexperience_primary_key": chatbot.experience_id,
        "total_amount": "0",
        "eouser_primary_key":user_key,  # This seems to be a static value, consider making it dynamic if needed
        "date_of_exp": chatbot.check_in,
        "end_date": None,
        "ticket_details": [
            {
                "ticket_id": chatbot.selected_room['ticket_id'],
                "max_occupants_per_room": chatbot.selected_room['max_occupants_per_room'],
                "guest_type": [
                    {
                        "qty": chatbot.adults,
                        "price": next(guest['price_per_ticket'] for guest in chatbot.selected_room['guests'] if guest['type'] == 1),
                        "type": 1,
                    }
                    # {
                    #     "qty": chatbot.children,
                    #     "price": next(guest['price_per_ticket'] for guest in chatbot.selected_room['guests'] if guest['type'] == 2),
                    #     "type": 2,
                    # }
                ]
            }
        ],
        "txn_id": "AVATHI" + datetime.now().strftime("%y%m%d%H%M%S"),  # Generate a unique transaction ID
        "universal_coupon_code": ""  # Consider making this dynamic if needed
    }
    if chatbot.is_stay:
        payload["ticket_details"][0]["guest_type"].append({
            "qty": chatbot.children,
            "price": next(guest['price_per_ticket'] for guest in chatbot.selected_room['guests'] if guest['type'] == 2),
            "type": 2,
        })
        
    price_response = APIUtils.get_payment_total(payload)
    price_response['payment_link']=None
    payment_data = price_response.get("data")
    chatbot.payment_data = payment_data
    total_amount=price_response['data']['total_amount']
    if 'user_key' in user_data and chatbot.user_auth['user_key'] and chatbot.user_auth['access_token']:
        create_payment_payload={
                "eoexperience_primary_key":chatbot.experience_id,
                "date_of_exp": chatbot.check_in,
                "end_date": chatbot.check_out,
                "total_amount": total_amount,
                "eouser_primary_key": chatbot.user_auth['user_key'],
                "txn_id": "AVATHI172475431836",
                "universal_coupon_code": "",
                "ticket_details": [
                    {
                        "ticket_id": chatbot.selected_room['ticket_id'],
                        "max_occupants_per_room": chatbot.selected_room['max_occupants_per_room'],
                        "guest_type": [
                            {
                                "qty": chatbot.adults,
                                "price": next(guest['price_per_ticket'] for guest in chatbot.selected_room['guests'] if guest['type'] == 1),
                                "type": 1,
                            },
                            {
                                "qty": chatbot.children,
                                "price": next(guest['price_per_ticket'] for guest in chatbot.selected_room['guests'] if guest['type'] == 2),
                                "type": 2,
                            }
                        ]
                    }
                ]
            }
        create_payment=APIUtils.create_payment(create_payment_payload,chatbot.user_auth['access_token'])
        take_payment=create_payment['data']['take_payment']
        success=create_payment['data']['success']
        if take_payment and  success:
            total_amount=create_payment['data']['total_amount']
            get_payment_token=APIUtils.get_payment_token()
            token=get_payment_token['access_token']
            get_payment_link=APIUtils.get_payment_link(total_amount,token)
            payment_link=get_payment_link['result']['paymentLink']
            payment_data['payment_link'] =payment_link
            chatbot.payment_data = payment_data
            message =chatbot.get_most_recent_message()
            message += f"\nGreat! Here's a summary of your booking:"
            chatbot.chat_history.add_ai_message(message)
            return "Would you like to confirm this booking or make any changes?"

        else:
            message =chatbot.get_most_recent_message()
            chatbot.show_login_popup=True
            message += "\nGreat! Here's a summary of your booking:"
            chatbot.chat_history.add_ai_message(message)
            return "Would you like to confirm this booking or make any changes?"
    else:
        message =chatbot.get_most_recent_message()
        chatbot.show_login_popup=True
        message += "Great! Here's a summary of your booking:"
        chatbot.chat_history.add_ai_message(message)
        return "Would you like to confirm this booking or make any changes?"
    
def set_occupancy(chatbot, adults, children):
    max_occupancy = 3
    total_guests = adults + children
    if total_guests > max_occupancy:
        chatbot.chat_history.add_ai_message(f"I'm sorry, but the total number of guests ({total_guests}) exceeds the maximum occupancy ({max_occupancy}) for this room. Would you like to select a different room or adjust the number of guests?")
        return "Please choose to either 'select another room' or 'adjust guests'."
    
    chatbot.adults = adults
    chatbot.children = children
    
    message = f"Great! You've selected {adults} adult{'s' if adults > 1 else ''} and {children} child{'ren' if children > 1 else ''}.\n"
    # chatbot.chat_history.add_ai_message(message)
    user_data=chatbot.user_auth
    if 'user_key' not in user_data and user_data['user_key']:
        message += f"Would you like to log in to get discount prices? If yes, click on the give link."
        chatbot.set_current_step('login_prompt')
        chatbot.chat_history.add_ai_message(message)
    else:
        chatbot.chat_history.add_ai_message(message)
        calculate_price_and_payment(chatbot)
    return "Please respond with 'yes' if you'd like to log in, or 'no' to continue without logging in."

def ask_for_occupancy(chatbot):
    max_occupancy = chatbot.selected_room['max_occupants_per_room']
    chatbot.chat_history.add_ai_message(f"Great! You've selected the {chatbot.selected_room['ticket_name']}. Please provide the number of adults and children.")
    chatbot.guest_type=True
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
    
    Only respond to queries related to booking information. Do not initiate any 
    new bookings or confirmations yourself. Your role is strictly to assist and provide relevant booking details.
    """
    chat_history.add_message(SystemMessage(content=system_message))

    ai_message = "Welcome! What kind of travel experience or room are you looking to book today?"
    chat_history.add_message(AIMessage(content=ai_message))
    # print('\nini chat_history : ' ,chat_history)
    return BookingRequest(chat_history, llm)
def select_single_option(chatbot, user_input,options):
    prompt = f"""Given the following list of experiences:
    {options}
    And the user input: "{user_input}"

    Determine which experience name the user input matches most closely. Consider partial matches and semantic similarity.

    Your response should be only the id of the best matching experience. If there's no good match, respond with "None".

    """
    # Call the LLM (using OpenAI's API in this example)
    response =chatbot.llm.chat.completions.create(
        model="gpt-4o-mini",  # or whichever model you're using
        messages=[
            {"role": "system", "content": "You are an AI assistant helping to match user input to a list of experience names."},
            {"role": "user", "content": prompt}
        ]
    )
    selected_id = response.choices[0].message.content.strip()
    return selected_id if selected_id != "None" else None
def process_experience_selection(chatbot, user_input):
    if not chatbot.possible_experiences:
        return None
    experience_options = "\n".join([f"{exp['id']}: {exp['name']}" for exp in chatbot.possible_experiences])
    selected_id = select_single_option(chatbot, user_input,experience_options)
        # try:
        #     selection = int(user_input) - 1
        #     if 0 <= selection < len(chatbot.possible_experiences):
        #         selected_experience = chatbot.possible_experiences[selection]
        # except ValueError:
        #     for exp in chatbot.possible_experiences:
        #         if fuzz.ratio(user_input.lower(), exp['name'].lower()) > 80:
        #             selected_experience = exp
        #             break
    if selected_id:
        selected_experience=None
        for exp in chatbot.possible_experiences:
            if str(exp['id']).strip() == str(selected_id):
                selected_experience=exp
                break
        if selected_experience:
            chatbot.experience_id = selected_experience['id']
            chatbot.experience_name = selected_experience['name']
            chatbot.possible_experiences = None
            chatbot.date_picker = True
            chatbot.check_in = None
            chatbot.check_out = None
            chatbot.selected_room = None
            chatbot.adults = None
            chatbot.children = None
            chatbot.payment_data = None
            chatbot.price_data = None
            chatbot.is_event=selected_experience['is_event']
            chatbot.is_stay=selected_experience['is_stay']
            chatbot.current_step="set_dates"
            if chatbot.is_event:
                chatbot.chat_history.add_ai_message(f"Great! You've selected {chatbot.experience_name}. Please select the Date?")
            else:
                chatbot.chat_history.add_ai_message(f"Great! You've selected {chatbot.experience_name}. When would you like to check in and check out?")
            
            return chatbot.get_most_recent_message(), chatbot.get_booking_state(), convert_chat_history_to_messages(chatbot.chat_history)
    
    chatbot.chat_history.add_ai_message("I'm sorry, I couldn't match your input to any of the available experiences. Could you please try again? You can type the name of the experience you're interested in.")
    return chatbot.get_most_recent_message(), chatbot.get_booking_state(), convert_chat_history_to_messages(chatbot.chat_history)

def interpret_user_response(chatbot,user_input):
    prompt = f"""Given the user's response: "{user_input}"

    Determine if this response is affirmative (yes) or negative (no).
    Consider various ways of expressing agreement or disagreement, including informal language.

    Your response should be only "yes" or "no".
    If the intent is unclear, respond with "unclear".
    """

    try:
        response = chatbot.llm.chat.completions.create(
            model="gpt-4o-mini",  # or whichever model you're using
            messages=[
                {"role": "system", "content": "You are an AI assistant interpreting user responses as yes or no."},
                {"role": "user", "content": prompt}
            ]
        )

        interpretation = response.choices[0].message.content.strip().lower()
        
        if interpretation in ["yes", "no"]:
            return interpretation
        else:
            return "unclear"
    except Exception as e:
        print(f"Error in interpret_user_response: {str(e)}")
        return "unclear"
def process_login_response(chatbot, user_input):
    response = interpret_user_response(chatbot,user_input)
    print('\nresponse:',response)
    if response == "yes":
        chatbot.chat_history.add_ai_message("Great! Please enter log in Details.")
        chatbot.show_login_popup=True
        return "Please provide your phone number."
    elif response == "no":
        chatbot.chat_history.add_ai_message("No problem. We'll continue without logging in.")
        chatbot.show_login_popup=False
        return calculate_price_and_payment(chatbot)
    else:
        chatbot.chat_history.add_ai_message("I'm not sure if you want to log in or not. Could you please clarify?")
        return "Please respond with 'yes' if you'd like to log in for discounts, or 'no' to continue without logging in."
def run_booking_assistant(user_input, chatbot=None):
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
    chatbot.chat_history.add_user_message(user_input)
    if chatbot.possible_experiences:
        return process_experience_selection(chatbot, user_input)
    
    if chatbot.current_step == 'login_prompt':
        process_login_response(chatbot, user_input)
        return chatbot.get_most_recent_message(), chatbot.get_booking_state() ,convert_chat_history_to_messages(chatbot.chat_history)
    
    if chatbot.price_data and chatbot.current_step=="set_room":
        selected_room=None
        for room in chatbot.price_data:
            if fuzz.ratio(user_input.lower(), room['ticket_name'].lower()) > 90:
                selected_room = room
                break
        room_selection=None
        if selected_room:
            select_room_or_package(chatbot, room_selection,selected_room)
            return chatbot.get_most_recent_message(), chatbot.get_booking_state() ,convert_chat_history_to_messages(chatbot.chat_history)
            
    
    ai_response = chatbot.llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=convert_chat_history_to_messages(chatbot.chat_history),
        functions=functions,
        function_call="auto"
    )
    if ai_response.choices[0].message.content:
        chatbot.chat_history.add_ai_message(ai_response.choices[0].message.content)
    elif ai_response.choices[0].message.function_call:
        function_call = ai_response.choices[0].message.function_call
        function_name = function_call.name
        arguments = json.loads(function_call.arguments)
        if function_name == "set_experience":
            set_experience(chatbot, arguments)
        elif function_name == "set_dates":
            set_dates(chatbot, arguments)
        elif function_name == "select_room_or_package":
            select_room_or_package(chatbot, arguments.get("room_selection"))
        elif function_name == "set_occupancy":
            set_occupancy(chatbot, arguments.get("adults"), arguments.get("children"))
        elif function_name == "confirm_booking":
            confirm_booking(chatbot)
    # if not chatbot.experience_id:
        # next_ai_message(chatbot)
        
    return chatbot.get_most_recent_message(), chatbot.get_booking_state() ,convert_chat_history_to_messages(chatbot.chat_history)

def select_relevant_experiences(chatbot,user_query, possible_experiences):
    experience_options = "\n".join([f"{exp['id']}: {exp['name']}" for exp in possible_experiences])
    prompt = f"""Given the following list of experiences:
    {experience_options}
    And the user query: "{user_query}"
    Your task:
    1. Determine which experiences are most relevant to the user's query.
    2. Return only the IDs of the relevant experiences, separated by commas.
    3. If there are no relevant experiences, return "None".

    Your response should be in the format:
    Relevant IDs: <comma-separated list of IDs or "None">
    """
    response = chatbot.llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI assistant helping to select relevant travel experiences based on a user query."},
            {"role": "user", "content": prompt}
        ]
    )
    # Parse the LLM's response
    llm_response = response.choices[0].message.content.strip()
    relevant_ids = llm_response.split(": ")[1]

    if relevant_ids == "None":
        return []
    else:
        return [int(id.strip()) for id in relevant_ids.split(",")]
def set_experience(chatbot, arguments):
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    experience_name = arguments.get("experience_name")
    possible_experiences = search_experiences(experience_name)
    
    if not possible_experiences:
        chatbot.chat_history.add_ai_message("I'm sorry, I couldn't find any experiences matching your request. Could you please try a different search term?")
        return

    relevant_ids = select_relevant_experiences(chatbot,experience_name, possible_experiences)
    relevant_experiences = [exp for exp in possible_experiences if (exp['id']) in relevant_ids]
    if len(relevant_experiences) == 1:
        chatbot.experience_id = relevant_experiences[0]["id"]
        chatbot.experience_name = relevant_experiences[0]["name"]
        chatbot.chat_history.add_ai_message(f"Great! I've found the experience: {chatbot.experience_name}. When would you like to check in and check out?")
        chatbot.date_picker = True
    elif len(relevant_experiences) > 1:
        chatbot.possible_experiences = relevant_experiences
        for exp in relevant_experiences:
            chatbot.add_option(exp['name'])
        chatbot.chat_history.add_ai_message(f"I found multiple options matching your request.Here are the options \nPlease reply with the name of the experience you're interested in.")
    else:
        chatbot.chat_history.add_ai_message("I'm sorry, I couldn't find any experiences closely matching your request. Could you please try a different search term or provide more details about what you're looking for?")
def set_dates(chatbot, arguments):
    print(arguments)
    dates = arguments.get("dates", [])
    is_valid, error_message, check_in, check_out = validate_dates(chatbot, dates)
    # check_in = arguments.get("check_in")
    # check_out = arguments.get("check_out")
    print(check_in,check_out)
    if is_valid:
        chatbot.check_in = check_in
        chatbot.check_out = check_out
        if chatbot.experience_id:
            price_info = get_price(chatbot)
            
            print(price_info)
            if price_info:
                
                check_in_obj = datetime.strptime(check_in, '%Y-%m-%d')
                check_in_obj = check_in_obj.strftime('%d %b %Y')
                message = f"Thank you. I've set your dates :\nCheck-in : {check_in_obj}"
                if chatbot.is_stay:
                    check_out_obj = datetime.strptime(check_out, '%Y-%m-%d')
                    check_out_obj = check_out_obj.strftime('%d %b %Y')
                    message +=f"\nCheck-out : {check_out_obj}."
                message +=f"\nPlease select a room from the options."
                chatbot.current_step="set_room"
                chatbot.chat_history.add_ai_message(message)
            else:
                chatbot.chat_history.add_ai_message(f"Thank you. I've set your check-in date to {check_in} and check-out date to {check_out}. However, I couldn't retrieve the price for these dates. Would you like to try different dates?")
        else:
            chatbot.chat_history.add_ai_message(f"Thank you. I've set your check-in date to {check_in} and check-out date to {check_out}. Now, let's select an experience for your stay.")
    else:
        chatbot.chat_history.add_ai_message(f"I'm sorry, but the dates you provided are not valid. {error_message} Could you please provide the dates again?")

def get_price(chatbot):
    if chatbot.is_event:
        chatbot.check_out=chatbot.check_in
    if chatbot.experience_id and chatbot.check_in and chatbot.check_out:
        price_response = APIUtils.get_price_by_date(chatbot.experience_id, chatbot.check_in, chatbot.check_out)
        if price_response.get("status") == "success":
            chatbot.price_data = price_response.get("data")
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
def search_experiences(query):
    results = retriever.get_relevant_documents(query)
    return [{
        "id": doc.metadata["eoexperience_primary_key"],
        "name": doc.metadata["eoexperience_name"],
        "is_stay": doc.metadata["is_stay"],
        "is_event": doc.metadata["is_event"],
        
        } for doc in results]

def validate_dates(chatbot, dates):
    try:
        today = datetime.now().date()
        if len(dates) == 1 and chatbot.is_event:
            check_in = datetime.strptime(dates[0], "%Y-%m-%d").date()
            check_out = None
            if check_in < today:
                return False, "The event date cannot be in the past. Please provide a future date.", None, None
        elif len(dates) == 2 and chatbot.is_stay:
            check_in, check_out = sorted(datetime.strptime(date, "%Y-%m-%d").date() for date in dates)
            if check_in < today:
                return False, "The check-in date cannot be in the past. Please provide a future date.", None, None
            if check_out < today:
                return False, "The check-out date cannot be in the past. Please provide a future date.", None, None
            if check_in >= check_out:
                return False, "The check-out date must be after the check-in date.", None, None
            max_stay = 30  # Assuming a maximum stay of 30 days, adjust as needed
            if (check_out - check_in).days > max_stay:
                return False, f"The maximum stay duration is {max_stay} days. Please adjust your dates.", None, None
        else:
            if chatbot.is_event:
                return False, "For an event, please provide a single date.", None, None
            elif chatbot.is_stay:
                return False, "For a stay, please provide both check-in and check-out dates.", None, None
            else:
                return False, "Invalid booking type. Please specify either an event or a stay.", None, None

        return True, None, check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d") if check_out else None

    except ValueError:
        return False, "Invalid date format. Please use YYYY-MM-DD format for dates.", None, None
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
        "description": "Set the date(s) for the booking. If one date is provided, it's treated as an event date. If two dates are provided, they're treated as check-in and check-out dates for a stay. The earlier date will be set as check-in and the later as check-out. Dates should not be before today.",
        "parameters": {
            "type": "object",
            "properties": {
                "dates": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "date"
                    },
                    "minItems": 1,
                    "maxItems": 2,
                    "description": "The date(s) in YYYY-MM-DD format. Provide one date for an event, or two dates for a stay (check-in and check-out)."
                }
            },
            "required": ["dates"]
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
        chatbot = booking_state  # This now stores the dictionary representation
def booking_chat(user_input, chat_state=None):
    chatbot = chat_state if chat_state else None
    response, booking_state ,conversation_history = run_booking_assistant(user_input, chatbot)
    return response, booking_state,conversation_history
    