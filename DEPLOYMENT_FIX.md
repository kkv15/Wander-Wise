# MongoDB Integer Key Fix - Deployment Issue

## Problem
When deploying to MongoDB (Render/deployed backend), you were getting this error:
```
"documents must have only string keys, key was 1"
```

This happened because:
- `hotels_by_day` dictionary uses **integer keys** (1, 2, 3, etc.)
- MongoDB **requires all dictionary keys to be strings**
- The code was trying to save integer keys, causing MongoDB to reject the document

## Fix Applied

### 1. Backend Fix (`backend/storage/mongo_repository.py`)
- Added `_convert_keys_to_strings()` method that recursively converts all integer keys to strings
- This method is called before saving to MongoDB
- Now `hotels_by_day` keys are converted: `{1: [...]}` → `{"1": [...]}`

### 2. Frontend Fix (`frontend/src/components/ItineraryView.jsx`)
- Updated to handle both integer and string keys for backward compatibility
- Changed: `data.hotels?.hotels_by_day?.[d.day]`
- To: `data.hotels?.hotels_by_day?.[d.day] || data.hotels?.hotels_by_day?.[String(d.day)]`

## About Netlify Auto-Deploy

**Netlify auto-deploying your frontend is actually GOOD!** ✅

However, you need to understand:
1. **Frontend on Netlify** = ✅ Correct (Netlify auto-detected and deployed it)
2. **Backend** = ❌ NOT on Netlify (needs separate deployment on Render/Railway/etc.)

### Current Setup
- **Frontend:** Deployed on Netlify (this is correct!)
- **Backend:** Still needs to be deployed separately

### Next Steps for Full Deployment

1. **Deploy Backend to Render:**
   - Go to https://render.com
   - Create new Web Service
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml`
   - Add environment variables (API keys)
   - Deploy

2. **Update Frontend API URL:**
   - Go to Netlify dashboard → Site settings → Environment variables
   - Add/Update: `VITE_API_BASE` = your Render backend URL
   - Trigger a new deploy

3. **Update Backend CORS:**
   - In `backend/main.py`, update CORS origins to include your Netlify URL
   - Redeploy backend

## Testing After Fix

The MongoDB integer key error should now be fixed. After redeploying:

1. Create a new trip
2. Check "My Trips" - hotels should now appear correctly
3. Verify hotels show in both:
   - "Hotels by Location" section (grouped by city)
   - "Daily Plan" section (hotels matched to each day)

## If Issues Persist

1. Clear MongoDB collection (if you want to start fresh)
2. Create a new trip (old trips may still have the error)
3. Check backend logs on Render for any errors
4. Verify environment variables are set correctly
