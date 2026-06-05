import os
import requests
from universe import get_universe

# =========================
# ENV
# =========================
FMP_KEY = os.getenv("FMP_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STOCKS = get_universe()

# =========================
# SAFE REQUEST (FINAL)
# =========================
def safe_get(url):

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            return None

        try:
            return r.json()
        except:
            return None

    except:
        return None


# =========================
# DATA QUALITY CHECK
# =========================
def is_valid_price(p):
    return p is not None and p > 0 and isinstance(p, (int, float))


# =========================
# FMP + YAHOO QUOTE
# =========================
def get_quote(symbol):

    # ===== FMP =====
    try:
        url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
        data = safe_get(url)
        print("FMP RAW:", data)

        if isinstance(data, list) and len(data) > 0:
            q = data[0]
            price = q.get("price")

            if is_valid_price(price):
                return {
                    "price": float(price),
                    "changesPercentage": float(q.get("changesPercentage") or 0)
                }
    except:
        pass

    # ===== YAHOO =====
    return get_quote_yahoo(symbol)


def get_quote_yahoo(symbol):

    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    data = safe_get(url)
    print("YAHOO QUOTE RAW:", data)

    try:
        q = data["quoteResponse"]["result"][0]

        price = q.get("regularMarketPrice")

        return {
            "price": float(price) if is_valid_price(price) else 0,
            "changesPercentage": float(q.get("regularMarketChangePercent") or 0)
        }

    except:
        return {"price": 0, "changesPercentage": 0}


# =========================
# HISTORY (FINAL SAFE)
# =========================
def get_history(symbol):

    # ===== FMP =====
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=200"
        data = safe_get(url)

        if data and "historical" in data:
            prices = [
                float(x["close"])
                for x in reversed(data["historical"])
                if is_valid_price(x.get("close"))
            ]

            if len(prices) >= 60:
                return prices
    except:
        pass

    # ===== YAHOO =====
    return get_history_yahoo(symbol)


def get_history_yahoo(symbol):

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d"
    data = safe_get(url)
    print("YAHOO HISTORY RAW:", data)

    try:
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

        prices = [float(x) for x in closes if is_valid_price(x)]

        # 最低保证
        if len(prices) < 20:
            return []

        return prices[-250:]

    except:
        return []


# =========================
# INDICATORS
# =========================
def sma(prices, period):

    if len(prices) == 0:
        return 0

    if len(prices) < period:
        return sum(prices) / len(prices)

    return sum(prices[-period:]) / period


def calc_rsi(prices):

    if len(prices) < 14:
        return 50

    gains, losses = 0, 0

    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)

    if losses == 0:
        return 100

    rs = gains / losses
    return 100 - (100 / (1 + rs))


# =========================
# SCORING (FINAL LOGIC)
# =========================
def score_v7(q, prices):

    price = q.get("price", 0)
    change = q.get("changesPercentage", 0)

    if price <= 0 or len(prices) < 30:
        return 0, 50, "NO DATA", 0, 0, 0, 0, "NONE"

    rsi = calc_rsi(prices)

    ma50 = sma(prices, 50)
    ma200 = sma(prices, 200)

    score = 60
    trend = "SIDE"

    # TREND
    if ma50 > ma200:
        score += 20
        trend = "BULL"
    else:
        score -= 10
        trend = "BEAR"

    # MOMENTUM
    if change > 3:
        score += 15
    elif change > 0:
        score += 8
    elif change < -3:
        score -= 10

    # RSI
    if rsi < 30:
        score += 20
    elif rsi < 45:
        score += 10
    elif rsi > 75:
        score -= 15

    # BREAKOUT
    breakout = "NONE"

    if price > ma50 > ma200:
        score += 15
        breakout = "BREAKOUT"
    elif price < ma50 < ma200:
        score -= 10
        breakout = "WEAK"

    # UPSIDE
    if ma50 > ma200 and rsi < 60:
        upside = 8
    elif ma50 > ma200:
        upside = 6
    elif rsi < 40:
        upside = 5
    else:
        upside = 3

    # RISK
    risk = 0
    if ma50 < ma200:
        risk += 4
    if rsi > 75:
        risk += 3
    if change < -3:
        risk += 2

    risk = min(10, risk)

    score = max(0, min(100, round(score)))

    return score, rsi, trend, ma50, ma200, upside, risk, breakout


# =========================
# TELEGRAM
# =========================
def send(msg):

    print(msg)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


# =========================
# MAIN
# =========================
def main():

    print("🚀 V7 PRO FINAL START")
    print("TOTAL STOCKS:", len(STOCKS))

    results = []

    for s in STOCKS:

        q = get_quote(s)
        prices = get_history(s)

        if not q:
            q = {"price": 0, "changesPercentage": 0}

        if not prices:
            continue   # ❗关键：不要假数据污染

        score, rsi, trend, ma50, ma200, upside, risk, breakout = score_v7(q, prices)

        results.append({
            "symbol": s,
            "score": score,
            "price": q["price"],
            "rsi": round(rsi, 1),
            "trend": trend,
            "ma50": round(ma50, 2),
            "ma200": round(ma200, 2),
            "upside": upside,
            "risk": risk,
            "breakout": breakout
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    top = results[:10]

    if len(top) == 0:
        send("⚠️ No valid signals (data issue)")
        return

    msg = "🚀 V7 PRO FINAL TOP 10\n\n"

    for i, x in enumerate(top, 1):

        msg += (
            f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
            f"💰 {x['price']}\n"
            f"📊 RSI: {x['rsi']}\n"
            f"📈 {x['trend']} (50:{x['ma50']} 200:{x['ma200']})\n"
            f"🚀 UPSIDE: {x['upside']}/10\n"
            f"⚠️ RISK: {x['risk']}/10\n"
            f"💥 {x['breakout']}\n\n"
        )

    send(msg)


if __name__ == "__main__":
    main()
