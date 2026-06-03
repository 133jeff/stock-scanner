import os
import requests

set BOT_TOKEN=8822216767:AAF-TEbnyncD4pnys4lhu6IRPEyf74HuXwc
set CHAT_ID=7694683964

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)
