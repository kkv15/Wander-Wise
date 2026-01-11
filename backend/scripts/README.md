# Utility Scripts

This folder contains utility scripts for development and debugging.

## test_mongo_connection.py

Test script to verify MongoDB connection string is correct.

**Usage:**
```bash
python backend/scripts/test_mongo_connection.py
```

This script:
- Tests MongoDB connection using your `.env` configuration
- Verifies authentication
- Checks database accessibility
- Provides troubleshooting tips if connection fails

## fix_mongo_uri.py

Helper script to properly format MongoDB URI with URL encoding for special characters.

**Usage:**
```bash
python backend/scripts/fix_mongo_uri.py
```

This script:
- Prompts for MongoDB username, password, and cluster URL
- URL-encodes special characters in credentials
- Generates properly formatted connection string
- Outputs ready-to-use `MONGODB_URI` for your `.env` file
