import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

from fmp_api import get_quote
from scanner import score_stock
from universe import get_universe
from telegram import send_telegram


def keep_alive():
    class Handler(BaseHTTPRequestHandler):

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()


def run():
    print("=" * 50)
    print("🚀 RUN ENTERED", datetime.now())
    print("=" * 50)

    symbols = get_universe()
    print("UNIVERSE LOADED:", len(symbols))

    results = []

    for s in symbols[:5]:
        print("Scanning:", s)

        q = get_quote(s)
        print("QUOTE:", q)

        if not q:
            continue

        score = score_stock(q)

        results.append({
            "symbol": s,
            "price": q.get("price", 0),
            "score": score
        })

    print("DONE LOOP")

    if results:
        send_telegram("TEST OK: " + str(results))
        print("TELEGRAM SENT")


if __name__ == "__main__":
    print("🔥 MAIN STARTED")

    threading.Thread(target=keep_alive, daemon=True).start()

    # 先立即执行一次
    run()

    # 再进入循环
    while True:
        print("⏰ Sleeping 48 hours...")
        time.sleep(60 * 60 * 48)
        run()
