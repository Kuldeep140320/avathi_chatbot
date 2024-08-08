import os
import sys
import streamlit as st
from datetime import datetime, date
from dotenv import load_dotenv

# Ensure the correct path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.faiss_helper import initialize_vector_store
from app.services.query_handler import handle_query
# from app.routes.booking import getPriceByDate, callPaymesntAPI

# Load environment variables
load_dotenv()
from app.chatbot.travel_assistant import TravelAssistant


import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# assistant = TravelAssistant()

# Initialize session state for conversation history and selected experience
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'selected_experience' not in st.session_state:
    st.session_state.selected_experience = None

if 'checkin_date' not in st.session_state:
    st.session_state.checkin_date = None

if 'checkout_date' not in st.session_state:
    st.session_state.checkout_date = None

if 'guest_details' not in st.session_state:
    st.session_state.guest_details = {}
if 'travel_assistant' not in st.session_state:
    st.session_state.travel_assistant = TravelAssistant()
    
def main():
    st.title("Chatbot Data and Chain Flow Visualization")
    # Initialize vector store
    with st.sidebar:
        st.header("Settings")
        vector_db_file_path = st.text_input("Vector Store Path", "vector_store_new_5")
        if st.button("Initialize Vector Store"):
            try:
                vector_store = initialize_vector_store(vector_db_file_path)
                st.success("Vector store initialized.")
                st.write(f"Vector store details: {vector_store}")
            except Exception as e:
                st.error(f"Error initializing vector store: {e}")

    query = st.text_input("Enter your query", placeholder="Type your query here...")

    if st.button("Send"):
        try:
            # result = handle_query(query)
            # result = assistant.run(query)
            result = st.session_state.travel_assistant.run(query)
            st.session_state.conversation_history.append(("user", query))
            st.session_state.conversation_history.append(("bot", result['result']))
            # display_conversation_history()
            chat_history = st.session_state.travel_assistant.memory.chat_memory.messages
            for message in chat_history:
                if message.type == 'human':
                    st.markdown(f"**You:** {message.content}")
                elif message.type == 'ai':
                    st.markdown(f"**Bot:** {message.content}")
            if 'document_metadata' in result and result['document_metadata']:
                st.subheader("Select an Experience Document")
                selected_experience = st.selectbox(
                    "Choose a document",
                    options=[f"{doc['primary_key']}: {doc['name']}" for doc in result['document_metadata']],
                    key='experience_select'
                )
                st.session_state.selected_experience = selected_experience if selected_experience != "" else None

            with st.expander("Detailed Information", expanded=False):
                st.subheader("Source Documents")
                for j, doc in enumerate(result['source_documents']):
                    st.markdown(f"##### Document {j + 1} Metadata")
                    for key, value in doc.metadata.items():
                        st.markdown(f"**{key.capitalize()}: {value}")
                    st.markdown("##### Document Content")
                    st.markdown(doc.page_content.replace('\n', '\n\n'))
                st.subheader("context")
                st.markdown(result['context'])
        except Exception as e:
            st.error(f"Error invoking chain: {e}")

    if st.session_state.selected_experience:
        checkin_date = st.date_input("Check-in Date", key='checkin_date')
        checkout_date = st.date_input("Check-out Date", key='checkout_date')
        if st.button("Get Prices"):
            selected_primary_key = int(st.session_state.selected_experience.split(":")[0])
            get_prices(selected_primary_key, checkin_date, checkout_date)

def get_prices(primary_key, checkin_date, checkout_date):
    st.write(primary_key, checkin_date, checkout_date)
    st.write("Fetching prices...")
    if primary_key and checkin_date and checkout_date:
        getPriceByDate_response = getPriceByDate(primary_key, checkin_date, checkout_date)
        st.write("Prices received:")
        display_prices(getPriceByDate_response, primary_key, checkin_date, checkout_date)

def display_prices(response, primary_key, checkin_date, checkout_date):
    if response and response.get('status') == 'success':
        st.success("Prices fetched successfully")
        st.subheader("Price Details")
        data = response.get('data', [])
        guest_type_mapping = {1: "Adult", 3: "Child"}

        for item in data:
            st.markdown(f"## {item['ticket_name']}")
            cols = st.columns(2)
            with cols[0]:
                st.write(f"**Ticket ID:** {item['ticket_id']}")
                st.write(f"**Pax:** {item['pax']}")
                st.write(f"**Price per Ticket with Tax:** {item['price_per_ticket_with_tax']}")
                st.write(f"**Price per Ticket:** {item['price_per_ticket']}")
                st.write(f"**Host Tax per Ticket:** {item['host_tax_per_ticket']}")
                st.write(f"**Commission Tax per Ticket:** {item['commission_tax_per_ticket']}")
                st.write(f"**Total Amount:** {item['total_amount']}")
            with cols[1]:
                st.write(f"**Type:** {item['type']}")
                st.write(f"**Period:** {item['period']}")
                st.write(f"**Max Occupants per Room:** {item['max_occupants_per_room']}")
                st.write(f"**Ticket Note:** {item['ticket_note']}")
            
            st.markdown("### Guests")
            for guest in item.get('guests', []):
                guest_type = guest_type_mapping[guest['type']]
                guest_qty = st.number_input(
                    f"Number of {guest_type}s",
                    min_value=0,
                    max_value=10,
                    value=0,
                    key=f"guest_qty_{item['ticket_id']}_{guest['type']}"
                )
                st.session_state.guest_details[(item['ticket_id'], guest['type'])] = {
                    "qty": guest_qty,
                    "price": guest['price_per_ticket'],
                    "type": guest['type']
                }
            st.markdown("---")
        
        if st.button("Submit"):
            prepare_payload_and_call_api(primary_key, checkin_date, checkout_date)
    else:
        st.error("Failed to fetch prices")

def prepare_payload_and_call_api(primary_key, checkin_date, checkout_date):
    ticket_details = []
    total_amount = 0

    for (ticket_id, guest_type), guest_detail in st.session_state.guest_details.items():
        if guest_detail['qty'] > 0:
            total_amount += guest_detail['qty'] * guest_detail['price']
            ticket_details.append({
                "ticket_id": ticket_id,
                "max_occupants_per_room": 0,  # You can update this value as needed
                "guest_type": [
                    {
                        "qty": guest_detail['qty'],
                        "price": str(guest_detail['price']),
                        "type": guest_type
                    }
                ]
            })
    
    payload = {
        "eoexperience_primary_key": str(primary_key),
        "date_of_exp": checkin_date.strftime("%Y-%m-%d"),
        "end_date": checkout_date.strftime("%Y-%m-%d"),
        "eouser_primary_key": 8553,  # Replace with actual user primary key
        "ticket_details": ticket_details,
        "total_amount": str(total_amount),
        "txn_id": "AVATHI172251470632",  # Replace with actual transaction ID
        "universal_coupon_code": ""
    }

    st.write("Payload:", payload)
    response = callPaymentAPI(payload)
    st.success("Payment API called successfully!")
    st.write(response)

# def display_conversation_history():
    # st.subheader("Conversation History")
    # for i, (sender, message_text) in enumerate(st.session_state.conversation_history):
    #     if sender == "user":
    #         st.markdown(f"**You:** {message_text}")
    #     else:
    #         st.markdown(f"**Bot:** {message_text}")
    

if __name__ == "__main__":
    main()
