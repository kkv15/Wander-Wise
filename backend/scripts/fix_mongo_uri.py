"""
Helper script to properly format MongoDB URI with URL encoding.
"""
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

load_dotenv()

print("MongoDB Connection String Helper\n")
print("=" * 50)

# Get current URI to show what's wrong
current_uri = os.getenv("MONGODB_URI", "")
if current_uri:
    print(f"Current MONGODB_URI (masked): {current_uri.split('@')[0] if '@' in current_uri else current_uri}@***")
    print()

print("To fix your connection string, you need:")
print("1. Your MongoDB username")
print("2. Your MongoDB password")
print("3. Your cluster URL (from MongoDB Atlas)")
print()

# Get inputs
username = input("Enter your MongoDB username: ").strip()
password = input("Enter your MongoDB password: ").strip()
cluster_url = input("Enter your cluster URL (e.g., cluster0.xxxxx.mongodb.net): ").strip()

# URL encode username and password
encoded_username = quote_plus(username)
encoded_password = quote_plus(password)

# Build the connection string
connection_string = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster_url}/?retryWrites=true&w=majority"

print()
print("=" * 50)
print("Copy this to your .env file:")
print("=" * 50)
print(f"MONGODB_URI={connection_string}")
print("=" * 50)
print()
print("Note: If your password contains special characters, they are now properly encoded.")
