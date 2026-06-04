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
# DATA
# =========================
def get_quote(symbol):
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_KEY}"
    data = safe_get(url)

    print("QUOTE DEBUG:", symbol, data)

    return data[0] if isinstance(data, list) and len(data) > 0 else None


def get_history(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=60"
    data = safe_get(url)

    if not data or "historical" not in data:
        print("HISTORY DEBUG:", symbol, 0)
        return []

    print("HISTORY DEBUG:", symbol, len(data["historical"]))

    # ⭐⭐⭐ 这里就是关键 RETURN
    return [x["close"] for x in reversed(data["historical"])]

# =========================
# RSI
# =========================
def calc_rsi(prices):
    if len(prices) < 14:
        return 50

    gains = 0
    losses = 0

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
# SCORE
# =========================
def score_v5(q, prices):
    price = q.get("price")
    high = q.get("yearHigh")

    if price is None or high is None or not prices or high == 0:
        return 0, 50, "NO DATA", ""

    rsi = calc_rsi(prices)
    change = q.get("changesPercentage") or 0

    try:
        change = float(change)
    except:
        change = 0

    score = 60
    trend = "SIDE"
    zone = "NONE"

    # ===== TREND =====
    if change > 3:
        score += 20
        trend = "STRONG UP"
    elif change > 0:
        score += 10
        trend = "UP"
    elif change < -3:
        score -= 10
        trend = "DOWN"

    # ===== PULLBACK =====
    dist = (price - high) / high

    if -0.20 < dist < -0.07 and rsi < 60:
        score += 20
        zone = "🟢 ACCUMULATION"
    elif -0.30 < dist < -0.20:
        score += 10
        zone = "🟡 WATCH"
    elif dist > -0.05:
        score -= 10
        zone = "🔴 OVERHEATED"

    # ===== RSI =====
    if rsi < 30:
        score += 20
    elif rsi < 45:
        score += 10
    elif rsi > 75:
        score -= 10

    return score, rsi, trend, zone

# =========================
# TELEGRAM
# =========================
def send(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# MAIN
# =========================
def main():
    print("🚀 V5 SCANNER START")
    print("TOTAL STOCKS:", len(STOCKS))

    results = []

    for s in STOCKS:
        q = get_quote(s)
        prices = get_history(s)

        if not q or not prices or len(prices) < 5:
            continue

        score_val, rsi, trend, zone = score_v5(q, prices)

        results.append({
            "symbol": s,
            "score": score_val,
            "price": q.get("price"),
            "change": q.get("changesPercentage") or 0,
            "rsi": round(rsi, 1),
            "trend": trend,
            "zone": zone
        })

    # =========================
    # FALLBACK（永远不空）
    # =========================
    if len(results) == 0:
        print("⚠️ fallback triggered")

        for s in STOCKS[:10]:
            q = get_quote(s)

            if not q:
                continue

            results.append({
                "symbol": s,
                "score": 50,
                "price": q.get("price"),
                "change": q.get("changesPercentage") or 0,
                "rsi": 50,
                "trend": "NO DATA",
                "zone": "⚪ BASIC"
            })

    # =========================
    # SORT + TOP10
    # =========================
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    top_list = results[:10]

    msg = "🚀 V5 STOCK SCANNER TOP\n\n"

    for i, x in enumerate(top_list, 1):
        msg += (
            f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
            f"💰 {x['price']}\n"
            f"📉 {x['change']}%\n"
            f"📊 RSI: {x['rsi']}\n"
            f"📈 {x['trend']}\n"
            f"🎯 {x['zone']}\n\n"
        )

    send(msg)

# =========================
if __name__ == "__main__":
    main()
