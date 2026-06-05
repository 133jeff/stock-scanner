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
# SAFE REQUEST
# =========================
def safe_get(url, headers=None):
    for _ in range(2):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            time.sleep(0.3)
    return None

# =========================
# DATA SOURCES
# =========================

# ---- FMP ----
def get_fmp_quote(symbol):
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
    data = safe_get(url)
    if isinstance(data, list) and len(data) > 0:
        q = data[0]
        return {
            "price": q.get("price") or 0,
            "changes": q.get("changesPercentage") or 0
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

# ---- TWELVE DATA ----
def get_twelve_quote(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_KEY}"
    data = safe_get(url)
    try:
        return {
            "price": float(data["price"]),
            "changes": 0
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

# ---- YAHOO ----
def get_yahoo_quote(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    data = safe_get(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        q = data["quoteResponse"]["result"][0]
        return {
            "price": q.get("regularMarketPrice") or 0,
            "changes": q.get("regularMarketChangePercent") or 0
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
# MASTER ENGINE
# =========================
def get_quote(symbol):
    return (
        get_fmp_quote(symbol)
        or get_twelve_quote(symbol)
        or get_yahoo_quote(symbol)
    )

def get_history(symbol):
    return (
        get_fmp_history(symbol)
        or get_twelve_history(symbol)
        or get_yahoo_history(symbol)
    )

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
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gain += diff
        else:
            loss += abs(diff)

    if loss == 0:
        return 100

    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =========================
# V7 SIGNAL ENGINE
# =========================

def momentum(prices):
    if len(prices) < 10:
        return 0
    return (prices[-1] - prices[-10]) / prices[-10]

def regime(ma50, ma200, r):
    if ma50 > ma200 and r > 55:
        return "RISK-ON"
    elif ma50 < ma200:
        return "RISK-OFF"
    return "NEUTRAL"

def breakout(price, ma50, ma200):
    if price > ma50 > ma200:
        return "STRONG UP"
    elif price < ma50 < ma200:
        return "DOWN"
    return "NONE"

def probability(r, ma50, ma200, m):
    p = 50
    if ma50 > ma200:
        p += 20
    else:
        p -= 20

    if r < 35:
        p += 15
    elif r > 70:
        p -= 15

    if m > 0:
        p += 10
    else:
        p -= 10

    return max(0, min(100, p))

def signal(prob, reg, brk):
    if reg == "RISK-OFF" and prob < 45:
        return "SELL"

    if brk == "STRONG UP" and prob > 65:
        return "BUY"

    if prob > 70:
        return "BUY"

    if prob < 40:
        return "SELL"

    return "HOLD"

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

    print("🚀 V7 SIGNAL SYSTEM START")

    results = []

    for s in STOCKS:

        q = get_quote(s)
        p = get_history(s)

        if not q or not p:
            continue

        price = q["price"]
        r = rsi(p)

        ma50 = sma(p, min(50, len(p)))
        ma200 = sma(p, min(200, len(p)))

        m = momentum(p)

        reg = regime(ma50, ma200, r)
        brk = breakout(price, ma50, ma200)
        prob = probability(r, ma50, ma200, m)
        action = signal(prob, reg, brk)

        results.append({
            "symbol": s,
            "price": price,
            "rsi": round(r, 1),
            "ma50": round(ma50, 2),
            "ma200": round(ma200, 2),
            "regime": reg,
            "breakout": brk,
            "prob": prob,
            "signal": action
        })

    results.sort(key=lambda x: x["prob"], reverse=True)

    top = results[:10]

    if len(top) == 0:
        send("⚠️ No signals")
        return

    msg = "🚀 V7 SIGNAL SYSTEM TOP 10\n\n"

    for i, x in enumerate(top, 1):

        msg += (
            f"{i}. {x['symbol']} {x['signal']} ({x['prob']}/100)\n"
            f"💰 {x['price']}\n"
            f"📊 RSI: {x['rsi']}\n"
            f"🌐 {x['regime']}\n"
            f"💥 {x['breakout']}\n\n"
        )

    send(msg)

if __name__ == "__main__":
    main()
