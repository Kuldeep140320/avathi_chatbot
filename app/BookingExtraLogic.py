import requests

def get_price_by_date(experience_id, start_date, end_date):
    url = "http://devapi.avathi.com/api/v1/experience/getPriceByDate"

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }

    payload = {
        "eoexperience_primary_key": experience_id,
        "date_of_exp": start_date,
        "end_date": end_date
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
