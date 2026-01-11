from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import math
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from models.schemas import PlanTripRequest, PlanTripResponse
from services.free_places_service import FreePlacesService
from services.ai_service import AiService
from storage.sqlite_repository import SQLiteRepository
from storage.mongo_repository import MongoRepository
from utils.cost_estimator import CostEstimator
from auth.security import create_access_token, decode_token, hash_password, verify_password
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserPublic


def get_env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


load_dotenv()  # load variables from .env if present

app = FastAPI(title="Travel Planner (Free Providers + Groq)")

# CORS: during local dev, allow all; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Instantiate services (lazy)
_places_service: Optional[FreePlacesService] = None
_ai_service: Optional[AiService] = None
_repo: Optional[object] = None
_cost_estimator: Optional[CostEstimator] = None
_db_backend: Optional[str] = None


def get_services():
    global _places_service, _ai_service, _repo, _cost_estimator, _db_backend
    if _places_service is None:
        _places_service = FreePlacesService(
            opentripmap_api_key=get_env("OPENTRIPMAP_API_KEY"),
            nominatim_email=os.getenv("NOMINATIM_EMAIL"),
            google_places_api_key=os.getenv("GOOGLE_PLACES_API_KEY"),  # Optional
        )
    if _ai_service is None:
        _ai_service = AiService(api_key=get_env("GROQ_API_KEY"))
    if _db_backend is None:
        _db_backend = os.getenv("DB_BACKEND", "sqlite").lower()
    if _repo is None:
        if _db_backend == "mongo":
            mongo_uri = get_env("MONGODB_URI")
            mongo_db = get_env("MONGO_DB")
            _repo = MongoRepository(uri=mongo_uri, db_name=mongo_db)
        else:
            _repo = SQLiteRepository(db_path=os.getenv("SQLITE_PATH", "./data.db"))
    if _cost_estimator is None:
        default_currency = os.getenv("DEFAULT_CURRENCY", "INR")
        _cost_estimator = CostEstimator(default_currency=default_currency)
    return _places_service, _ai_service, _repo, _cost_estimator


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/cities")
def cities(q: str):
    try:
        places_service, _, __, ___ = get_services()
        return places_service.search_cities(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#
# Auth endpoints (enabled when DB_BACKEND=mongo)
#
def _get_current_user(authorization: Optional[str] = None):
    token = None
    if authorization and isinstance(authorization, str) and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        return None
    secret = get_env("JWT_SECRET", "dev-secret")
    payload = decode_token(token, secret)
    if not payload:
        return None
    user_id = payload.get("sub")
    _, __, repo, ___ = get_services()
    if not isinstance(repo, MongoRepository):
        return None
    return repo.get_user_by_id(user_id)


@app.post("/auth/register", response_model=TokenResponse)
def register(body: RegisterRequest):
    _, __, repo, ___ = get_services()
    if not isinstance(repo, MongoRepository):
        raise HTTPException(status_code=400, detail="Auth requires DB_BACKEND=mongo")
    existing = repo.get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = repo.create_user(email=body.email, password_hash=hash_password(body.password))
    token = create_access_token(user["id"], get_env("JWT_SECRET", "dev-secret"), int(os.getenv("JWT_EXPIRE_MINUTES", "60")))
    return TokenResponse(accessToken=token, user=UserPublic(id=user["id"], email=user["email"], createdAt=user.get("createdAt")))


@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    _, __, repo, ___ = get_services()
    if not isinstance(repo, MongoRepository):
        raise HTTPException(status_code=400, detail="Auth requires DB_BACKEND=mongo")
    user = repo.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["id"], get_env("JWT_SECRET", "dev-secret"), int(os.getenv("JWT_EXPIRE_MINUTES", "60")))
    return TokenResponse(accessToken=token, user=UserPublic(id=user["id"], email=user["email"], createdAt=user.get("createdAt")))


@app.get("/me", response_model=UserPublic)
def me(authorization: Optional[str] = Header(default=None)):
    user = _get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return UserPublic(id=user["id"], email=user["email"], createdAt=user.get("createdAt"))


@app.get("/me/trips")
def list_my_trips(limit: int = 20, authorization: Optional[str] = Header(default=None)):
    """
    List recent itineraries for the authenticated user (MongoDB backend only).
    """
    _, __, repo, ___ = get_services()
    if not isinstance(repo, MongoRepository):
        raise HTTPException(status_code=400, msg="Trips endpoint requires DB_BACKEND=mongo")
    user = _get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        items = repo.list_itineraries_for_user(user["id"], limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"items": items}


@app.post("/api/plan-trip", response_model=PlanTripResponse)
async def plan_trip(req: PlanTripRequest, authorization: Optional[str] = Header(default=None)):
    try:
        places_service, ai_service, repo, cost_estimator = get_services()

        # Geocode origin/destination
        origin_geo = places_service.geocode_city(req.originCity)
        dest_geo = places_service.geocode_city(req.destinationCity)

        # Nearby airports (for heuristic flight estimate)
        # Improved airport detection that prioritizes commercial airports with IATA codes
        origin_airport = places_service.find_nearest_airport(origin_geo["lat"], origin_geo["lng"])
        dest_airport = places_service.find_nearest_airport(dest_geo["lat"], dest_geo["lng"])
        
        # Get route information from airport to destination (for cases like Bagdogra to Gangtok)
        # Include multiple transport options: taxi, bus, shared taxi
        route_info = None
        if dest_airport.get("name") and dest_airport.get("lat") and dest_airport.get("lng"):
            # Check if destination city is far from airport (more than 10km)
            import math
            airport_lat = dest_airport["lat"]
            airport_lng = dest_airport["lng"]
            dlat = math.radians(dest_geo["lat"] - airport_lat)
            dlng = math.radians(dest_geo["lng"] - airport_lng)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(airport_lat)) * math.cos(math.radians(dest_geo["lat"])) * math.sin(dlng/2)**2
            dist_km = 2 * math.asin(math.sqrt(a)) * 6371
            
            if dist_km > 10:  # If destination is more than 10km from airport
                # Get all ground transport options (taxi, bus, shared taxi)
                route_info = places_service.get_all_ground_transport_options(
                    airport_lat, airport_lng,
                    dest_geo["lat"], dest_geo["lng"]
                )
                # Also include primary route info for backward compatibility
                route_info["primary"] = route_info.get("taxi", {})

        # Attractions and Hotels near destination
        attractions = places_service.find_attractions(dest_geo["lat"], dest_geo["lng"])
        # Pass destination city name for better booking links
        # Extract clean city name - handle formats like "Gangtok, Sikkim, IN" or "New Delhi, IN"
        destination_parts = req.destinationCity.split(',')
        destination_city = destination_parts[0].strip()  # Get first part (main city name)
        # If we have a state/region, use it too (e.g., "Gangtok, Sikkim" not just "Gangtok")
        if len(destination_parts) > 1 and destination_parts[1].strip().lower() not in ['in', 'india', 'us', 'usa', 'uk', 'gb']:
            destination_city = f"{destination_city}, {destination_parts[1].strip()}"
        
        # Get destination country code for hotel validation
        dest_country_code = dest_geo.get("country_code", "").lower()
        
        hotels_result = places_service.find_hotels(
            dest_geo["lat"], dest_geo["lng"], 
            city=destination_city, 
            limit=30,  # Get more hotels to filter strictly
            destination_country_code=dest_country_code  # Pass country for validation
        )
        hotels = hotels_result.get("hotels", [])
        
        # STRICT additional filter: Double-check distance for ALL destinations (not just international)
        # Filtering in find_hotels should be sufficient, but this is a safety check
        import math
        validated_hotels = []
        max_distance_km = 30 if dest_country_code != 'in' else 35  # Stricter for international
        
        for hotel in hotels:
            hotel_lat = hotel.get("lat")
            hotel_lng = hotel.get("lng")
            if hotel_lat and hotel_lng:
                try:
                    # Calculate distance from destination
                    dlat = math.radians(hotel_lat - dest_geo["lat"])
                    dlng = math.radians(hotel_lng - dest_geo["lng"])
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(dest_geo["lat"])) * math.cos(math.radians(hotel_lat)) * math.sin(dlng/2)**2
                    dist_km = 2 * math.asin(math.sqrt(a)) * 6371
                    
                    if dist_km <= max_distance_km:
                        # For international destinations, also verify country
                        if dest_country_code != 'in':
                            hotel_country = places_service.reverse_geocode_country(hotel_lat, hotel_lng)
                            if hotel_country and hotel_country.lower() == dest_country_code:
                                validated_hotels.append(hotel)
                        else:
                            # For India, distance check is sufficient
                            validated_hotels.append(hotel)
                except Exception:
                    # Skip if validation fails
                    pass
        
        # Limit to fewer hotels - show only top 2-3, rest via Booking.com link
        # Sort by rating (highest first) to show best hotels
        hotels = sorted(validated_hotels, key=lambda h: (h.get("rating") or 0, h.get("user_ratings_total") or 0), reverse=True)[:3]  # Show only top 3 hotels directly
        # Store city_links separately if needed for frontend
        hotels_with_metadata = hotels_result

        # Estimate costs
        flight_estimate = cost_estimator.estimate_flights(
            origin_airport=origin_airport,
            destination_airport=dest_airport,
            num_people=req.numPeople,
            origin_city=req.originCity,
            destination_city=req.destinationCity,
        )
        hotel_estimate = cost_estimator.estimate_hotels(
            hotels=hotels,
            num_days=req.numDays,
            num_people=req.numPeople,
        )
        other_costs_estimate = cost_estimator.estimate_other_costs(
            num_days=req.numDays,
            num_people=req.numPeople,
            city_price_level=cost_estimator.derive_city_price_level(hotels, attractions),
        )

        # Compute train estimate for short intra-India trips
        train_estimate = None
        try:
            origin_cc = (origin_geo.get("country_code") or "").lower()
            dest_cc = (dest_geo.get("country_code") or "").lower()
            if origin_cc == "in" and dest_cc == "in":
                dist_km = cost_estimator.compute_distance_km(
                    origin_geo["lat"], origin_geo["lng"], dest_geo["lat"], dest_geo["lng"]
                )
                if dist_km <= 1200:
                    train_estimate = cost_estimator.estimate_train(
                        {"lat": origin_geo["lat"], "lng": origin_geo["lng"]},
                        {"lat": dest_geo["lat"], "lng": dest_geo["lng"]},
                    )
        except Exception:
            train_estimate = None

        # Use AI to produce a structured itinerary using gathered data
        itinerary = await ai_service.generate_itinerary(
            req=req,
            origin_geo=origin_geo,
            dest_geo=dest_geo,
            attractions=attractions,
            hotels=hotels,
            flight_estimate=flight_estimate,
            hotel_estimate=hotel_estimate,
            other_costs_estimate=other_costs_estimate,
            train_estimate=train_estimate,
            route_info=route_info,
            dest_airport=dest_airport,
        )

        # CRITICAL FIX: Extract cities STRICTLY - only destination city by default
        # Only extract other cities if they're EXPLICITLY mentioned as places being visited
        import re
        destination_city_name = destination_city.split(',')[0].strip()
        destination_lower = destination_city_name.lower()
        daily_plan = itinerary.get("dailyPlan", [])
        
        # STRICT city extraction - only extract cities explicitly mentioned as visit destinations
        explicitly_mentioned_cities = set()
        
        for day_plan in daily_plan:
            items = day_plan.get("items", [])
            for item in items:
                item_lower = item.lower()
                
                # Only extract cities that are CLEARLY being visited, not just mentioned
                # Pattern 1: "Visit CityName", "Travel to CityName", "Go to CityName", "Stay in CityName"
                explicit_visits = re.findall(r'\b(?:visit|travel to|go to|head to|stay in|stay at|arrive in|arrive at|explore)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', item, re.IGNORECASE)
                for city_match in explicit_visits:
                    city_normalized = city_match.strip()
                    city_lower = city_normalized.lower()
                    # Only add if it's clearly different from destination and makes sense
                    if city_lower != destination_lower and len(city_normalized) > 2:
                        # Check if it's a reasonable city name (starts with capital, not common words)
                        if city_normalized not in ["Morning", "Afternoon", "Evening", "Hotel", "Airport", "Local", "Nearby"]:
                            explicitly_mentioned_cities.add(city_normalized)
                
                # Pattern 2: CityName with landmark (e.g., "Jaipur City Palace")
                city_landmarks = re.findall(r'\b([A-Z][a-z]+)\s+(?:City\s+)?(?:Fort|Palace|Lake|Temple|Market|Airport|Museum)\b', item)
                for city_match in city_landmarks:
                    city_lower = city_match.lower()
                    if city_lower != destination_lower and city_match not in ["The", "New", "Old", "Local"]:
                        explicitly_mentioned_cities.add(city_match)
        
        # ALWAYS use destination city as PRIMARY - this is the main city for hotels
        cities_to_fetch = [destination_city_name]
        
        # Validate and add other cities only if they make geographic sense
        for city in explicitly_mentioned_cities:
            if city.lower() == destination_lower:
                continue  # Skip if it's the destination city
            
            try:
                # Verify this city is reasonably close to destination (within ~300km)
                test_city_geo = places_service.geocode_city(f"{city}, IN")
                dest_geo_test = places_service.geocode_city(destination_city)
                lat_diff = abs(test_city_geo["lat"] - dest_geo_test["lat"])
                lng_diff = abs(test_city_geo["lng"] - dest_geo_test["lng"])
                # 2.7 degrees ≈ 300km at Indian latitudes
                if lat_diff < 2.7 and lng_diff < 2.7:
                    cities_to_fetch.append(city)
                    logger.info(f"Adding validated city: {city} (distance: {lat_diff:.2f}, {lng_diff:.2f} degrees)")
                else:
                    logger.info(f"Excluding {city} - too far from {destination_city_name}")
            except:
                # If geocoding fails, skip this city
                pass
        
        # Fetch hotels - DESTINATION CITY IS PRIMARY
        hotels_by_city = {}
        all_hotels_list = []
        
        # PRIORITY 1: Fetch hotels for DESTINATION CITY ONLY (this should be the main source)
        try:
            dest_geo = places_service.geocode_city(destination_city)
            dest_hotels_result = places_service.find_hotels(
                dest_geo["lat"], dest_geo["lng"], 
                city=destination_city_name, limit=15
            )
            dest_hotels = dest_hotels_result.get("hotels", [])
            if dest_hotels:
                # STRICT filtering: only include hotels actually near destination coordinates
                filtered_dest_hotels = []
                for hotel in dest_hotels:
                    hotel_lat = hotel.get("lat") or (hotel.get("center", {}).get("lat") if isinstance(hotel.get("center"), dict) else None)
                    hotel_lng = hotel.get("lng") or (hotel.get("center", {}).get("lng") if isinstance(hotel.get("center"), dict) else None) or hotel.get("lon")
                    
                    if hotel_lat and hotel_lng:
                        # STRICT distance check: within ~35km of destination center
                        lat_diff = abs(hotel_lat - dest_geo["lat"])
                        lng_diff = abs(hotel_lng - dest_geo["lng"])
                        # 0.31 degrees ≈ 35km at Indian latitudes - strict radius
                        if lat_diff < 0.31 and lng_diff < 0.31:
                            hotel["city"] = destination_city_name
                            filtered_dest_hotels.append(hotel)
                
                if filtered_dest_hotels:
                    hotels_by_city[destination_city_name] = filtered_dest_hotels
                    # Sort by rating and take top 3
                    filtered_dest_hotels_sorted = sorted(filtered_dest_hotels, key=lambda h: (h.get("rating") or 0, h.get("user_ratings_total") or 0), reverse=True)
                    all_hotels_list.extend(filtered_dest_hotels_sorted[:3])  # Limit destination hotels to top 3
                    logger.info(f"Found {len(filtered_dest_hotels)} hotels in {destination_city_name}")
        except Exception as e:
            logger.error(f"Failed to fetch hotels for destination {destination_city_name}: {e}")
        
        # PRIORITY 2: Fetch hotels for other validated cities (if any exist)
        for city_name in cities_to_fetch[1:]:  # Skip first (destination)
            try:
                city_geo = places_service.geocode_city(f"{city_name}, IN")
                city_hotels_result = places_service.find_hotels(
                    city_geo["lat"], city_geo["lng"], 
                    city=city_name, limit=4  # Fewer hotels for secondary cities
                )
                city_hotels = city_hotels_result.get("hotels", [])
                if city_hotels:
                    filtered_city_hotels = []
                    for hotel in city_hotels:
                        hotel_lat = hotel.get("lat") or (hotel.get("center", {}).get("lat") if isinstance(hotel.get("center"), dict) else None)
                        hotel_lng = hotel.get("lng") or (hotel.get("center", {}).get("lng") if isinstance(hotel.get("center"), dict) else None) or hotel.get("lon")
                        
                        if hotel_lat and hotel_lng:
                            lat_diff = abs(hotel_lat - city_geo["lat"])
                            lng_diff = abs(hotel_lng - city_geo["lng"])
                            if lat_diff < 0.25 and lng_diff < 0.25:  # Strict: within ~28km
                                hotel["city"] = city_name
                                filtered_city_hotels.append(hotel)
                    
                    if filtered_city_hotels:
                        hotels_by_city[city_name] = filtered_city_hotels
                        # Sort by rating and take top 2
                        filtered_city_hotels_sorted = sorted(filtered_city_hotels, key=lambda h: (h.get("rating") or 0, h.get("user_ratings_total") or 0), reverse=True)
                        all_hotels_list.extend(filtered_city_hotels_sorted[:2])  # Max 2 hotels per secondary city
            except Exception as e:
                logger.error(f"Failed to fetch hotels for {city_name}: {e}")
                continue
        
        # Use hotels from itinerary if AI suggested them, otherwise use fetched hotels
        ai_hotels = itinerary.get("hotels", [])
        if isinstance(ai_hotels, list) and ai_hotels:
            # Merge AI hotels with fetched hotels by city
            final_hotels = []
            # Group AI hotels by checking if they match fetched cities
            for ai_hotel in ai_hotels:
                hotel_name = ai_hotel.get("name", "").lower()
                # Try to match AI hotel with fetched hotels
                matched = False
                for city, city_hotels in hotels_by_city.items():
                    for city_hotel in city_hotels:
                        if city_hotel.get("name", "").lower() == hotel_name:
                            # Use fetched hotel (has booking links) but keep AI hotel data
                            merged = {**city_hotel, **{k: v for k, v in ai_hotel.items() 
                                    if k not in ["lat", "lng", "place_id", "booking_links"] and v}}
                            final_hotels.append(merged)
                            matched = True
                            break
                    if matched:
                        break
                
                if not matched:
                    # If AI hotel doesn't match any fetched hotel, use it as-is if it has coordinates
                    if ai_hotel.get("lat") and ai_hotel.get("lng"):
                        final_hotels.append(ai_hotel)
            
            # Add hotels from cities that might not have been in AI suggestions
            for city, city_hotels in hotels_by_city.items():
                city_hotel_names = {h.get("name", "").lower() for h in final_hotels}
                for city_hotel in city_hotels[:2]:  # Add up to 2 hotels per city
                    if city_hotel.get("name", "").lower() not in city_hotel_names:
                        city_hotel["city"] = city  # Tag with city name
                        final_hotels.append(city_hotel)
            
            # Sort by rating and limit to top 3
            hotels_to_show = sorted(final_hotels, key=lambda h: (h.get("rating") or 0, h.get("user_ratings_total") or 0), reverse=True)[:3]  # Show only top 3 hotels directly
        else:
            # No AI hotels, use fetched hotels grouped by city - sort by rating and limit to top 3
            hotels_to_show = sorted(all_hotels_list, key=lambda h: (h.get("rating") or 0, h.get("user_ratings_total") or 0), reverse=True)[:3]  # Show only top 3 hotels directly
        
        # Match hotels to specific days in the itinerary
        # Extract hotel names and cities mentioned in daily plan items
        hotels_by_day = {}
        daily_plan = itinerary.get("dailyPlan", [])
        
        for day_plan in daily_plan:
            day_num = day_plan.get("day", 1)
            items = day_plan.get("items", [])
            day_hotels = []
            day_cities = set()
            
            # First, extract cities mentioned in this day's items (only validated cities)
            for item in items:
                item_lower = item.lower()
                # Check which validated cities are mentioned in this day
                for city in cities_to_fetch:
                    city_lower = city.lower()
                    # Check if city name appears in item (as whole word or major part)
                    if city_lower in item_lower:
                        # Filter out false positives (especially for Jammu vs other cities)
                        if not any(skip in item_lower for skip in ["jammu airport", "jammu market", "jammu city"]):
                            day_cities.add(city)
                        elif "jammu" in city_lower and "jammu" in item_lower and "airport" not in item_lower and "market" not in item_lower:
                            day_cities.add(city)
            
            # If no city found, try to extract city from hotel mentions or check destination
            if not day_cities:
                # Check for hotel mentions with city context
                for item in items:
                    item_lower = item.lower()
                    # If check-in/check-out mentioned, this is likely the main destination city
                    if any(keyword in item_lower for keyword in ["check-in", "check-out", "check in", "check out"]):
                        # Use destination city as default for check-in/check-out days
                        main_city = destination_city.split(',')[0].strip()
                        day_cities.add(main_city)
            
            # Assign hotels from cities mentioned in this day
            for city in day_cities:
                if city in hotels_by_city:
                    # Add top 2 hotels from this city for this day
                    for hotel in hotels_by_city[city][:2]:
                        hotel_with_day = {**hotel, "day": day_num, "city": city}
                        # Avoid duplicates
                        if not any(h.get("name") == hotel_with_day.get("name") for h in day_hotels):
                            day_hotels.append(hotel_with_day)
            
            # Also try to match specific hotel names mentioned in items
            for item in items:
                item_lower = item.lower()
                # Look for hotel name patterns
                hotel_patterns = [
                    r'check-?in\s+(?:at|to)?\s+([A-Z][A-Za-z\s&\-]+?)(?:\s|$|,|\.|Hotel)',
                    r'stay\s+(?:at|in)?\s+([A-Z][A-Za-z\s&\-]+?)(?:\s|$|,|\.)',
                    r'at\s+([A-Z][A-Za-z\s&\-]+?\s+Hotel)',
                    r'hotel\s+([A-Z][A-Za-z\s&\-]+?)(?:\s|$|,|\.|,)',
                ]
                
                for pattern in hotel_patterns:
                    matches = re.findall(pattern, item)
                    for match in matches:
                        hotel_name_candidate = match.strip()
                        # Clean up hotel name - remove common suffixes
                        hotel_name_candidate = re.sub(r'\s+(Hotel|Palace|Resort|Inn|Lodge)$', '', hotel_name_candidate, flags=re.IGNORECASE).strip()
                        hotel_name_candidate = re.sub(r'\s+', ' ', hotel_name_candidate)
                        
                        if len(hotel_name_candidate) < 3:
                            continue
                        
                        # Find matching hotel from fetched hotels by city
                        for city in day_cities:
                            if city in hotels_by_city:
                                for hotel in hotels_by_city[city]:
                                    hotel_name = hotel.get("name", "").lower()
                                    candidate_lower = hotel_name_candidate.lower()
                                    
                                    # Flexible matching - check if significant words match
                                    hotel_words = set(word for word in hotel_name.split() if len(word) > 2)
                                    candidate_words = set(word for word in candidate_lower.split() if len(word) > 2)
                                    
                                    # If hotel name contains significant words from candidate
                                    if candidate_words and hotel_words.intersection(candidate_words):
                                        hotel_with_day = {**hotel, "day": day_num, "city": city}
                                        if not any(h.get("name") == hotel_with_day.get("name") for h in day_hotels):
                                            day_hotels.insert(0, hotel_with_day)  # Prepend if matched by name
                                            break
            
            # If we have hotels for this day, store them
            if day_hotels:
                hotels_by_day[day_num] = day_hotels
        
        # Combine city links from all cities
        combined_city_links = hotels_result.get("city_links", {})
        
        # Add hotels metadata with grouped hotels and day assignments
        itinerary["hotels"] = {
            "hotels": hotels_to_show,
            "hotels_by_city": hotels_by_city,  # Grouped by city for frontend
            "hotels_by_day": hotels_by_day,  # Grouped by day for frontend
            "count": len(hotels_to_show),
            "cities_mentioned": list(cities_to_fetch),
            "city_links": combined_city_links,
            "note": f"Hotels for: {', '.join(sorted(cities_to_fetch)[:5])}" if cities_to_fetch else hotels_result.get("note", "")
        }

        # Compose response and persist
        response = PlanTripResponse(**itinerary)
        current = _get_current_user(authorization)
        user_id = current["id"] if (current and isinstance(repo, MongoRepository)) else None
        
        try:
            # Save with proper structure (hotels as list for storage compatibility)
            save_dict = response.model_dump()
            save_dict["hotels"] = hotels  # Save as list for backward compatibility
            itinerary_id = repo.save_itinerary(save_dict, user_id=user_id)
        except TypeError:
            save_dict = response.model_dump()
            save_dict["hotels"] = hotels  # Save as list for backward compatibility
            itinerary_id = repo.save_itinerary(save_dict)
        
        response.itineraryId = itinerary_id
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

