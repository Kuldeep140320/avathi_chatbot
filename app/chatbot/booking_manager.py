# chatbot/chatbot/booking_manager.py

class BookingManager:
    STATES = [
        'initial', 'destination', 'date', 'guests', 'login', 'payment'
        ]

    def __init__(self):
        self.current_state = 'initial'
        self.booking_info = {}

    def get_current_state(self):
        return self.current_state

    def set_state(self, new_state):
        if new_state in self.STATES:
            self.current_state = new_state
        else:
            raise ValueError(f"Invalid booking state: {new_state}")

    def next_state(self):
        current_index = self.STATES.index(self.current_state)
        if current_index < len(self.STATES) - 1:
            self.current_state = self.STATES[current_index + 1]
        return self.current_state

    def reset_state(self):
        self.current_state = 'initial'
        self.booking_info = {}
    def update_booking_state(self, suggested_state, query, context_analysis):
        suggested_state = suggested_state.lower()
        topic_changed = False

        if "topic switch: yes" in context_analysis.lower():
            self.reset_state()
            topic_changed = True
        elif 'destination' in suggested_state and self.current_state in ['initial']:
            self.set_state('destination')
        elif 'date' in suggested_state and self.current_state in ['destination']:
            self.set_state('date')
        elif 'guest' in suggested_state and self.current_state in ['date']:
            self.set_state('guests')
        elif 'login' in suggested_state and self.current_state in ['guests']:
            self.set_state('login')
        elif 'payment' in suggested_state and self.current_state in ['login']:
            self.set_state('payment')
        return self.current_state, topic_changed
# You can add more booking-related methods here as needed