import requests

BOT_TOKEN = "8822216767:AAGe6EHNyJLD3gBGSbX7K09FxMZ6nwEcVPk"
CHAT_ID = "7694683964"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)