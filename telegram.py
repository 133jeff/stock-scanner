import os
import requests

BOT_TOKEN = os.getenv("8822216767:AAGXS0_jB4o9B5e29nhIHBDgfwSziuXnFdA")
CHAT_ID = os.getenv("7694683964")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)
