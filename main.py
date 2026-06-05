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
# 1️⃣ FMP HISTORY (PRIMARY)
# =========================
def get_history_fmp(symbol):
    if not FMP_KEY:
        return []

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=500"
    data = safe_get(url)

    try:
        if data and "historical" in data:
            prices = [x["close"] for x in reversed(data["historical"]) if x.get("close")]
            if len(prices) > 20:
                return prices
    except:
        pass

    return []


# =========================
# 2️⃣ TWELVE DATA (SECONDARY)
# =========================
def get_history_twelve(symbol):
    if not TWELVE_KEY:
        return []

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=500&apikey={TWELVE_KEY}"
    data = safe_get(url)

    try:
        values = data.get("values", [])
        prices = [float(x["close"]) for x in reversed(values)]

        if len(prices) > 20:
            return prices
    except:
        pass

    return []


# =========================
# 3️⃣ YAHOO (LAST RESORT)
# =========================
def get_history_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2y&interval=1d"
    data = safe_get(url)

    try:
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        prices = [x for x in closes if isinstance(x, (int, float))]

        if len(prices) > 20:
            return prices
    except:
        pass

    return []


# =========================
# FINAL HISTORY ENGINE
# =========================
def get_history(symbol):

    # FMP
    prices = get_history_fmp(symbol)
    if len(prices) > 20:
        return prices

    # TwelveData
    prices = get_history_twelve(symbol)
    if len(prices) > 20:
        return prices

    # Yahoo fallback
    prices = get_history_yahoo(symbol)
    if len(prices) > 20:
        return prices

    # ❗最后保护（不会用来误导趋势，只避免崩溃）
    return []


# =========================
# QUOTE (FMP + SAFE)
# =========================
def get_quote(symbol):

    if FMP_KEY:
        url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
        data = safe_get(url)

        try:
            if isinstance(data, list) and len(data) > 0:
                q = data[0]
                return {
                    "price": float(q.get("price") or 0),
                    "changesPercentage": float(q.get("changesPercentage") or 0)
                }
        except:
            pass

    return {"price": 0, "changesPercentage": 0}


# =========================
# INDICATORS (SAFE VERSION)
# =========================
def sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calc_rsi(prices):
    if len(prices) < 15:
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
# SCORING V12 (CLEAN + SAFE)
# =========================
def score_v12(q, prices):

    price = q.get("price", 0)

    # ❗必须有真实价格或历史最后价
    if price == 0 and len(prices) > 0:
        price = prices[-1]

    rsi = calc_rsi(prices)

    ma50 = sma(prices, 50)
    ma200 = sma(prices, 200)

    change = float(q.get("changesPercentage") or 0)

    score = 60
    trend = "NO TREND"

    # ===== TREND =====
    if ma50 and ma200:
        if ma50 > ma200:
            score += 20
            trend = "BULL"
        else:
            score -= 10
            trend = "BEAR"
    else:
        score -= 5
        trend = "WEAK DATA"

    # ===== MOMENTUM =====
    if change > 3:
        score += 15
    elif change > 0:
        score += 8
    elif change < -3:
        score -= 10

    # ===== RSI =====
    if rsi < 30:
        score += 20
    elif rsi < 45:
        score += 10
    elif rsi > 75:
        score -= 15

    # ===== BREAKOUT =====
    breakout = "NONE"

    if ma50 and ma200:
        if price > ma50 > ma200:
            score += 15
            breakout = "UP"
        elif price < ma50 < ma200:
            score -= 10
            breakout = "DOWN"

    # ===== UPSIDE =====
    if ma50 and ma200:
        if ma50 > ma200 and rsi < 60:
            upside = 8
        elif ma50 > ma200:
            upside = 6
        elif rsi < 40:
            upside = 5
        else:
            upside = 3
    else:
        upside = 3

    # ===== RISK =====
    risk = 0
    if ma50 and ma200 and ma50 < ma200:
        risk += 4
    if rsi > 75:
        risk += 3
    if change < -3:
        risk += 2

    risk = min(10, risk)

    score = max(0, min(100, round(score)))

    return score, rsi, trend, ma50 or 0, ma200 or 0, upside, risk, breakout


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

    print("🚀 V12 FINAL START")
    print("TOTAL STOCKS:", len(STOCKS))

    results = []

    for s in STOCKS:

        q = get_quote(s)
        prices = get_history(s)

        if len(prices) < 20:
            continue

        score, rsi, trend, ma50, ma200, upside, risk, breakout = score_v12(q, prices)

        results.append({
            "symbol": s,
            "score": score,
            "price": q.get("price", 0),
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

    msg = "🚀 V12 FINAL TOP 10\n\n"

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
