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

def validate_mongo_url():
    """Validate MongoDB URL structure"""
    url = os.getenv("DATABASE_URL", "")
    print("Checking MongoDB URL format...")
    
    if not url:
        print("ERROR: DATABASE_URL is empty")
        return False
        
    if not url.startswith("mongodb+srv://"):
        print("ERROR: DATABASE_URL should start with 'mongodb+srv://'")
        return False
        
    # Check if URL contains username and password
    try:
        # Print first few characters of username for verification
        username = url.split("//")[1].split(":")[0]
        print(f"Found username: {username[:4]}***")
        
        # Check if password is present (don't print it)
        if "@" not in url:
            print("ERROR: No password found in URL")
            return False
            
        # Check if database name is present
        if "mongodb.net/" not in url:
            print("ERROR: No database name found in URL")
            return False
            
        print("MongoDB URL format appears valid")
        return True
        
    except Exception as e:
        print(f"ERROR parsing MongoDB URL: {str(e)}")
        return False

def get_db_connection():
    """Establish database connection with detailed error reporting"""
    try:
        if not validate_mongo_url():
            return None
            
        print("Attempting to connect to MongoDB...")
        client = MongoClient(
            os.getenv("DATABASE_URL"),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test the connection
        try:
            print("Testing connection...")
            client.admin.command('ping')
            print("Connection test successful")
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return None
            
        db = client.PiProject
        print("Successfully connected to database")
        
        # Verify collections exist
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        
        if 'users' not in collections:
            print("WARNING: 'users' collection not found in database")
        if 'message_tracking' not in collections:
            print("WARNING: 'message_tracking' collection not found in database")
            
        return db
        
    except Exception as e:
        print(f"ERROR connecting to database: {str(e)}")
        print("Connection error details:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return None

def main():
    print("Follow-up message service starting...")
    print(f"Python version: {sys.version}")
    
    while True:
        try:
            print("\n--- Starting new check cycle ---")
            db = get_db_connection()
            if db is None:
                print("Failed to connect to database. Waiting 30 seconds before retry...")
                time.sleep(30)
                continue
                
            # Rest of your code...
            
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            print("Waiting before retry...")
        
        print("Sleeping for 30 seconds...")
        time.sleep(30)

if __name__ == "__main__":
    main()
