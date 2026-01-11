# Netlify Deployment Guide for WanderWise

This guide will help you deploy WanderWise on Netlify's free tier.

## ⚠️ Important: Two-Part Deployment

Since Netlify's free tier primarily supports static sites and serverless functions, you'll need to deploy:
1. **Frontend** (React) → Netlify (Free)
2. **Backend** (FastAPI) → Render/Railway/Fly.io (Free tier available)

---

## Part 1: Deploy Frontend to Netlify

### Prerequisites
- GitHub/GitLab/Bitbucket account
- Netlify account (sign up at https://app.netlify.com)

### Step 1: Push Your Code to Git

If you haven't already:

```bash
cd E:\Project\untitled
git add .
git commit -m "Prepare for Netlify deployment"
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 2: Deploy via Netlify Dashboard

1. **Go to Netlify Dashboard**
   - Visit https://app.netlify.com
   - Click "Add new site" → "Import an existing project"

2. **Connect Your Repository**
   - Choose your Git provider (GitHub/GitLab/Bitbucket)
   - Authorize Netlify to access your repositories
   - Select your `wanderwise` repository

3. **Configure Build Settings**
   - **Base directory:** Leave empty (root)
   - **Build command:** `cd frontend && npm install && npm run build`
   - **Publish directory:** `frontend/dist`
   - Click "Show advanced" → Click "New variable" and add:
     - **Key:** `VITE_API_BASE`
     - **Value:** `https://your-backend-url.onrender.com` (or your backend URL)
     - Click "Deploy site"

### Step 3: Configure Environment Variables

After initial deployment:

1. Go to **Site settings** → **Environment variables**
2. Add the following variable:
   ```
   Key: VITE_API_BASE
   Value: https://your-backend-url.onrender.com
   ```
3. Click "Save" and **trigger a new deploy** (Deploys → Trigger deploy → Deploy site)

### Step 4: Update Backend CORS (Important!)

After you have your Netlify frontend URL, update your backend CORS settings:

1. Go to your backend code
2. Update `backend/main.py`:

```python
# In main.py, update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local dev
        "https://your-site-name.netlify.app",  # Your Netlify URL
        "https://www.your-custom-domain.com"  # If you add custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Part 2: Deploy Backend to Render (Recommended - Free Tier)

### Why Render?
- **Free tier available** for web services
- Easy Python/FastAPI deployment
- Automatic HTTPS
- Environment variable management

### Step 1: Prepare Backend for Render

1. **Create `render.yaml`** in your project root:

```yaml
services:
  - type: web
    name: wanderwise-backend
    env: python
    plan: free
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENTRIPMAP_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: NOMINATIM_EMAIL
        sync: false
      - key: GOOGLE_PLACES_API_KEY
        sync: false
      - key: OPENROUTESERVICE_API_KEY
        sync: false
      - key: DB_BACKEND
        value: sqlite
      - key: DEFAULT_CURRENCY
        value: INR
```

2. **Update `backend/main.py`** CORS to include Render URL (after deployment).

### Step 2: Deploy to Render

1. **Sign up at Render:**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`

3. **Configure Environment Variables:**
   - Go to "Environment" tab
   - Add all your API keys from `.env` file:
     - `OPENTRIPMAP_API_KEY`
     - `GROQ_API_KEY`
     - `NOMINATIM_EMAIL`
     - `GOOGLE_PLACES_API_KEY` (optional)
     - `OPENROUTESERVICE_API_KEY` (optional)

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for build to complete (5-10 minutes first time)
   - Copy your Render URL (e.g., `https://wanderwise-backend.onrender.com`)

### Step 3: Update Frontend API URL

1. Go back to Netlify dashboard
2. Site settings → Environment variables
3. Update `VITE_API_BASE` with your Render backend URL
4. Trigger a new deploy

---

## Part 3: Alternative Backend Hosting Options

### Option A: Railway (Free Tier with Credit Card)

1. Sign up at https://railway.app
2. Create new project → Deploy from GitHub
3. Select your repository
4. Railway auto-detects Python
5. Add environment variables
6. Deploy

### Option B: Fly.io (Free Tier)

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up: `fly auth signup`
3. Create app: `fly launch`
4. Deploy: `fly deploy`

### Option C: Render (Recommended - Already covered above)

---

## Part 4: Database Setup

### For MongoDB (If using MongoDB):

1. Use **MongoDB Atlas** (Free tier: M0):
   - Sign up at https://www.mongodb.com/cloud/atlas
   - Create free cluster
   - Get connection string
   - Add to Render environment variables:
     - `DB_BACKEND=mongo`
     - `MONGODB_URI=your-connection-string`
     - `MONGO_DB=wanderwise`
     - `JWT_SECRET=your-random-secret`

### For SQLite (Default - File-based):

- SQLite will work on Render, but data will be lost on redeploy
- For production, use MongoDB Atlas (free tier)

---

## Part 5: Final Configuration

### Update Backend CORS

In `backend/main.py`, update the CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local dev
        "https://your-site-name.netlify.app",  # Netlify frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Verify Deployment

1. **Test Frontend:**
   - Visit your Netlify URL
   - Should load the app

2. **Test Backend:**
   - Visit `https://your-backend.onrender.com/health`
   - Should return `{"status":"ok"}`

3. **Test Full Flow:**
   - Try planning a trip on Netlify frontend
   - Should connect to Render backend

---

## Troubleshooting

### Frontend shows "Network Error"
- Check `VITE_API_BASE` environment variable in Netlify
- Ensure backend CORS includes your Netlify URL
- Check backend is running (visit backend `/health` endpoint)

### Backend deployment fails
- Check `requirements.txt` is correct
- Verify all environment variables are set
- Check Render logs for errors

### CORS errors
- Update backend CORS to include exact Netlify URL
- Ensure `allow_credentials=True` in CORS config
- Restart backend after CORS changes

### Build fails on Netlify
- Check Node version (should be 18+)
- Verify `package.json` scripts are correct
- Check Netlify build logs

---

## Custom Domain (Optional)

### Netlify:
1. Site settings → Domain management
2. Add custom domain
3. Follow DNS setup instructions

### Update Backend CORS:
- Add your custom domain to CORS origins in `backend/main.py`

---

## Free Tier Limits

### Netlify:
- ✅ 100GB bandwidth/month
- ✅ 300 build minutes/month
- ✅ Unlimited sites

### Render:
- ✅ 750 hours/month (enough for always-on service)
- ✅ 512MB RAM
- ⚠️ Sleeps after 15 min inactivity (wakes on request)

### Railway (if using):
- ✅ $5 free credit/month
- ⚠️ Requires credit card

---

## Quick Deployment Checklist

- [ ] Code pushed to Git (GitHub/GitLab/Bitbucket)
- [ ] Frontend deployed to Netlify
- [ ] Backend deployed to Render
- [ ] Environment variables configured (both Netlify & Render)
- [ ] Backend CORS updated with Netlify URL
- [ ] Frontend `VITE_API_BASE` set to Render URL
- [ ] Database configured (MongoDB Atlas if using)
- [ ] Tested full flow (plan trip works)

---

## Support

If you encounter issues:
1. Check build logs in Netlify dashboard
2. Check deployment logs in Render dashboard
3. Verify environment variables are set correctly
4. Test backend health endpoint directly

---

**Congratulations!** Your WanderWise app should now be live on Netlify! 🎉
