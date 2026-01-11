"""
Test MongoDB connection script.
Run this to verify your MongoDB connection string is correct.
"""
import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI from environment
mongo_uri = os.getenv("MONGODB_URI")
mongo_db = os.getenv("MONGO_DB", "wanderwise")

if not mongo_uri:
    print("ERROR: MONGODB_URI not found in .env file")
    sys.exit(1)

print("Testing MongoDB connection...")
print(f"Database: {mongo_db}")
print(f"URI (masked): {mongo_uri.split('@')[0] if '@' in mongo_uri else mongo_uri}@***")
print()

try:
    from pymongo import MongoClient
    from pymongo.errors import OperationFailure, ConfigurationError, ServerSelectionTimeoutError
    
    # Try to connect
    print("Attempting to connect...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    
    # Test connection by listing databases (this requires authentication)
    print("Testing authentication...")
    client.admin.command('ping')
    
    # List databases to verify connection works
    db_list = client.list_database_names()
    print(f"✓ Connection successful!")
    print(f"Available databases: {db_list}")
    
    # Test database access
    db = client[mongo_db]
    collections = db.list_collection_names()
    print(f"✓ Database '{mongo_db}' accessible")
    print(f"Collections: {collections if collections else '(none yet)'}")
    
    client.close()
    print("\n✓ All tests passed! Your MongoDB connection is working correctly.")
    
except OperationFailure as e:
    print(f"✗ Authentication failed: {e}")
    print("\nCommon fixes:")
    print("1. Check if your password contains special characters (encode them)")
    print("2. Verify username and password are correct")
    print("3. Make sure the database user exists in MongoDB Atlas")
    sys.exit(1)
    
except ServerSelectionTimeoutError as e:
    print(f"✗ Connection timeout: {e}")
    print("\nCommon fixes:")
    print("1. Check if your IP address is whitelisted in MongoDB Atlas")
    print("2. Go to Network Access → Add IP Address → Allow Access from Anywhere")
    print("3. Wait 1-2 minutes after whitelisting before retrying")
    sys.exit(1)
    
except ConfigurationError as e:
    print(f"✗ Configuration error: {e}")
    print("\nCheck your MONGODB_URI format. It should look like:")
    print("mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    print(f"Error type: {type(e).__name__}")
    sys.exit(1)
