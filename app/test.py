import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = "8689214344:AAGjQ9vDouN1yxVkjq5TdEi_NfTrHs-dBFg" 
ALLOWED_ID = int(os.getenv('ALLOWED_TELEGRAM_ID'))  

last_update_id = 0 


def check_telegram():

    global last_update_id
    url = (f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
           f"?offset={last_update_id + 1}" # no idea what this does
    )

    response = requests.get(url).json()
    if not response["ok"]:
        return None

    results = response["result"]
    if not results:
        return None

    latest = results[-1]
    update_id = latest["update_id"]

    try:
        user_id = latest["message"]["from"]["id"]
        if user_id != ALLOWED_ID:
            print(f"Blocked User: {user_id}")
            return None
    
        return latest["message"]["text"]
    
    except:
        return None

if __name__ == "__main__": 
    while True:
        msg = check_telegram()
        if msg:
            print("New Telegram message:", msg)
        time.sleep(10)