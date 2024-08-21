# chatbot/chatbot/booking_manager.py
from app.routes.api import APIUtils
import sys
from operator import itemgetter

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
    def get_price_by_date(self, exp_id, check_in, check_out):
        room_details =APIUtils.get_price_by_date(exp_id, check_in, check_out)
        organized_rooms = []
        for room in room_details['data']:
            organized_room = {
                'name': room['ticket_name'],
                'id': room['ticket_id'],
                'price': room['price_per_ticket'],
                'total_price': room['price_per_ticket_with_tax'],
                'occupancy': room['max_occupants_per_room'],
                'ticket_order':room['ticket_order'],
                'note': room['ticket_note'],
                'guests': [
                    {'type': guest['type'], 'price': guest['price_per_ticket']}
                    for guest in room['guests']
                ]
            }
            organized_rooms.append(organized_room)
        organized_rooms.sort(key=itemgetter('price'))
        response = f"I've found {len(organized_rooms)} accommodation options for your dates. "
        response += "The prices range from "
        response += f"₹{organized_rooms[0]['price']} to ₹{organized_rooms[-1]['price']} per night. "
        response += "You can view all options in the dropdown menu below. "
        response += "Which type of accommodation are you most interested in?"
        organized_rooms.sort(key=itemgetter('ticket_order'))
        
        return {
            'ai':response,
            'ui_analysis': {
                "options_list": False,
                "guest_list": True,
                'guest_data': room_details,
                # "login_popup": False,
                # "payment_link": False
            },
            

        }
        
    def get_payment_total(self ,payment_total):
        static_payload = {
            "eoexperience_primary_key": "686",
            "total_amount": "0",
            "eouser_primary_key": 8553,
            "date_of_exp": "2024-05-28",
            "end_date": "2024-05-29",
            "ticket_details": [
                {
                    "ticket_id": 1066,
                    "max_occupants_per_room": 3,
                    "guest_type": [
                        {
                            "qty": 2,
                            "price": "11500",
                            "type": 1
                        }
                    ]
                }
            ],
            "txn_id": "AVATHI171404042080",
            "universal_coupon_code": "staff"
        }
        print('\npayment_total\n' ,payment_total)
        payment_details = APIUtils.get_payment_total(payment_total)
        return payment_details
