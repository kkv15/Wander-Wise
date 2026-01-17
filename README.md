# WanderWise - AI-Powered Travel Planning Platform

**WanderWise** is an AI-powered travel planning platform that generates personalized day-by-day itineraries with hotel recommendations, attraction suggestions, and budget estimates for any destination.

This full-stack application:
- Generates detailed, elaborative day-by-day itineraries using AI (Groq)
- Suggests hotels and attractions using free providers (OpenStreetMap stack)
- Estimates costs (flights, hotels, daily spend) heuristically
- Saves itineraries with user authentication support
- Works entirely on free-tier APIs 

Backend: Python (FastAPI)  
Frontend: React (Vite)  
Database: MongoDB Atlas (M0 free tier)  
AI: Groq API (free tier)  
Maps/Places: 
- Geocoding: Nominatim (OpenStreetMap)
- Attractions: OpenTripMap (free API key)
- Hotels: OSM via Overpass API (free, rate limited)



---

### 1) Free Provider Setup (No Card Required)

1. OpenTripMap API key: create a free account and copy the API key.
2. Nominatim: no key; add your email to requests for politeness and to comply with usage policy.
3. Groq API key: create a free account and copy the API key (no card).
4. SQLite: no setup; a local file will be created automatically.

---

### 2) Backend Setup (FastAPI)

Requirements: Python 3.10+

1. Copy `backend/.env.example` to `backend/.env` and fill in your API keys:
   ```bash
   cp backend/.env.example backend/.env
   ```
   
   Required API keys:
   - `OPENTRIPMAP_API_KEY` - Get from https://opentripmap.io/docs
   - `GROQ_API_KEY` - Get from https://console.groq.com/
   - `NOMINATIM_EMAIL` - Your email (optional but recommended)
   
   Optional API keys:
   - `GOOGLE_PLACES_API_KEY` - For enhanced hotel ratings
   - `OPENROUTESERVICE_API_KEY` - For detailed route planning
   
   Database configuration:
   - `DB_BACKEND=sqlite` (default) or `mongo`
   - For MongoDB: Set `MONGODB_URI`, `MONGO_DB`, `JWT_SECRET`
   - For SQLite: No additional config needed
2. Install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Run backend locally:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Health check:
Open `http://localhost:8000/health`.

---

### 3) Frontend Setup (React + Vite)

Requirements: Node 18+

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

In production, deploy the frontend to Firebase Hosting (free tier) or Vercel/Netlify.

---

### 4) How Python Scripts Work (High-level)

- `backend/main.py`: FastAPI app, defines routes:
  - `POST /api/plan-trip`: orchestrates geocoding (Nominatim), attractions (OpenTripMap), hotels and airports (Overpass), AI itinerary generation (Groq), and cost estimation. Saves result to SQLite.
  - `GET /health`: simple health endpoint.
- `backend/models/schemas.py`: Pydantic models for request/response, strong typing.
- `backend/services/free_places_service.py`: Free stack provider:
  - Geocode cities (Nominatim)
  - Find attractions (OpenTripMap)
  - Find hotels and airports (Overpass API)
- `backend/services/ai_service.py`: Calls Groq (open model) to produce a day-by-day itinerary JSON given inputs and candidates.
- `backend/utils/cost_estimator.py`: Heuristic flight/hotel/daily-spend estimator using distance and rough city price signals.
- `backend/storage/sqlite_repository.py` and `backend/models/db_models.py`: Saves itineraries in SQLite as JSON blobs.

You can open each file to see docstrings and comments that explain details inline.

---

### 5) Environment Variables

Copy `.env.example` to `.env` and set:

```
OPENTRIPMAP_API_KEY=YOUR_OTM_API_KEY
NOMINATIM_EMAIL=your@email
GROQ_API_KEY=YOUR_GROQ_API_KEY
SQLITE_PATH=./data.db
DEFAULT_CURRENCY=INR
```

---

### 6) Deployment

#### Quick Deploy to Netlify (Frontend) + Render (Backend)

**See detailed guide in [`NETLIFY_DEPLOYMENT.md`](NETLIFY_DEPLOYMENT.md)**

**Quick Steps:**

1. **Frontend (Netlify):**
   - Push code to GitHub
   - Connect to Netlify
   - Build command: `cd frontend && npm install && npm run build`
   - Publish directory: `frontend/dist`
   - Set environment variable: `VITE_API_BASE` = your backend URL

2. **Backend (Render - Free Tier):**
   - Sign up at https://render.com
   - Connect GitHub repository
   - Create new Web Service
   - Render will auto-detect `render.yaml`
   - Add environment variables in Render dashboard
   - Deploy!

**Alternative Backend Hosting:**
- **Railway** (Free tier with $5 credit/month)
- **Fly.io** (Free tier available)
- **Heroku** (No longer free, but paid options available)

**Docker Deployment:**
- Dockerfile is included in `backend/`. Build and run with Docker if you prefer containers.

---

### 7) Notes and Limitations
- Flight prices are estimated, not real-time. Add a 3rd-party API later if needed.
- Free providers have rate limits:
  - Nominatim and Overpass: be gentle, cache responses, include contact email, and avoid heavy load.
  - OpenTripMap: respect your free plan’s limits.
- Groq free tier has rate limits; keep prompts small and cache results if possible.

---

### 8) API Contract

Request:
```json
POST /api/plan-trip
{
  "originCity": "New Delhi, IN",
  "destinationCity": "Bangkok, TH",
  "numDays": 5,
  "numPeople": 2,
  "budgetCurrency": "INR",
  "budgetAmount": 120000
}
```

Response (abridged):
```json
{
  "itineraryId": "abc123",
  "summary": "...",
  "flights": {
    "originAirport": "Indira Gandhi International Airport",
    "destinationAirport": "Suvarnabhumi Airport",
    "estimatedRoundTripPerPerson": 28000
  },
  "hotels": [{ "name": "...", "address": "..." }],
  "dailyPlan": [{ "day": 1, "items": ["..."] }],
  "estimatedTotals": {
    "flights": 56000,
    "hotels": 40000,
    "activities": 10000,
    "foodTransportMisc": 8000,
    "grandTotal": 114000,
    "currency": "INR"
  }
}
```

---

### 9) Next Steps
- Replace flight cost heuristic with a real flights API when available.
- Add map visualizations on the frontend using Leaflet (free) with OSM tiles.


