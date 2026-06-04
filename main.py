import os
import requests
from universe import get_universe

FMP_KEY = os.getenv("FMP_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STOCKS = get_universe()

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
def get_quote(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_KEY}"
    data = safe_get(url)
    return data[0] if isinstance(data, list) and len(data) > 0 else None

# =========================
def get_history(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=20"
    data = safe_get(url)

    if not data or "historical" not in data:
        return []

    return [x["close"] for x in reversed(data["historical"])]

# =========================
def calc_rsi(prices):
    if len(prices) < 15:
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
def score_v4(q, prices):
    price = q.get("price")
    high = q.get("yearHigh")

    if price is None or high is None or not prices or high == 0:
        return 0, 50, "NO DATA", ""

    rsi = calc_rsi(prices)

    change = q.get("changesPercentage") or q.get("changePercent") or 0

    score = 50

    if change > 2:
        score += 20
        trend = "STRONG UP"
    elif change > 0:
        score += 10
        trend = "UP"
    elif change < -2:
        score -= 10
        trend = "DOWN"
    else:
        trend = "SIDE"

    dist = (price - high) / high

    if -0.15 < dist < -0.05:
        score += 20
        zone = "🟢 BUY ZONE"
    elif dist < -0.15:
        score += 10
        zone = "🟡 WATCH"
    else:
        zone = "🔴 OVERHEATED"

    if rsi < 35:
        score += 20
    elif rsi < 45:
        score += 10
    elif rsi > 70:
        score -= 10

    return score, rsi, trend, zone

# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
def main():
    print("🚀 V4 SCANNER START")

    if not FMP_KEY:
        print("❌ Missing FMP_KEY")
        return

    results = []

    for s in STOCKS:
        q = get_quote(s)
        prices = get_history(s)

        if not q or not prices:
            continue

        score_val, rsi, trend, zone = score_v4(q, prices)

        results.append({
            "symbol": s,
            "score": score_val,
            "price": q.get("price"),
            "rsi": round(rsi, 1),
            "trend": trend,
            "zone": zone
        })

    top10 = sorted(results, key=lambda x: x["score"], reverse=True)[:10]

    if not top10:
        send("⚠️ No stocks passed V4 filter today")
        return

    msg = "🔥 V4 TOP 10 STOCKS\n\n"

    for i, x in enumerate(top10, 1):
        msg += (
            f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
            f"💰 Price: {x['price']}\n"
            f"📊 RSI: {x['rsi']}\n"
            f"📈 Trend: {x['trend']}\n"
            f"{x['zone']}\n\n"
        )

    send(msg)

# =========================
if __name__ == "__main__":
    main()
