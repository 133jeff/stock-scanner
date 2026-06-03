import requests

API_KEY = "PGStuFJEoUpLtUjfH3wSbUMp1RruJSgH"

def safe_get(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


def get_quote(symbol):
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)

    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return {}


def get_ratios(symbol):
    url = f"https://financialmodelingprep.com/stable/ratios?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)

    if isinstance(data, list) and len(data) > 0:
        return data[0]
    return {}


def get_growth(symbol):
    url = f"https://financialmodelingprep.com/stable/financial-growth?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)

    if isinstance(data) and isinstance(data, list) and len(data) > 0:
        return data[0]
    return {}
