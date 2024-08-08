# chatbot/chatbot/booking_manager.py

class BookingManager:
    STATES = [
        'initial', 'destination', 'date', 'guests', 'login', 'payment'
        ]

    def __init__(self):
        self.current_state = 'initial'

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

# You can add more booking-related methods here as needed