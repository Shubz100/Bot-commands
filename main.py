import os
from dotenv import load_dotenv
import json
import urllib.request
import urllib.parse
import time

load_dotenv()

def send_message(token, chat_id, text, inline_keyboard=None):
    base_url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    if inline_keyboard:
        data["reply_markup"] = json.dumps(inline_keyboard)
    
    data = urllib.parse.urlencode(data).encode()
    
    req = urllib.request.Request(base_url, data=data)
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode())

def get_updates(token, offset=None):
    base_url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    response = urllib.request.urlopen(url)
    return json.loads(response.read().decode())

def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBAPP_URL = "https://voicexcopy.vercel.app/"
    
    keyboard = {
        "inline_keyboard": [[{
            "text": "Open Web App",
            "web_app": {"url": WEBAPP_URL}
        }]]
    }
    
    print("Bot started...")
    offset = None
    
    while True:
        try:
            updates = get_updates(TOKEN, offset)
            
            for update in updates["result"]:
                offset = update["update_id"] + 1
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    message_text = update["message"]["text"]
                    
                    if message_text == "/start":
                        send_message(
                            TOKEN,
                            chat_id,
                            "Welcome! Click the button below to open the web app:",
                            keyboard
                        )
                        
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(5)
            continue
            
        time.sleep(1)

if __name__ == "__main__":
    main()
