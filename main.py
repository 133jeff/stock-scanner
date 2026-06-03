import time
from fmp_api import get_quote, get_ratios, get_growth
from scanner import score_stock
from universe import get_universe
from telegram import send_telegram

print("🚀 V5 + TELEGRAM SCANNER RUNNING")

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

    # 防止API限流
    time.sleep(0.3)

results.sort(key=lambda x: x["score"], reverse=True)

print("\n🔥 TOP 20 PICKS:\n")

msg = "🚀 TOP 20 STOCK PICKS\n\n"

for r in results[:20]:
    line = f"{r['symbol']}  {r['price']}  {r['change']}  {r['score']}"
    print(line)
    msg += line + "\n"

# ===== SEND TO TELEGRAM =====
send_telegram(msg)

print("\n📩 Sent to Telegram!")