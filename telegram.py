import requests

BOT_TOKEN = "8822216767:AAHUqV8CYiFtKbogRyoNR-yBx9m5xP1ZSd8"
CHAT_ID = "7694683964"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)
