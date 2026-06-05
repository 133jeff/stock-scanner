import os
import time
import requests
from universe import get_universe

# =========================
# ENV
# =========================
FMP_KEY = os.getenv("FMP_KEY")
TWELVE_KEY = os.getenv("TWELVE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STOCKS = get_universe()

# =========================
# SAFE REQUEST (with retry)
# =========================
def safe_get(url, headers=None):
    for _ in range(2):  # retry twice
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            time.sleep(0.3)
    return None

# =========================
# FMP
# =========================
def get_fmp_quote(symbol):
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
    data = safe_get(url)
    if isinstance(data, list) and len(data) > 0:
        q = data[0]
        return {
            "price": q.get("price") or 0,
            "changesPercentage": q.get("changesPercentage") or 0,
        }
    return None


def get_fmp_history(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=200"
    data = safe_get(url)
    if data and "historical" in data:
        prices = [x["close"] for x in reversed(data["historical"]) if x.get("close")]
        if len(prices) > 30:
            return prices
    return None

# =========================
# TWELVE DATA (fallback)
# =========================
def get_twelve_quote(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_KEY}"
    data = safe_get(url)
    try:
        return {
            "price": float(data["price"]),
            "changesPercentage": 0
        }
    except:
        return None


def get_twelve_history(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=200&apikey={TWELVE_KEY}"
    data = safe_get(url)
    try:
        values = data["values"]
        prices = [float(x["close"]) for x in reversed(values)]
        return prices if len(prices) > 30 else None
    except:
        return None

# =========================
# YAHOO (last fallback)
# =========================
def get_yahoo_quote(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    data = safe_get(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        q = data["quoteResponse"]["result"][0]
        return {
            "price": q.get("regularMarketPrice") or 0,
            "changesPercentage": q.get("regularMarketChangePercent") or 0
        }
    except:
        return None


def get_yahoo_history(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=6mo&interval=1d"
    data = safe_get(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [x for x in closes if isinstance(x, (int, float))]
    except:
        return None

# =========================
# MASTER DATA ENGINE
# =========================
def get_quote(symbol):

    q = get_fmp_quote(symbol)
    if q: return q

    q = get_twelve_quote(symbol)
    if q: return q

    return get_yahoo_quote(symbol)


def get_history(symbol):

    h = get_fmp_history(symbol)
    if h: return h

    h = get_twelve_history(symbol)
    if h: return h

    return get_yahoo_history(symbol)

# =========================
# INDICATORS
# =========================
def sma(prices, period):
    if len(prices) < period:
        return sum(prices) / len(prices)
    return sum(prices[-period:]) / period


def rsi(prices):
    if len(prices) < 14:
        return 50

    gain, loss = 0, 0
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gain += diff
        else:
            loss += abs(diff)

    if loss == 0:
        return 100

    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =========================
# SCORE
# =========================
def score(q, prices):

    price = q.get("price", 0)
    if price == 0 or len(prices) < 30:
        return None

    r = rsi(prices)
    ma50 = sma(prices, min(50, len(prices)))
    ma200 = sma(prices, min(200, len(prices)))

    change = q.get("changesPercentage", 0)

    s = 50

    if ma50 > ma200:
        s += 20
    else:
        s -= 10

    if r < 30:
        s += 15
    elif r > 75:
        s -= 10

    if change > 2:
        s += 10

    s = max(0, min(100, round(s)))

    return s, r, ma50, ma200

# =========================
# TELEGRAM
# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# MAIN
# =========================
def main():

    print("🚀 STABLE V2 FINAL START")
    results = []

    for s in STOCKS:

        q = get_quote(s)
        p = get_history(s)

        if not q or not p:
            continue

        res = score(q, p)

        if not res:
            continue

        s_score, r, ma50, ma200 = res

        results.append({
            "symbol": s,
            "score": s_score,
            "rsi": round(r, 1),
            "price": q["price"]
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    if len(results) == 0:
        send("⚠️ No signals (ALL DATA FAILED)")
        return

    top = results[:10]

    msg = "🚀 STABLE V2 FINAL\n\n"

    for i, x in enumerate(top, 1):
        msg += f"{i}. {x['symbol']} ⭐ {x['score']}/100\n💰 {x['price']}\n📊 RSI: {x['rsi']}\n\n"

    send(msg)

if __name__ == "__main__":
    main()
