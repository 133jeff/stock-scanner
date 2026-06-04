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
            print("HTTP ERROR:", r.status_code)
            return None
        return r.json()
    except Exception as e:
        print("REQUEST ERROR:", e)
        return None

# =========================
# 行情数据
# =========================
def get_quote(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={API_KEY}"
    data = safe_get(url)

    if isinstance(data, list) and len(data) > 0:
        return data[0]

    return None

# =========================
# 历史价格（V4 RSI用）
# =========================
def get_history(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={API_KEY}&timeseries=20"
    data = safe_get(url)

    if not data or "historical" not in data:
        return []

    # ⚠️ 保证时间顺序正确（RSI必须）
    return [x["close"] for x in reversed(data["historical"])]

# =========================
# 财务比率（质量因子）
# =========================
def get_ratios(symbol):
    url = f"https://financialmodelingprep.com/stable/ratios?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)

    if isinstance(data, list) and len(data) > 0:
        return data[0]

    return None

# =========================
# 增长数据（成长因子）
# =========================
def get_growth(symbol):
    url = f"https://financialmodelingprep.com/stable/financial-growth?symbol={symbol}&apikey={API_KEY}"
    data = safe_get(url)

    if isinstance(data, list) and len(data) > 0:
        return data[0]

    return None
