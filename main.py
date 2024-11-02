import os
from dotenv import load_dotenv
import json
import urllib.request
import urllib.parse
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import sys

load_dotenv()

def validate_environment():
    """Validate all required environment variables are present"""
    required_vars = ["DATABASE_URL", "TELEGRAM_BOT_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("Environment variables validation passed")
    return True

def send_message(token, chat_id, text):
    base_url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    data = urllib.parse.urlencode(data).encode()
    
    try:
        print(f"Attempting to send message to chat_id: {chat_id}")
        req = urllib.request.Request(base_url, data=data)
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        print(f"Message sent successfully: {result}")
        return result
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return None

def get_db_connection():
    try:
        print(f"Attempting to connect to database with URL: {os.getenv('DATABASE_URL')[:20]}...")
        client = MongoClient(os.getenv("DATABASE_URL"), serverSelectionTimeoutMS=5000)
        # Validate connection
        client.server_info()
        db = client.PiProject
        print("Successfully connected to database")
        return db
    except Exception as e:
        print(f"ERROR connecting to database: {str(e)}")
        return None

def check_and_send_messages(db):
    if db is None:
        print("Database connection is not available")
        return
    
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    print(f"Using bot token: {TOKEN[:10]}...")
    
    try:
        # Get the collections we need
        users = db.users
        message_tracking = db.message_tracking
        
        # Print collection info
        print(f"Number of users in database: {users.count_documents({})}")
        print(f"Number of tracked messages: {message_tracking.count_documents({})}")
        
        # Get current time
        current_time = datetime.utcnow()
        sixty_seconds_ago = current_time - timedelta(seconds=60)
        
        # Find eligible users
        query = {
            "createdAt": {"$lte": sixty_seconds_ago},
            "telegramId": {"$exists": True, "$ne": None}
        }
        
        users_to_message = list(users.find(query))
        print(f"Found {len(users_to_message)} users to message")
        
        # Get list of already messaged users
        messaged_users = set(doc["telegram_id"] for doc in message_tracking.find({}, {"telegram_id": 1}))
        print(f"Already messaged users count: {len(messaged_users)}")
        
        # Send messages to eligible users
        for user in users_to_message:
            telegram_id = user.get("telegramId")
            
            if telegram_id and telegram_id not in messaged_users:
                try:
                    print(f"Attempting to send message to user {telegram_id}")
                    response = send_message(
                        TOKEN,
                        telegram_id,
                        "Afraid of Scams? So can sell as low as 1Pi"
                    )
                    
                    if response:
                        message_tracking.insert_one({
                            "telegram_id": telegram_id,
                            "sent_at": current_time,
                            "success": True
                        })
                        print(f"Successfully sent and tracked message to {telegram_id}")
                    else:
                        print(f"Failed to send message to {telegram_id}")
                        
                except Exception as e:
                    print(f"Error processing user {telegram_id}: {str(e)}")
                
                time.sleep(0.5)
                
    except Exception as e:
        print(f"Error in check_and_send_messages: {str(e)}")
        
def main():
    print("Follow-up message service starting...")
    print(f"Python version: {sys.version}")
    
    # Validate environment variables
    if not validate_environment():
        print("Failed environment validation. Exiting...")
        sys.exit(1)
    
    while True:
        try:
            print("\n--- Starting new check cycle ---")
            db = get_db_connection()
            if db is None:
                print("Failed to connect to database. Waiting before retry...")
                time.sleep(30)
                continue
                
            check_and_send_messages(db)
            
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            print("Waiting before retry...")
        
        print("Sleeping for 30 seconds...")
        time.sleep(30)

if __name__ == "__main__":
    main()
