import time
from datetime import datetime

from fmp_api import get_quote
from scanner import score_stock
from universe import get_universe
from telegram import send_telegram


print("🚀 V6 SCANNER STARTED")


def run():
    print("\n==============================")
    print("RUN:", datetime.now())
    print("==============================")

    symbols = get_universe()[:10]  # 🔥 控制10只，防FMP爆
    results = []

    for s in symbols:
        print("Scanning:", s)

        try:
            q = get_quote(s)

            if not q or q == {}:
                print("SKIP EMPTY:", s)
                continue

            score = score_stock(q)

            results.append({
                "symbol": s,
                "price": q.get("price", 0),
                "score": score
            })

            time.sleep(1.2)  # 🔥 防限流

        except Exception as e:
            print("ERROR:", s, e)
            continue

    results.sort(key=lambda x: x["score"], reverse=True)

    top = results[:5]

    if top:
        msg = "🔥 TOP STOCKS:\n"
        for r in top:
            msg += f"{r['symbol']} | {r['price']} | score:{r['score']}\n"

        send_telegram(msg)
        print("TELEGRAM SENT")


if __name__ == "__main__":
    run()
