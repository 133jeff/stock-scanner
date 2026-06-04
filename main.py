import os
import requests

FMP_KEY = os.getenv("FMP_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STOCKS = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","AVGO","TSLA"]

def get_quote(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_KEY}"
    r = requests.get(url).json()
    return r[0] if r else None

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def score(q):
    price = q["price"]
    high = q["yearHigh"]
    dist = (price - high) / high

    score = 0

    if -0.15 < dist < -0.05:
        score += 30
    elif dist > 0:
        score += 5

    if q.get("changesPercentage", 0) > 1:
        score += 20

    return score, dist

def main():
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
                "price": q["price"],
                "dist": round(dist*100,2)
            })

    top10 = sorted(results, key=lambda x: x["score"], reverse=True)[:10]

    msg = "🔥 V3 TOP 10\n\n"

    for i, x in enumerate(top10, 1):
        msg += f"{i}. {x['symbol']} — {x['score']}/100\n💰 {x['price']}\n📉 {x['dist']}%\n\n"

    send(msg)

if __name__ == "__main__":
    main()
