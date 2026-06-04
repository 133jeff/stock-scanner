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
            print("HTTP ERROR:", r.status_code)
            return None
        return r.json()
    except Exception as e:
        print("REQUEST ERROR:", e)
        return None

# =========================
def get_quote(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_KEY}"
    r = safe_get(url)

    print("RAW:", symbol, r)

    if isinstance(r, list) and len(r) > 0:
        return r[0]

    return None

# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    print("Telegram:", res.text)

# =========================
# =========================
# V4 TECH INDICATORS
# =========================

def calc_rsi(prices):
    if len(prices) < 15:
        return 50

    gains = 0
    losses = 0

    for i in range(1, 15):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)

    if losses == 0:
        return 100

    rs = gains / losses
    return 100 - (100 / (1 + rs))


def get_history(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=20"
    data = safe_get(url)

    if not data or "historical" not in data:
        return []

    return [x["close"] for x in data["historical"]]
    
# =========================
def score_v4(q, prices):
    price = q.get("price")
    high = q.get("yearHigh")

    if price is None or high is None or not prices or high == 0:
        return 0, 50, "NO DATA", ""

    # ===== RSI =====
    rsi = calc_rsi(prices)

    # ===== trend =====
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

    # ===== pullback =====
    dist = (price - high) / high

    if -0.15 < dist < -0.05:
        score += 20
        zone = "🟢 BUY ZONE"
    elif dist < -0.15:
        score += 10
        zone = "🟡 WATCH"
    else:
        zone = "🔴 OVERHEATED"

    # ===== RSI scoring =====
    if rsi < 35:
        score += 20
    elif rsi < 45:
        score += 10
    elif rsi > 70:
        score -= 10

    return score, rsi, trend, zone

# =========================
def main():
    print("DEBUG TOKEN:", TELEGRAM_TOKEN)
    print("DEBUG CHAT:", CHAT_ID)

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

    msg = "🔥 V4 TOP 10\n\n"

    for i, x in enumerate(top10, 1):
        msg += (
            f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
            f"💰 {x['price']}\n"
            f"📊 RSI: {x['rsi']}\n"
            f"📈 {x['trend']}\n"
            f"{x['zone']}\n\n"
        )

    send(msg)

if __name__ == "__main__":
    main()
