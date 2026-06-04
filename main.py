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
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_KEY}"
    data = safe_get(url)
    return data[0] if isinstance(data, list) and len(data) > 0 else None

def get_history(symbol):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=250"
    data = safe_get(url)

    if not data or "historical" not in data:
        return []

    return [x["close"] for x in reversed(data["historical"])]

# =========================
# INDICATORS
# =========================
def calc_rsi(prices):
    if len(prices) < 15:
        return 50

    recent = prices[-15:]

    gains = 0
    losses = 0

    for i in range(1, len(recent)):
        diff = recent[i] - recent[i - 1]

        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)

    if losses == 0:
        return 100

    rs = gains / losses

    return round(
        100 - (100 / (1 + rs)),
        1
    )

# =========================
# SCORING (V5)
# =========================
def score_v5(q, prices):

    price = q.get("price")
    high = q.get("yearHigh")

    if price is None or high is None or not prices or high == 0:
        return 0, 50, "NO DATA", ""

    rsi = calc_rsi(prices)
    macd_val = macd(prices)

    change = q.get("changesPercentage") or q.get("changePercent") or 0

    try:
        change = float(change)
    except:
        change = 0

    score = 60

    trend = "SIDE"
    zone = "NONE"

    # ===== TREND =====
    if change > 3 and macd_val > 0:
        score += 25
        trend = "STRONG UP"

    elif change > 0 and macd_val > 0:
        score += 15
        trend = "UP"

    elif change < -3:
        score -= 10
        trend = "DOWN"

    # ===== PULLBACK =====
    dist = (price - high) / high

    if -0.20 < dist < -0.07 and rsi < 60:
        score += 25
        zone = "🟢 ACCUMULATION BUY"

    elif -0.30 < dist < -0.20:
        score += 15
        zone = "🟡 DEEP VALUE"

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

    # ===== MACD =====
    if macd_val > 0:
        score += 10
    else:
        score -= 5

    # 防止超过100
    score = max(
        0,
        min(100, round(score))
    )

    return score, rsi, trend, zone

    # =========================
    # TREND
    # =========================
    if change > 3 and macd_val > 0:
        score += 25
        trend = "STRONG UP"
    elif change > 0 and macd_val > 0:
        score += 15
        trend = "UP"
    elif change < -3:
        score -= 10
        trend = "DOWN"

    # =========================
    # PULLBACK BUY ZONE
    # =========================
    dist = (price - high) / high

    if -0.20 < dist < -0.07 and rsi < 60:
        score += 25
        zone = "🟢 ACCUMULATION BUY"
    elif -0.30 < dist < -0.20:
        score += 15
        zone = "🟡 DEEP VALUE"
    elif dist > -0.05:
        score -= 10
        zone = "🔴 OVERHEATED"

    # =========================
    # RSI
    # =========================
    if rsi < 30:
        score += 20
    elif rsi < 45:
        score += 10
    elif rsi > 75:
        score -= 10

    # =========================
    # MACD CONFIRM
    # =========================
    if macd_val > 0:
        score += 10
    else:
        score -= 5

    return score, rsi, trend, zone

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
    print("🚀 V5 SCANNER START")

    if not FMP_KEY:
        print("❌ Missing FMP_KEY")
        return

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

    # 🚨 空结果保护
    if len(results) == 0:
        send("⚠️ No signals today")
        return

    # ⭐ 排序（只做一次）
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    # ⭐ TOP10（动态）
    top_list = results[:10]

    msg = "🚀 V5 TOP STOCKS\n\n"

for i, x in enumerate(top_list, 1):

    try:
        change = float(x["change"])
    except:
        change = 0

    msg += (
        f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
        f"💰 {x['price']}\n"
        f"📉 {change:.2f}%\n"
        f"📊 RSI: {x['rsi']}\n"
        f"📈 {x['trend']}\n"
        f"🎯 {x['zone']}\n\n"
    )

    send(msg)

# =========================
if __name__ == "__main__":
    main()
