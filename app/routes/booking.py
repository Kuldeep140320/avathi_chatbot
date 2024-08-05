import requests
from datetime import datetime

def getPriceByDate(primary_key, checkin_date, checkout_date):
    url = "https://api.avathi.com/api/v1/experience/getPriceByDate"
    payload = {
        "eoexperience_primary_key": str(primary_key),
        "date_of_exp": checkin_date.strftime("%Y-%m-%d"),
        "end_date": checkout_date.strftime("%Y-%m-%d")
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def callPaymentAPI(payload):
    url = "https://api.avathi.com/api/v1/getPaymentTotal"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
