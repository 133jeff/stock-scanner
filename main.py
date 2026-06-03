import time
from datetime import datetime
from fmp_api import get_quote
from scanner import score_stock
from universe import get_universe
from telegram import send_telegram

def run():
    print("🚀 RUN START:", datetime.now())

    try:
        symbols = get_universe()
        results = []

        for s in symbols:
            try:
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

            except Exception as e:
                print("Skip symbol error:", s, e)
                continue

        results.sort(key=lambda x: x["score"], reverse=True)

        msg = "🚀 TOP PICKS\n\n"

        for r in results[:20]:
            line = f"{r['symbol']} {r['price']} {r['change']} {r['score']}"
            print(line)
            msg += line + "\n"

        send_telegram(msg)
        print("📩 TELEGRAM SENT")

    except Exception as e:
        print("RUN ERROR:", e)


# 🔁 保证永远不退出
while True:
    run()
    time.sleep(60 * 60 * 48)  # 每2天
