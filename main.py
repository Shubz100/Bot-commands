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
    connection_string = os.getenv("DATABASE_URL")
    if not connection_string:
        print("Error: DATABASE_URL environment variable not set")
        return None
    
    try:
        client = MongoClient(connection_string)
        # Test the connection
        client.admin.command('ping')
        return client.get_database()  # This will get the database name from the connection string
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def check_and_send_messages():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    db = get_db_connection()
    if db is None:  # Explicitly check for None
        print("Failed to connect to database")
        return
    
    try:
        # Get the collections
        users = db.User  # Changed to match Prisma schema collection name
        message_tracking = db.message_tracking
        
        current_time = datetime.utcnow()
        ten_seconds_ago = current_time - timedelta(seconds=10)
        
        # Find eligible users
        users_to_message = list(users.find({
            "createdAt": {"$lte": ten_seconds_ago},
            "telegramId": {
                "$nin": [
                    doc["telegram_id"] 
                    for doc in message_tracking.find({}, {"telegram_id": 1})
                ]
            }
        }))
        
        for user in users_to_message:
            telegram_id = user.get("telegramId")
            if telegram_id:
                message_sent = send_message(
                    TOKEN,
                    telegram_id,
                    "Afraid of scams? Why not try selling just 1Pi"  # Fixed typo in message
                )
                
                if message_sent:
                    # Only track if message was sent successfully
                    message_tracking.insert_one({
                        "telegram_id": telegram_id,
                        "sent_at": current_time
                    })
                    print(f"Successfully sent follow-up message to {telegram_id}")
                else:
                    print(f"Failed to send message to {telegram_id}")
                
                # Add a small delay between messages to avoid rate limiting
                time.sleep(0.1)
                
    except Exception as e:
        print(f"Error in check_and_send_messages: {e}")

def main():
    print("Follow-up message service started...")
    
    while True:
        try:
            check_and_send_messages()
        except Exception as e:
            print(f"Error in main loop: {e}")
            # Add a longer delay if there's an error
            time.sleep(5)
            continue
        
        time.sleep(2)

if __name__ == "__main__":
    main()
