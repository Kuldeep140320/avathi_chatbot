import requests
from flask import current_app, session
import json
from typing import Dict, Any, Optional

class APIUtils:
    # BASE_URL = 'http://127.0.0.1:8080/api/v1'
    BASE_URL = 'http://devapi.avathi.com/api/v1'

    
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
        
        session_id = cls._get_session_cookie()
        cookies = {'session': session_id} if session_id else {}

        try:
            response = requests.post(url, headers=headers, json=data, cookies=cookies)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            current_app.logger.error(f"Error calling API {endpoint}: {e}")
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
    def get_payment_total(cls, eoexperience_primary_key: str, total_amount: str, eouser_primary_key: int,
                          date_of_exp: str, end_date: str, ticket_details: list, txn_id: str,
                          universal_coupon_code: str) -> Optional[Dict[str, Any]]:
        data = {
            'eoexperience_primary_key': eoexperience_primary_key,
            'total_amount': total_amount,
            'eouser_primary_key': eouser_primary_key,
            'date_of_exp': date_of_exp,
            'end_date': end_date,
            'ticket_details': ticket_details,
            'txn_id': txn_id,
            'universal_coupon_code': universal_coupon_code
        }
        return cls.make_api_call('getPaymentTotal', data)

# Usage examples remain the same