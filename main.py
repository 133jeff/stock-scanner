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
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_KEY}&timeseries=30"
    data = safe_get(url)

    if not data or "historical" not in data:
        return []

    return [x["close"] for x in reversed(data["historical"])]

# =========================
# INDICATORS
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

def ema(prices, period=12):
    if len(prices) < period:
        return sum(prices) / len(prices)

    k = 2 / (period + 1)
    e = prices[0]

    for p in prices[1:]:
        e = p * k + e * (1 - k)

    return e

def macd(prices):
    if len(prices) < 26:
        return 0

    ema12 = ema(prices[-12:], 12)
    ema26 = ema(prices[-26:], 26)

    return ema12 - ema26

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

    score = 60  # baseline（保证不会空）

    trend = "SIDE"
    zone = "NONE"

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
            "rsi": round(rsi, 1),
            "trend": trend,
            "zone": zone
        })

# ⭐ 排序
results = sorted(results, key=lambda x: x["score"], reverse=True)

# ⭐ 动态TOP（最多10个）
topN = min(10, len(results))
top_list = results[:topN]

msg = "🚀 V5 TOP STOCKS\n\n"

for i, x in enumerate(top_list, 1):
    msg += (
        f"{i}. {x['symbol']} ⭐ {x['score']}/100\n"
        f"💰 {x['price']}\n"
        f"📊 RSI: {x['rsi']}\n"
        f"📈 {x['trend']}\n"
        f"🎯 {x['zone']}\n\n"
    )

send(msg)

# =========================
if __name__ == "__main__":
    main()
