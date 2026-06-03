import requests

BOT_TOKEN = "8822216767:AAG5jWmhp10FDxY_ohpwe3IlxTxjPyaLK28"
CHAT_ID = "7694683964"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    res = requests.post(url, data=payload)
    print(res.text)

send_telegram("test message")
