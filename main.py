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
# SAFE REQUEST (HARDENED)
# =========================
def safe_get(url):

    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )

        if r.status_code != 200:
            return None

        try:
            return r.json()
        except:
            return None

    except:
        return None


# =========================
# FMP + FALLBACK
# =========================
def get_quote(symbol):

    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
    data = safe_get(url)

    if isinstance(data, list) and len(data) > 0:
        q = data[0]
        price = q.get("price")

        if price:
            return {
                "price": float(price),
                "changesPercentage": float(q.get("changesPercentage") or 0)
            }

    return {"price": 0, "changesPercentage": 0}


def get_history(symbol):

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=200"
    data = safe_get(url)

    try:
        if data and "historical" in data:

            prices = [
                float(x["close"])
                for x in reversed(data["historical"])
                if x.get("close")
            ]

            if len(prices) >= 30:
                return prices

    except:
        pass

    return []


# =========================
# INDICATORS (SAFE)
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
# SCORE ENGINE V8
# =========================
def score_v8(q, prices):

    price = q.get("price", 0)

    if price <= 0 or len(prices) < 20:
        return 0, 50, "NO DATA", 0, 0, 0, 0, "NONE"

    rsi = calc_rsi(prices)

    ma20 = sma(prices, min(20, len(prices)))
    ma50 = sma(prices, min(50, len(prices)))

    change = q.get("changesPercentage", 0)

    score = 50
    trend = "SIDE"

    # TREND
    if ma20 > ma50:
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

    breakout = "NONE"
    if price > ma20 > ma50:
        score += 10
        breakout = "BREAKOUT"

    upside = 6 if ma20 > ma50 else 4

    risk = 0
    if ma20 < ma50:
        risk += 4
    if rsi > 75:
        risk += 3

    risk = min(10, risk)

    score = max(1, min(100, round(score)))

    return score, rsi, trend, ma20, ma50, upside, risk, breakout


# =========================
# TELEGRAM
# =========================
def send(msg):

    print(msg)

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


# =========================
# MAIN
# =========================
def main():

    print("🚀 V8 PRO FINAL START")
    print("TOTAL STOCKS:", len(STOCKS))

    results = []

    for s in STOCKS:

        q = get_quote(s)
        prices = get_history(s)

        if not prices:
            continue

        score, rsi, trend, ma20, ma50, upside, risk, breakout = score_v8(q, prices)

        results.append({
            "symbol": s,
            "score": score,
            "price": q["price"],
            "rsi": round(rsi, 1),
            "trend": trend,
            "ma20": round(ma20, 2),
            "ma50": round(ma50, 2),
            "upside": upside,
            "risk": risk,
            "breakout": breakout
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    top = results[:10]

    if len(top) == 0:
        send("⚠️ No signals (data unavailable)")
        return

    msg = "🚀 V8 PRO FINAL TOP 10\n\n"

    for i, x in enumerate(top, 1):

        msg += (
            f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
            f"💰 {x['price']}\n"
            f"📊 RSI: {x['rsi']}\n"
            f"📈 {x['trend']} (20:{x['ma20']} 50:{x['ma50']})\n"
            f"🚀 UPSIDE: {x['upside']}/10\n"
            f"⚠️ RISK: {x['risk']}/10\n"
            f"💥 {x['breakout']}\n\n"
        )

    send(msg)


if __name__ == "__main__":
    main()
