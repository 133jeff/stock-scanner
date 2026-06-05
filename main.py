import os
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
def safe_get(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
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
# FMP HISTORY
# =========================
def get_history_fmp(symbol):

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=200"
    data = safe_get(url)

    try:
        if data and "historical" in data:
            prices = [x["close"] for x in reversed(data["historical"]) if x.get("close")]
            if len(prices) > 50:
                return prices
    except:
        pass

    return []


# =========================
# TWELVE DATA HISTORY (FALLBACK)
# =========================
def get_history_twelve(symbol):

    if not TWELVE_KEY:
        return []

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=200&apikey={TWELVE_KEY}"
    data = safe_get(url)

    try:
        values = data.get("values", [])
        prices = [float(x["close"]) for x in reversed(values)]
        if len(prices) > 50:
            return prices
    except:
        pass

    return []


# =========================
# FINAL HISTORY (SMART SWITCH)
# =========================
def get_history(symbol):

    # 1. FMP
    prices = get_history_fmp(symbol)
    if len(prices) > 50:
        return prices

    # 2. Twelve Data
    prices = get_history_twelve(symbol)
    if len(prices) > 50:
        return prices

    return []


# =========================
# QUOTE (FMP ONLY)
# =========================
def get_quote(symbol):

    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
    data = safe_get(url)

    try:
        if isinstance(data, list) and len(data) > 0:
            q = data[0]
            return {
                "price": q.get("price") or 0,
                "changesPercentage": q.get("changesPercentage") or 0
            }
    except:
        pass

    return None


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
# SCORING V10 STABLE
# =========================
def score_v10(q, prices):

    price = q.get("price", 0)

    if price == 0 or len(prices) < 20:
        return 0, 50, "NO DATA", 0, 0, 0, 0, "NONE"

    rsi = calc_rsi(prices)

    ma50 = sma(prices, min(50, len(prices)))
    ma200 = sma(prices, min(200, len(prices)))

    change = float(q.get("changesPercentage") or 0)

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
        breakout = "BREAKOUT UP"
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

    print("TELEGRAM MESSAGE:")
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

    print("🚀 V10 STABLE START")
    print("TOTAL STOCKS:", len(STOCKS))

    results = []

    for s in STOCKS:

        print("CHECK:", s)

        q = get_quote(s)
        prices = get_history(s)

        print("PRICE LEN:", len(prices))

        if not q:
            continue

        if len(prices) < 20:
            continue

        score, rsi, trend, ma50, ma200, upside, risk, breakout = score_v10(q, prices)

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
        send("⚠️ No signals today")
        return

    msg = "🚀 V10 STABLE TOP 10\n\n"

    for i, x in enumerate(top, 1):

        msg += (
            f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
            f"💰 {x['price']}\n"
            f"📊 RSI: {x['rsi']}\n"
            f"📈 {x['trend']} (MA50:{x['ma50']} MA200:{x['ma200']})\n"
            f"🚀 UPSIDE: {x['upside']}/10\n"
            f"⚠️ RISK: {x['risk']}/10\n"
            f"💥 {x['breakout']}\n\n"
        )

    send(msg)


if __name__ == "__main__":
    main()
