import time
from datetime import datetime
from fmp_api import get_quote, get_ratios, get_growth
from scanner import score_stock
from universe import get_universe
from telegram import send_telegram

def run_scan():
    print("🚀 RUNNING SCAN:", datetime.now())

    symbols = get_universe()
    results = []

    for s in symbols:
        print("Scanning:", s)

        q = get_quote(s)
        if not q:
            continue

        r = get_ratios(s)
        g = get_growth(s)

        data = {}
        data.update(q)
        if r:
            data.update(r)
        if g:
            data.update(g)

        score = score_stock(data)

        results.append({
            "symbol": s,
            "price": data.get("price", 0),
            "change": data.get("changePercentage", 0),
            "score": score
        })

        time.sleep(0.3)

    results.sort(key=lambda x: x["score"], reverse=True)

    msg = "🚀 TOP PICKS\n\n"
    for r in results[:20]:
        line = f"{r['symbol']} {r['price']} {r['change']} {r['score']}"
        msg += line + "\n"
        print(line)

    send_telegram(msg)
    print("📩 SENT TELEGRAM")


# =========================
# 🔁 关键：保持运行不中断
# =========================
while True:
    try:
        run_scan()
    except Exception as e:
        print("ERROR:", e)

    # 每2天运行一次
    time.sleep(60 * 60 * 48)