import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

from fmp_api import get_quote
from scanner import score_stock
from universe import get_universe
from telegram import send_telegram

# =========================
# 🌐 保活服务器（解决 Render port error）
# =========================
def keep_alive():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()


# =========================
# 📊 主扫描逻辑
# =========================
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
                print("Symbol error:", s, e)
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


# =========================
# 🔁 云端持续运行（每2天）
# =========================
if __name__ == "__main__":
    while True:
        run()
        time.sleep(60 * 60 * 48)
