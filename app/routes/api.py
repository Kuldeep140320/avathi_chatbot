import requests
# from flask import current_app, session
import json
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

pau_merchantId = os.getenv("MERCHANTID")
payu_token = os.getenv("PAYUTOKEN")
class APIUtils:
    # BASE_URL = 'http://127.0.0.1:8080/api/v1'
    BASE_URL = 'http://devapi.avathi.com/api/v1'
    PAYU_BASE_URL = 'https://oneapi.payu.in'
    
    @staticmethod
    def _get_headers():
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'http://159.65.156.66',
            'Referer': 'http://159.65.156.66/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }
    @staticmethod
    def _get_headers_payu():
        return {
            'merchantId': os.getenv("MERCHANTID"),
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.getenv("PAYUTOKEN")}'
        }
        
    @classmethod
    def get_payment_link(cls ,total_amount):
        url = f"{cls.PAYU_BASE_URL}/payment-links/"
        headers = cls._get_headers_payu()
        payload = {
            "subAmount": total_amount,
            "isPartialPaymentAllowed": False,
            "description": "paymentLink for testing",
            "source": "API"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to create payment link: {e}")
            print(f"Response content: {response.text}")  # Add this line to see the full error message
            return None
    @classmethod
    def get_payment_token(cls):
        url="https://accounts.payu.in/oauth/token"
        payload = {
            "client_id": os.getenv("PAYU_CLIENT_ID"),
            "client_secret": os.getenv("PAYU_CLIENT_SECRET"),
            "grant_type": "create_payment_links",
            "scope": "client_credentials"
        }
        headers = cls._get_headers_payu()
        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            return response.json()  # Return the JSON response which contains the token
        except requests.RequestException as e:
            print(f"Failed to retrieve payment token: {e}")
            if response is not None:
                print(f"Response content: {response.text}")
            return None
    @staticmethod
    def _get_session_cookie():
        try:
            # Try to get the session ID directly
            return session.sid if hasattr(session, 'sid') else None
        except RuntimeError:
            # If we're outside of request context, log a warning and return None
            current_app.logger.warning("Attempted to access session outside of request context")
            return None

    @classmethod
    def make_api_call(cls, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{cls.BASE_URL}/{endpoint}"
        headers = cls._get_headers()
        
        # session_id = cls._get_session_cookie()
        # cookies = {'session': session_id} if session_id else {}

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # current_app.logger.error(f"Error calling API {endpoint}: {e}")
            return None

    @classmethod
    def get_price_by_date(cls, eoexperience_primary_key: str, date_of_exp: str, end_date: str) -> Optional[Dict[str, Any]]:
        data = {
            'eoexperience_primary_key': eoexperience_primary_key,
            'date_of_exp': date_of_exp,
            'end_date': end_date
        }
        return cls.make_api_call('experience/getPriceByDate', data)

    @classmethod
    def get_payment_total(cls, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return cls.make_api_call('getPaymentTotal', payload)      
    # def get_payment_total(self, exp_id: str, check_in: str, check_out: Optional[str]) -> Optional[Dict[str, Any]]:
    #     # Map new arguments to the required payload structure
    #     data = {
    #         'eoexperience_primary_key': exp_id,
    #         'total_amount': "0",  # Assuming you always start with a total amount of "0"
    #         'eouser_primary_key': self.user_primary_key,  # Assuming the user primary key is stored in the instance
    #         'date_of_exp': check_in,
    #         'end_date': check_out,
    #         'ticket_details': self.get_ticket_details(),  # Assuming there's a method to retrieve ticket details
    #         'txn_id': self.generate_txn_id(),  # Assuming there's a method to generate or retrieve a transaction ID
    #         'universal_coupon_code': self.get_universal_coupon_code()  # Assuming there's a method to retrieve a coupon code
    #     }
        
    #     return self.make_api_call('getPaymentTotal', data)



# Usage examples remain the same