import requests
import time
from datetime import datetime

BOT_TOKEN = "8423808528:AAEDAlT_B_Y6xDwOytCRLYm0WcjMwBGFUsk"
CHAT_ID = "1307136561"

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def whale_check():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 2
    }

    data = requests.get(url, params=params).json()

    gems = []

    for coin in data:
        change_1h = coin.get("price_change_percentage_1h_in_currency", 0)
        change_24h = coin.get("price_change_percentage_24h", 0)
        volume = coin.get("total_volume", 0)

        score = 0

        if change_1h > 0.5:
            score += 30
        if change_24h > 5:
            score += 30
        if volume > 5000000:
            score += 40

        if score >= 80:
            gems.append((coin["symbol"].upper(), score, coin["current_price"]))

    return gems

def run():
    while True:
        gems = whale_check()

        if gems:
            msg = "🐋 WHALE SNIPER\n\n"
            msg += f"🕒 {datetime.now().strftime('%H:%M')}\n\n"

            for g in gems:
                msg += f"{g[0]} | Skor: {g[1]} | ${g[2]}\n"

            send(msg)

        time.sleep(900)

run()
