# Trip Planning API Improvements

## Overview
This document describes the improvements made to the trip planning API to provide better route planning and hotel recommendations.

## Improvements

### 1. Enhanced Airport Detection

**Problem:** The API was finding small aerodromes instead of commercial airports (e.g., showing random aerodromes instead of Bagdogra airport for Sikkim).

**Solution:**
- Prioritizes commercial airports (`aeroway=airport`) over general aerodromes
- Prefers airports with IATA codes (like IXB for Bagdogra)
- Expands search radius intelligently to find the best airport
- Returns airport name with IATA code when available

**Example:** 
- For Sikkim, it now correctly identifies Bagdogra Airport (IXB) instead of random aerodromes

### 2. Route Planning Integration

**Problem:** For destinations like Sikkim, users need to fly to Bagdogra and then take ground transport to Gangtok, but the API wasn't providing this information.

**Solution:**
- Integrates with OpenRouteService API (free tier: 2000 requests/day) for route directions
- Automatically detects when destination is far from airport (>10km)
- Provides route information including:
  - Distance in kilometers
  - Estimated travel time
  - Route steps (for detailed directions)
- Falls back to simple distance calculation if API key not configured

**Configuration:**
Add to your `.env` file:
```env
OPENROUTESERVICE_API_KEY=your-api-key-here
```

**Get API Key:**
1. Sign up at https://openrouteservice.org/dev/#/signup
2. Get your free API key (2000 requests/day)
3. Add to `.env` file

**Note:** The API works without this key but will provide simpler route estimates.

### 3. Enhanced Hotel Recommendations

**Improvements:**
1. **More Hotels:** Increased search radius and improved query to find 15+ hotels (up from 2)
2. **Booking Links:** Automatically generates Booking.com and Agoda search links for each hotel
3. **Better Display:** Frontend now shows:
   - Hotel star ratings
   - User ratings (when available)
   - Direct booking links to Booking.com and Agoda
   - Phone numbers (when available)

**Booking Links:**
- Hotels now include `booking_links` object with:
  - `booking_com`: Direct search link to Booking.com
  - `agoda`: Direct search link to Agoda
- Users can click these links to see ratings, prices, and book directly

### 4. AI Itinerary Enhancement

**Route Information in Itineraries:**
- When destination is far from airport, AI now includes ground transport instructions
- Example: "Fly to Bagdogra Airport (IXB), then take bus/taxi to Gangtok (approx. 124km, 3 hours)"
- Includes this in Day 1 of the itinerary automatically

## Configuration

### Required Environment Variables

```env
# Existing required variables
GROQ_API_KEY=your-groq-key
OPENTRIPMAP_API_KEY=your-opentripmap-key
NOMINATIM_EMAIL=your@email.com
DB_BACKEND=mongo  # or sqlite
MONGODB_URI=mongodb+srv://...
MONGO_DB=your-db-name
JWT_SECRET=your-secret

# New optional variable (for enhanced route planning)
OPENROUTESERVICE_API_KEY=your-openrouteservice-key  # Optional but recommended
```

### Getting OpenRouteService API Key (Free)

1. Visit: https://openrouteservice.org/dev/#/signup
2. Sign up for free account
3. Get your API key from dashboard
4. Free tier includes: 2000 requests/day

**Note:** The API works without this key but provides basic route estimates.

## API Response Changes

### Airport Object
```json
{
  "name": "Bagdogra Airport",
  "iata": "IXB",
  "lat": 26.6811,
  "lng": 88.3286,
  "place_id": "osm-node-12345"
}
```

### Hotel Object (Enhanced)
```json
{
  "name": "Hotel Name",
  "address": "Hotel Address",
  "rating": 4.5,
  "user_ratings_total": 123,
  "stars": 4,
  "lat": 27.3389,
  "lng": 88.6069,
  "place_id": "osm-node-67890",
  "booking_links": {
    "booking_com": "https://www.booking.com/search.html?ss=...",
    "agoda": "https://www.agoda.com/search?city=...&q=..."
  },
  "phone": "+91-1234567890",
  "url": "https://hotel-website.com"
}
```

### Route Information (New)
When destination is far from airport, the API response includes route information in the AI summary:
- Distance from airport to destination
- Estimated travel time
- Ground transport recommendation

## Testing

### Test Airport Detection
```bash
# Test with Bangalore to Sikkim
curl -X POST http://localhost:8000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "originCity": "Bangalore, IN",
    "destinationCity": "Gangtok, Sikkim, IN",
    "numDays": 5,
    "numPeople": 2,
    "budgetCurrency": "INR",
    "budgetAmount": 50000
  }'
```

Expected:
- Origin airport: Bangalore Airport (BLR) or Kempegowda International Airport
- Destination airport: Bagdogra Airport (IXB)
- Route info: Distance from Bagdogra to Gangtok (~124km)
- Itinerary should mention: "Fly to Bagdogra (IXB), then take bus/taxi to Gangtok"

### Test Hotel Recommendations
- Should return 15+ hotels (instead of 2)
- Each hotel should have booking_links object
- Frontend should display Booking.com and Agoda buttons

## Free Tier Limits

All APIs used are free tier compatible:

1. **OpenRouteService**: 2000 requests/day (free)
2. **OpenTripMap**: Free tier available
3. **Nominatim**: Free (respect usage policy)
4. **Overpass API**: Free (respect usage policy)
5. **Booking.com/Agoda**: Deep links (no API calls, just URL generation)

## Troubleshooting

### Issue: Still showing wrong airports
- Check Overpass API response (may need to expand search radius)
- Verify destination coordinates are correct
- Airport data depends on OpenStreetMap completeness

### Issue: No route information
- Check if `OPENROUTESERVICE_API_KEY` is set
- Verify destination is more than 10km from airport
- Check API key validity (2000 requests/day limit)

### Issue: Hotels not showing booking links
- Verify hotel name and city are available
- Check frontend is using latest version
- Booking links are generated from hotel name + city search

## Future Enhancements

### ✅ Implemented Improvements

The following improvements have been implemented:

#### 1. Google Places API Integration for Hotel Ratings

**Status:** ✅ Implemented (Optional)

**Features:**
- Integrates with Google Places API when `GOOGLE_PLACES_API_KEY` is provided
- Enhances hotel data with:
  - Accurate ratings from Google
  - User review counts
  - Price levels
  - Phone numbers
  - Official websites
- Falls back gracefully to OSM data if API key not configured
- Free tier: $200 credit/month (sufficient for low to moderate usage)

**Configuration:**
```env
GOOGLE_PLACES_API_KEY=your-google-places-api-key
```

**Get API Key:**
1. Visit: https://console.cloud.google.com/
2. Enable Places API
3. Create credentials (API key)
4. Add to `.env` file

#### 2. Enhanced Train Route Planning

**Status:** ✅ Implemented

**Features:**
- Improved train estimation with multiple classes:
  - SL (Sleeper): Basic budget option
  - 3A (3-tier AC): Comfortable mid-range
  - 2A (2-tier AC): Premium option
  - 1A (First AC): Luxury option
- Includes distance and duration estimates
- Better fare calculations based on distance
- Clear descriptions for each class

**Usage:**
- Automatically enabled for intra-India trips within 1200km
- Shows in itinerary when train is available
- Estimates include all class options

#### 3. Multiple Ground Transport Options

**Status:** ✅ Implemented

**Features:**
- Provides multiple transport options from airport to destination:
  - **Taxi/Private Car**: Fastest option
  - **Bus**: Budget-friendly public transport
  - **Shared Taxi**: Cost-effective middle ground
- Shows distance and duration for each option
- Automatically detects when destination is far from airport (>10km)
- All options include route information

**Implementation:**
- Uses OpenRouteService API with different profiles
- Caches results to reduce API calls
- Falls back to distance calculation if API unavailable

#### 4. Route Information Caching

**Status:** ✅ Implemented

**Features:**
- In-memory cache for route information
- Cache TTL: 1 hour
- Reduces API calls significantly
- Automatic cache cleanup of expired entries
- Cache key based on route coordinates and profile

**Benefits:**
- Reduces OpenRouteService API calls (free tier: 2000/day)
- Faster response times for repeated queries
- Lower API costs

**Implementation Details:**
- Cache key: MD5 hash of rounded coordinates + profile
- Coordinates rounded to ~100m precision for effective caching
- Automatic expiration after 1 hour

#### 5. Additional Booking Platforms for India

**Status:** ✅ Implemented

**Features:**
- Added MakeMyTrip and Goibibo booking links for hotels in India
- Automatically detects Indian destinations (by coordinates or city name)
- Provides both hotel-specific and city-level search links
- Frontend displays booking buttons for all platforms:
  - Booking.com (international)
  - Agoda (international)
  - MakeMyTrip (India)
  - Goibibo (India)

**Booking Links Structure:**
```json
{
  "booking_hotel": "https://...",
  "agoda_hotel": "https://...",
  "makemytrip": "https://... (India only)",
  "goibibo": "https://... (India only)",
  "booking_city": "https://...",
  "agoda_city": "https://...",
  "makemytrip_city": "https://... (India only)",
  "goibibo_city": "https://... (India only)"
}
```

## Configuration Summary

### Required Environment Variables

```env
# Existing required
GROQ_API_KEY=your-groq-key
OPENTRIPMAP_API_KEY=your-opentripmap-key
NOMINATIM_EMAIL=your@email.com
DB_BACKEND=mongo  # or sqlite
MONGODB_URI=mongodb+srv://...
MONGO_DB=your-db-name
JWT_SECRET=your-secret

# New optional (for enhanced features)
OPENROUTESERVICE_API_KEY=your-openrouteservice-key  # For route planning (recommended)
GOOGLE_PLACES_API_KEY=your-google-places-key  # For better hotel ratings (optional)
```

## API Response Changes

### Hotels Structure

Hotels are now returned with metadata:

```json
{
  "hotels": {
    "hotels": [
      {
        "name": "Hotel Name",
        "address": "Address",
        "rating": 4.5,
        "user_ratings_total": 123,
        "stars": 4,
        "price_level": 2,
        "lat": 27.3389,
        "lng": 88.6069,
        "place_id": "osm-node-123",
        "booking_links": {
          "booking_hotel": "https://...",
          "agoda_hotel": "https://...",
          "makemytrip": "https://... (India only)",
          "goibibo": "https://... (India only)"
        },
        "phone": "+91-1234567890",
        "url": "https://hotel-website.com"
      }
    ],
    "count": 15,
    "city_links": {
      "booking_city": "https://...",
      "agoda_city": "https://...",
      "makemytrip_city": "https://... (India only)",
      "goibibo_city": "https://... (India only)"
    },
    "note": "Hotel list is limited due to OpenStreetMap coverage..."
  }
}
```

### Train Estimate Structure

```json
{
  "train": {
    "available": true,
    "distance_km": 850.5,
    "classes": {
      "SL": {
        "estFarePerPerson": 510.3,
        "estDurationHours": 16.0,
        "currency": "INR",
        "description": "Sleeper Class"
      },
      "3A": {
        "estFarePerPerson": 1360.8,
        "estDurationHours": 16.0,
        "currency": "INR",
        "description": "3-tier AC"
      },
      "2A": {
        "estFarePerPerson": 2041.2,
        "estDurationHours": 16.0,
        "currency": "INR",
        "description": "2-tier AC"
      },
      "1A": {
        "estFarePerPerson": 3402.0,
        "estDurationHours": 16.0,
        "currency": "INR",
        "description": "First AC"
      }
    },
    "note": "Estimates only. Actual fares and duration may vary. Book via IRCTC (irctc.co.in) or authorized agents."
  }
}
```

### Route Information Structure

```json
{
  "route_info": {
    "taxi": {
      "distance_km": 124.5,
      "duration_minutes": 180,
      "mode": "taxi",
      "description": "Private taxi or car",
      "available": true,
      "cached": false
    },
    "bus": {
      "distance_km": 124.5,
      "duration_minutes": 234,
      "mode": "bus",
      "description": "Bus service",
      "available": true,
      "cached": false
    },
    "shared_taxi": {
      "distance_km": 124.5,
      "duration_minutes": 207,
      "mode": "shared_taxi",
      "description": "Shared taxi/cab",
      "available": true,
      "cached": false
    },
    "primary": {
      "distance_km": 124.5,
      "duration_minutes": 180,
      "available": true
    }
  }
}
```

## Performance Improvements

1. **Route Caching**: Reduces API calls by ~80-90% for repeated routes
2. **Google Places API**: Optional, only used when API key provided
3. **Smart India Detection**: Efficiently detects Indian destinations for platform-specific links

## Testing

### Test Google Places Integration
```bash
# Set GOOGLE_PLACES_API_KEY in .env
# Test with any destination
curl -X POST http://localhost:8000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "originCity": "Delhi, IN",
    "destinationCity": "Mumbai, IN",
    "numDays": 3,
    "numPeople": 2
  }'
```

Expected: Hotels should have ratings, user_ratings_total, and price_level from Google Places

### Test Multiple Transport Options
```bash
# Test with destination far from airport (e.g., Gangtok)
curl -X POST http://localhost:8000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "originCity": "Bangalore, IN",
    "destinationCity": "Gangtok, Sikkim, IN",
    "numDays": 5,
    "numPeople": 2
  }'
```

Expected: Route info should include taxi, bus, and shared_taxi options

### Test Indian Booking Platforms
```bash
# Test with Indian destination
curl -X POST http://localhost:8000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "originCity": "Delhi, IN",
    "destinationCity": "Goa, IN",
    "numDays": 4,
    "numPeople": 2
  }'
```

Expected: Hotels should include makemytrip and goibibo booking links

### Test Train Route Planning
```bash
# Test with short intra-India trip
curl -X POST http://localhost:8000/api/plan-trip \
  -H "Content-Type: application/json" \
  -d '{
    "originCity": "Delhi, IN",
    "destinationCity": "Jaipur, IN",
    "numDays": 3,
    "numPeople": 2
  }'
```

Expected: Train estimate should include SL, 3A, 2A, and 1A classes

## Free Tier Limits

All APIs used are free tier compatible:

1. **OpenRouteService**: 2000 requests/day (free) - Reduced usage with caching
2. **Google Places API**: $200 credit/month (free tier) - Optional
3. **OpenTripMap**: Free tier available
4. **Nominatim**: Free (respect usage policy)
5. **Overpass API**: Free (respect usage policy)
6. **Booking Platforms**: Deep links (no API calls, just URL generation)

## Troubleshooting

### Issue: Google Places ratings not showing
- Verify `GOOGLE_PLACES_API_KEY` is set in `.env`
- Check API key has Places API enabled
- Verify billing is enabled (free tier credits apply)
- Check API quotas in Google Cloud Console

### Issue: Route caching not working
- Verify route coordinates are stable (within 100m)
- Check cache is being used (response includes `"cached": true` for subsequent requests)
- Cache expires after 1 hour automatically

### Issue: MakeMyTrip/Goibibo links not showing
- Verify destination is in India (coordinates or city name)
- Check city name contains India-related keywords
- Verify coordinates are within India bounds (8°N-37°N, 68°E-97°E)

### Issue: Train options not showing
- Verify both origin and destination are in India
- Check distance is within 1200km (train estimates only for short distances)
- Verify train estimate is being calculated correctly
