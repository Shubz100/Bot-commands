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
        return client.PiProject  # Database name from your URL
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def check_and_send_messages(db):
    if db is None:  # Proper way to check if db is None
        print("Database connection is not available")
        return
    
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Telegram bot token not found")
        return
        
    try:
        # Get the collections we need
        users = db.users  # Collection for users
        message_tracking = db.message_tracking  # Collection for tracking messages
        
        # Get current time
        current_time = datetime.utcnow()
        sixty_seconds_ago = current_time - timedelta(seconds=60)
        
        # Get list of already messaged users
        messaged_users = set(doc["telegram_id"] for doc in message_tracking.find({}, {"telegram_id": 1}))
        
        # Find eligible users
        query = {
            "createdAt": {"$lte": sixty_seconds_ago},
            "telegramId": {"$exists": True, "$ne": None}
        }
        
        users_to_message = users.find(query)
        
        # Send messages to eligible users
        for user in users_to_message:
            telegram_id = user.get("telegramId")
            
            if telegram_id and telegram_id not in messaged_users:
                try:
                    response = send_message(
                        TOKEN,
                        telegram_id,
                        "Afraid of Scams? So can sell as low as 1Pi"
                    )
                    
                    if response:  # Only track if message was sent successfully
                        message_tracking.insert_one({
                            "telegram_id": telegram_id,
                            "sent_at": current_time,
                            "success": True
                        })
                        print(f"Successfully sent follow-up message to {telegram_id}")
                    else:
                        print(f"Failed to send message to {telegram_id}")
                        
                except Exception as e:
                    print(f"Error sending message to user {telegram_id}: {e}")
                
                # Add small delay between messages to avoid rate limiting
                time.sleep(0.5)
                
    except Exception as e:
        print(f"Error in check_and_send_messages: {e}")

def main():
    print("Follow-up message service started...")
    
    while True:
        try:
            # Get database connection
            db = get_db_connection()
            check_and_send_messages(db)
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        # Sleep for 30 seconds before next check
        time.sleep(30)

if __name__ == "__main__":
    main()
