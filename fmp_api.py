import os
import requests

API_KEY = os.getenv("FMP_KEY")

# =========================
# 安全请求
# =========================
def safe_get(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# =========================
# 行情数据
# =========================
def get_quote(symbol):
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)
    return data[0] if isinstance(data, list) and len(data) > 0 else None

# =========================
# 财务比率（质量）
# =========================
def get_ratios(symbol):
    url = f"https://financialmodelingprep.com/stable/ratios?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)
    return data[0] if isinstance(data, list) and len(data) > 0 else None

# =========================
# 增长数据（成长）
# =========================
def get_growth(symbol):
    url = f"https://financialmodelingprep.com/stable/financial-growth?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)
    return data[0] if isinstance(data, list) and len(data) > 0 else None
