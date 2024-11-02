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

def print_database_status(db):
    """Print detailed information about database contents"""
    try:
        users = db.users
        message_tracking = db.message_tracking
        
        # Check all users
        all_users = list(users.find({}))
        print("\nDatabase Status:")
        print(f"Total users in database: {len(all_users)}")
        
        if all_users:
            print("\nSample user data:")
            sample_user = all_users[0]
            print(f"Fields present in user document: {list(sample_user.keys())}")
            print(f"Sample user telegramId: {sample_user.get('telegramId')}")
            print(f"Sample user createdAt: {sample_user.get('createdAt')}")
        
        # Check tracked messages
        tracked = list(message_tracking.find({}))
        print(f"\nTracked messages: {len(tracked)}")
        if tracked:
            print("Last tracked message:")
            print(f"Telegram ID: {tracked[-1].get('telegram_id')}")
            print(f"Sent at: {tracked[-1].get('sent_at')}")
            
    except Exception as e:
        print(f"Error checking database status: {str(e)}")

def check_and_send_messages(db):
    if db is None:
        print("Database connection is not available")
        return
    
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    try:
        # Print database status first
        print_database_status(db)
        
        users = db.users
        message_tracking = db.message_tracking
        
        # Get current time
        current_time = datetime.utcnow()
        sixty_seconds_ago = current_time - timedelta(seconds=60)
        
        # Find eligible users with detailed logging
        query = {
            "createdAt": {"$lte": sixty_seconds_ago},
            "telegramId": {"$exists": True, "$ne": None}
        }
        
        # Print the query we're using
        print(f"\nUsing query: {query}")
        
        users_to_message = list(users.find(query))
        print(f"Found {len(users_to_message)} users matching criteria")
        
        if not users_to_message:
            # Check why we found no users
            all_users_with_telegram = list(users.find({"telegramId": {"$exists": True, "$ne": None}}))
            print(f"Total users with telegramId: {len(all_users_with_telegram)}")
            
            if all_users_with_telegram:
                print("Sample user creation times:")
                for user in all_users_with_telegram[:3]:  # Show first 3 users
                    created_at = user.get('createdAt')
                    telegram_id = user.get('telegramId')
                    print(f"User {telegram_id} created at: {created_at}")
        
        # Get list of already messaged users
        messaged_users = set(doc["telegram_id"] for doc in message_tracking.find({}, {"telegram_id": 1}))
        print(f"Already messaged users count: {len(messaged_users)}")
        
        # Process eligible users
        for user in users_to_message:
            telegram_id = user.get("telegramId")
            
            if telegram_id and telegram_id not in messaged_users:
                print(f"Processing user {telegram_id}")
                print(f"User creation time: {user.get('createdAt')}")
                
                try:
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

def send_message(token, chat_id, text):
    # [Previous send_message function remains the same]
    pass

def get_db_connection():
    # [Previous get_db_connection function remains the same]
    pass

def main():
    print("Follow-up message service starting...")
    
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
