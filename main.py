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
# SAFE REQUEST
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
# FMP DATA
# =========================
def get_quote(symbol):
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
    data = safe_get(url)

    if isinstance(data, list) and len(data) > 0:
        return data[0]

    return get_quote_yahoo(symbol)


def get_history(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=200"
    data = safe_get(url)

    if data and "historical" in data:
        return [x["close"] for x in reversed(data["historical"])]

    return get_history_yahoo(symbol)

# =========================
# YAHOO FALLBACK
# =========================
def get_quote_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    data = safe_get(url)

    try:
        q = data["quoteResponse"]["result"][0]
        return {
            "price": q.get("regularMarketPrice") or 0,
            "yearHigh": q.get("fiftyTwoWeekHigh") or 0,
            "changesPercentage": q.get("regularMarketChangePercent") or 0,
        }
    except:
        return None


def get_history_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=6mo&interval=1d"
    data = safe_get(url)

    try:
        result = data["chart"]["result"][0]
        closes = result["indicators"]["quote"][0].get("close", [])
        return [x for x in closes if isinstance(x, (int, float))]
    except:
        return []

# =========================
# INDICATORS
# =========================
def sma(prices, period):
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
# SCORING V6
# =========================
def score_v6(q, prices):

    price = q.get("price")
    if not price or len(prices) < 50:
        return 0, 50, "NO DATA", 0, 0

    rsi = calc_rsi(prices)

    ma50 = sma(prices, 50)
    ma200 = sma(prices, 200)

    change = float(q.get("changesPercentage") or 0)

    score = 60
    trend = "SIDE"

    # =========================
    # TREND (MA STRUCTURE)
    # =========================
    if ma50 > ma200:
        score += 20
        trend = "BULL TREND"
    else:
        score -= 10
        trend = "BEAR / SIDE"

    # =========================
    # MOMENTUM
    # =========================
    if change > 3:
        score += 15
    elif change > 0:
        score += 8
    elif change < -3:
        score -= 10

    # =========================
    # RSI
    # =========================
    if rsi < 30:
        score += 20
    elif rsi < 45:
        score += 10
    elif rsi > 75:
        score -= 15

    # =========================
    # BREAKOUT LOGIC
    # =========================
    breakout = 0

    if price > ma50 > ma200:
        score += 15
        breakout = 1
    elif price < ma50 < ma200:
        score -= 15
        breakout = -1

    # =========================
    # UPSIDE SCORE
    # =========================
    upside_score = 0
    if ma50 > ma200 and rsi < 60:
        upside_score = 8
    elif ma50 > ma200:
        upside_score = 6
    elif rsi < 40:
        upside_score = 5
    else:
        upside_score = 3

    # =========================
    # RISK SCORE
    # =========================
    risk_score = 0
    if ma50 < ma200:
        risk_score += 4
    if rsi > 75:
        risk_score += 3
    if change < -3:
        risk_score += 2

    risk_score = min(10, risk_score)

    score = max(0, min(100, round(score)))

    return score, rsi, trend, ma50, ma200, upside_score, risk_score

# =========================
# TELEGRAM
# =========================
def send(msg):
    if len(msg) > 3500:
        msg = msg[:3500] + "\n...(TRUNCATED)"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# MAIN
# =========================
def main():

    print("🚀 V6 SCANNER START")
    print("TOTAL STOCKS:", len(STOCKS))

    results = []

    for s in STOCKS:

        q = get_quote(s)
        prices = get_history(s)

        if not q or not prices:
            continue

        score, rsi, trend, ma50, ma200, upside, risk = score_v6(q, prices)

        results.append({
            "symbol": s,
            "score": score,
            "price": q.get("price"),
            "rsi": round(rsi, 1),
            "trend": trend,
            "ma50": round(ma50, 2),
            "ma200": round(ma200, 2),
            "upside": upside,
            "risk": risk
        })

    if len(results) == 0:
        send("⚠️ No signals today")
        return

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    top_list = results[:10]

    msg = "🚀 V6 STOCK SCANNER\n\n"

    for i, x in enumerate(top_list, 1):

        msg += (
            f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
            f"💰 {x['price']}\n"
            f"📊 RSI: {x['rsi']}\n"
            f"📈 {x['trend']} (MA50:{x['ma50']} MA200:{x['ma200']})\n"
            f"🚀 UPSIDE: {x['upside']}/10\n"
            f"⚠️ RISK: {x['risk']}/10\n\n"
        )

    send(msg)

# =========================
if __name__ == "__main__":
    main()
