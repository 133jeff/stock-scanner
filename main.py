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
def score(q):
    if not q:
        return 0, 0

    price = q.get("price")
    high = q.get("yearHigh")

    if not price or not high:
        return 0, 0

    dist = (price - high) / high

    score = 0

    # 回调区间
    if -0.15 < dist < -0.05:
        score += 30
    elif dist > 0:
        score += 5

    # 动量（兼容字段）
    change = q.get("changesPercentage") or q.get("changePercent") or 0

    if change > 1:
        score += 20

    return score, dist

# =========================
def main():
    print("DEBUG TOKEN:", TELEGRAM_TOKEN)
    print("DEBUG CHAT:", CHAT_ID)
    
    if not FMP_KEY:
        print("❌ FMP_KEY missing")
        return

    results = []

    for s in STOCKS:
        q = get_quote(s)

        if not q:
            continue

        score_val, dist = score(q)

        if score_val >= 40:
            results.append({
                "symbol": s,
                "score": score_val,
                "price": q.get("price"),
                "dist": round(dist * 100, 2)
            })

    top10 = sorted(results, key=lambda x: x["score"], reverse=True)[:10]

    if not top10:
        send("⚠️ No stocks passed filter today")
        return

    msg = "🔥 V3 TOP 10 STOCKS\n\n"

    for i, x in enumerate(top10, 1):
        msg += f"{i}. {x['symbol']} — {x['score']}/100\n💰 {x['price']}\n📉 {x['dist']}%\n\n"

    send(msg)

if __name__ == "__main__":
    main()
