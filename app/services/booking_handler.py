booking_context = {}

def handle_booking_query(query):
    """Handle booking-related queries, maintaining the booking context."""
    global booking_context

    if 'checkin_date' not in booking_context:
        booking_context['checkin_date'] = query
        return "Please provide the checkout date."
    elif 'checkout_date' not in booking_context:
        booking_context['checkout_date'] = query
        return "How many guests will be staying?"
    elif 'guests' not in booking_context:
        booking_context['guests'] = query
        return "Are you logged in? (yes/no)"
    else:
        # Handle the final booking step
        is_logged_in = query.lower() == "yes"
        if is_logged_in:
            # Proceed with booking logic here, assuming booking_context has all needed information
            booking_info = booking_context
            # Clear booking context after booking
            booking_context = {}
            return f"Booking confirmed: {booking_info}"
        else:
            booking_context = {}
            return "Please log in to complete your booking."
