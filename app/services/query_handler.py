import logging
from app.services.nlp2 import genrate_query_response
from app.services.booking_handler import handle_booking_query

# Define keywords for intent detection
booking_keywords = ["reserve", "reservation", "check-in", "check-out"]
price_keywords = ["price", "cost", "rate", "charges"]

def detect_intent(query):
    """Detect the intent of the user's query."""
    for keyword in booking_keywords:
        if keyword in query.lower():
            return "booking", keyword
    for keyword in price_keywords:
        if keyword in query.lower():
            return "price", keyword
    return "general", None

def handle_query(query):
    """Handle the user query by detecting intent and responding accordingly."""
    intent, keyword = detect_intent(query)
    if intent == "booking":
        response = handle_booking_query(query)
        return {
            'result': f"Detected booking intent with keyword: '{keyword}'.\n\n{response}",
            'source_documents': []
        }
    elif intent == "price":
        response = handle_price_query(query)
        return {
            'result': response,
            'source_documents': []
        }
    else:
        if query:
            response = genrate_query_response(query)
            return response
        return {
            'result': "No relevant information found.",
            'source_documents': []
        }

def handle_price_query(query):
    """Handle price-related queries."""
    # Implement the logic to call the API and get the prices based on the query
    # This is a placeholder implementation and should be replaced with actual API call logic
    return "Price details are not implemented yet."

# The rest of the code (including `genrate_query_response`, `retrieve_and_filter_documents`, etc.) remains unchanged
