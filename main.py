from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "8423808528:AAEDAlT_B_Y6xDwOytCRLYm0WcjMwBGFUsk"
CHAT_ID = "1307136561"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

@app.route("/")
def home():
    return "Whale Sniper Bot Aktif"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    signal = data.get("signal", "YOK")
    ticker = data.get("ticker", "YOK")
    tf = data.get("tf", "YOK")
    price = data.get("price", "YOK")

    message = f"""
🔥 WHALE SNIPER

📊 Coin: {ticker}
⏱ Zaman: {tf}
💰 Fiyat: {price}

⚡ Sinyal: {signal}
"""

    send_telegram(message)
    return "OK"
