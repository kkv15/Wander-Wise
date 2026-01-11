# MongoDB Setup Guide

## Understanding the Error

The error `pymongo.errors.OperationFailure: bad auth : Authentication failed` means your MongoDB connection string is incorrect or missing credentials.

**Important:** `JWT_SECRET` and `MONGODB_URI` are two completely different things:
- `JWT_SECRET`: Used for signing API tokens (you've already set this correctly)
- `MONGODB_URI`: Used to connect to your MongoDB database (this needs database credentials)

## Setup Steps

### Option 1: MongoDB Atlas (Free Tier - Recommended)

1. **Create Account**: Go to https://www.mongodb.com/cloud/atlas/register
2. **Create Cluster**: Choose the free M0 tier
3. **Create Database User**:
   - Go to "Database Access" → "Add New Database User"
   - Choose "Password" authentication
   - Create username and password (save these!)
   - Set privileges to "Atlas admin" or "Read and write to any database"
4. **Whitelist IP Address**:
   - Go to "Network Access" → "Add IP Address"
   - Click "Allow Access from Anywhere" for development (or add your specific IP)
5. **Get Connection String**:
   - Go to "Database" → Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user's password
   - Replace `<username>` with your database username

### Option 2: Local MongoDB

If you have MongoDB installed locally:
```bash
# Install MongoDB (if not installed)
# Windows: Download from https://www.mongodb.com/try/download/community
# Or use Docker: docker run -d -p 27017:27017 --name mongodb mongo

# Connection string for local MongoDB (no authentication):
mongodb://localhost:27017
```

## .env File Configuration

Add these variables to your `backend/.env` file:

```env
# Database backend (use "mongo" for MongoDB, "sqlite" for SQLite)
DB_BACKEND=mongo

# MongoDB connection string
# Format: mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_URI=mongodb+srv://your-username:your-password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority

# MongoDB database name
MONGO_DB=wanderwise

# JWT secret for API authentication (this is separate from MongoDB!)
JWT_SECRET=your-random-secret-string-here

# Other required variables
GROQ_API_KEY=your-groq-key
OPENTRIPMAP_API_KEY=your-opentripmap-key
NOMINATIM_EMAIL=your@email.com
DEFAULT_CURRENCY=INR
```

## Common Issues & Fixes

### Issue 1: Special Characters in Password (MOST COMMON!)

If your MongoDB password contains special characters, you **MUST URL-encode** them:

| Character | Encoded |
|-----------|---------|
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |
| `&` | `%26` |
| `+` | `%2B` |
| `=` | `%3D` |
| ` ` (space) | `%20` |

**Example:** If your password is `MyPass@123#`, your connection string should be:
```
mongodb+srv://username:MyPass%40123%23@cluster.mongodb.net/...
```

**Quick fix:** Use Python to encode your password:
```python
from urllib.parse import quote_plus
password = "YourPassword@123#"
encoded = quote_plus(password)
print(encoded)  # Use this in your connection string
```

### Issue 2: IP Address Not Whitelisted

1. Go to MongoDB Atlas → **Network Access**
2. Click **"Add IP Address"**
3. For development, click **"Allow Access from Anywhere"** (adds `0.0.0.0/0`)
4. **Wait 1-2 minutes** for changes to propagate
5. Try connecting again

### Issue 3: Wrong Credentials

1. Go to MongoDB Atlas → **Database Access**
2. Verify your username and password
3. Make sure the user has **"Atlas admin"** or **"Read and write to any database"** role
4. If needed, reset the password and update your `.env` file

### Issue 4: Connection String Format

Your connection string should look like:
```
mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

Make sure:
- No spaces before/after the URI
- Password is URL-encoded if it has special characters
- The cluster name matches your actual cluster

## Testing the Connection

**Step 1: Test with the diagnostic script**
```bash
cd backend
python test_mongo_connection.py
```

This will tell you exactly what's wrong!

**Step 2: If test passes, restart your server**
```bash
cd backend
uvicorn main:app --reload
```

The connection will be tested when you try to register or login.
