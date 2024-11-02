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
    
    try:
        # First check if the chat exists and bot can message the user
        get_chat_url = f"https://api.telegram.org/bot{token}/getChat"
        chat_data = urllib.parse.urlencode({"chat_id": chat_id}).encode()
        chat_req = urllib.request.Request(get_chat_url, data=chat_data)
        
        try:
            urllib.request.urlopen(chat_req)
        except urllib.error.HTTPError as e:
            if e.code in [400, 403]:
                print(f"Chat {chat_id} is not accessible (user may have blocked the bot or never started it)")
                return False
            raise e

        # If chat exists, try to send the message
        data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(base_url, data=data)
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    
    except urllib.error.HTTPError as e:
        print(f"Error sending message to {chat_id}: HTTP Error {e.code}: {e.reason}")
        print(f"Response body: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Unexpected error sending message to {chat_id}: {str(e)}")
        return False

def get_db_connection():
    connection_string = os.getenv("DATABASE_URL")
    if not connection_string:
        print("Error: DATABASE_URL environment variable not set")
        return None
    
    try:
        client = MongoClient(connection_string)
        client.admin.command('ping')
        return client.get_database()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def check_and_send_messages():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    db = get_db_connection()
    if db is None:
        print("Failed to connect to database")
        return
    
    try:
        users = db.User
        message_tracking = db.message_tracking
        
        # Ensure message_tracking collection exists
        if "message_tracking" not in db.list_collection_names():
            db.create_collection("message_tracking")
        
        current_time = datetime.utcnow()
        ten_seconds_ago = current_time - timedelta(seconds=10)
        
        # Get list of already messaged users
        sent_to_users = set(
            doc["telegram_id"] 
            for doc in message_tracking.find({}, {"telegram_id": 1})
        )
        
        # Find eligible users and explicitly convert cursor to list
        users_query = {
            "createdAt": {"$lte": ten_seconds_ago},
            "telegramId": {"$exists": True, "$ne": None}
        }
        
        for user in users.find(users_query):
            telegram_id = user.get("telegramId")
            
            # Skip if already messaged
            if telegram_id in sent_to_users:
                continue
                
            # Skip invalid telegram_ids
            if not isinstance(telegram_id, (int, str)) or str(telegram_id).strip() == "":
                print(f"Skipping invalid telegram_id: {telegram_id}")
                continue
            
            print(f"Attempting to send message to user {telegram_id}")
            
            # Try to send message
            message_sent = send_message(
                TOKEN,
                telegram_id,
                "Afraid of scams? Why not try selling just 1Pi"
            )
            
            if message_sent:
                # Track successful message
                message_tracking.insert_one({
                    "telegram_id": telegram_id,
                    "sent_at": current_time,
                    "status": "success"
                })
                print(f"Successfully sent follow-up message to {telegram_id}")
            else:
                # Track failed attempt
                message_tracking.insert_one({
                    "telegram_id": telegram_id,
                    "sent_at": current_time,
                    "status": "failed"
                })
                print(f"Failed to send message to {telegram_id}")
            
            # Add delay between messages
            time.sleep(0.5)
                
    except Exception as e:
        print(f"Error in check_and_send_messages: {e}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.content}")

def main():
    print("Follow-up message service started...")
    
    while True:
        try:
            check_and_send_messages()
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)
            continue
        
        time.sleep(2)

if __name__ == "__main__":
    main()
