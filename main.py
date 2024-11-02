import os
from dotenv import load_dotenv
import json
import urllib.request
import urllib.parse
import time
from pymongo import MongoClient
from datetime import datetime, timedelta

load_dotenv()

def send_message(token, chat_id, text):
    base_url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    data = urllib.parse.urlencode(data).encode()
    
    try:
        req = urllib.request.Request(base_url, data=data)
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def get_db_connection():
    try:
        client = MongoClient(os.getenv("DATABASE_URL"))
        db = client.PiProject  # Database name from your URL
        return db
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def check_and_send_messages():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    db = get_db_connection()
    
    if db is None:  # Changed from 'if not db:' to 'if db is None:'
        return
    
    try:
        # Get the collections we need
        users = db.users  # Collection for users
        message_tracking = db.message_tracking  # Collection for tracking messages
        
        # Find users who haven't been processed yet
        current_time = datetime.utcnow()
        ten_seconds_ago = current_time - timedelta(seconds=10)  # Changed from 5 hours to 10 seconds
        
        # Find users who were created more than 10 seconds ago and haven't received the message
        users_to_message = users.find({
            "createdAt": {"$lte": ten_seconds_ago},
            "telegramId": {
                "$nin": [
                    doc["telegram_id"] 
                    for doc in message_tracking.find({}, {"telegram_id": 1})
                ]
            }
        })
        
        # Send messages and update tracking
        for user in users_to_message:
            try:
                telegram_id = user.get("telegramId")
                if telegram_id:
                    send_message(
                        TOKEN,
                        telegram_id,
                        "Afraid of Scams? So can sell as low as 1Pi"
                    )
                    
                    # Record that we've sent the message
                    message_tracking.insert_one({
                        "telegram_id": telegram_id,
                        "sent_at": current_time
                    })
                    
                    print(f"Sent follow-up message to {telegram_id}")
                    
            except Exception as e:
                print(f"Error processing user {telegram_id}: {e}")
                
    except Exception as e:
        print(f"Error in check_and_send_messages: {e}")

def main():
    print("Follow-up message service started...")
    
    while True:
        try:
            check_and_send_messages()
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        # Check every 2 seconds instead of every minute
        time.sleep(2)  # Changed from 60 to 2 seconds

if __name__ == "__main__":
    main()
