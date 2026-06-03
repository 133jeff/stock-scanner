import time
from datetime import datetime
from fmp_api import get_quote
from scanner import score_stock
from universe import get_universe
from telegram import send_telegram

def run():
    print("🚀 RUN:", datetime.now())

    symbols = get_universe()
    results = []

    for s in symbols:
        print("Scanning:", s)

        q = get_quote(s)
        if not q:
            continue

        score = score_stock(q)

        results.append({
            "symbol": s,
            "price": q.get("price", 0),
            "change": q.get("changePercentage", 0),
            "score": score
        })

        time.sleep(0.2)

    results.sort(key=lambda x: x["score"], reverse=True)

    msg = "🚀 TOP PICKS\n\n"

    for r in results[:20]:
        line = f"{r['symbol']} {r['price']} {r['change']} {r['score']}"
        print(line)
        msg += line + "\n"

    send_telegram(msg)
    print("📩 SENT TELEGRAM")


# 🔁 关键：保持运行
while True:
    try:
        run()
    except Exception as e:
        print("ERROR:", e)

    time.sleep(60 * 60 * 48)
