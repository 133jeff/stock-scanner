import os
import requests

BOT_TOKEN = os.getenv("8822216767:AAENHmFiC2zWOIUUzl0DaGIwhyVKKuf0EtE")
CHAT_ID = os.getenv("7694683964")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    res = requests.post(url, data=payload)
    print(res.text)

send_telegram("hello from github actions")
