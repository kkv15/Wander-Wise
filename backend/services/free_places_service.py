import os
import time
import httpx
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus
import hashlib
import json


class FreePlacesService:
    """
    Uses only free/no-card services:
    - Geocoding: Nominatim (OpenStreetMap) - follow usage policy, low-volume only.
    - Attractions: OpenTripMap (free API key).
    - Hotels: Overpass API (OSM) for tourism=hotel|hostel|guest_house|apartment within radius.
    - Airports: Overpass API for aeroway=aerodrome (nearest).
    """

    def __init__(self, opentripmap_api_key: str, nominatim_email: Optional[str] = None, google_places_api_key: Optional[str] = None):
        self.opentripmap_api_key = opentripmap_api_key
        self.nominatim_email = nominatim_email
        self.google_places_api_key = google_places_api_key
        self.http = httpx.Client(timeout=20.0)
        self._ua = f"travel-planner/1.0 (+https://example.com) {nominatim_email or ''}"
        # Overpass mirrors (configurable via env)
        env_eps = os.getenv("OVERPASS_ENDPOINTS")
        if env_eps:
            self.overpass_endpoints = [e.strip() for e in env_eps.split(",") if e.strip()]
        else:
            self.overpass_endpoints = [
                "https://overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter",
            ]
        # Route cache: simple in-memory cache with TTL (1 hour)
        self._route_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 hour in seconds

    def geocode_city(self, city: str) -> Dict[str, Any]:
        params = {"q": city, "format": "json", "limit": 1, "accept-language": "en", "addressdetails": 1}
        headers = {"User-Agent": self._ua, "Accept-Language": "en"}
        if self.nominatim_email:
            params["email"] = self.nominatim_email
        resp = self.http.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"Could not geocode city: {city}")
        top = data[0]
        address = top.get("address") or {}
        country_code = (address.get("country_code") or "").lower()
        return {"lat": float(top["lat"]), "lng": float(top["lon"]), "formatted": top.get("display_name"), "country_code": country_code}

    def search_cities(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query or len(query.strip()) < 2:
            return []
        params = {"q": query.strip(), "format": "json", "limit": limit, "addressdetails": 0, "accept-language": "en"}
        headers = {"User-Agent": self._ua, "Accept-Language": "en"}
        if self.nominatim_email:
            params["email"] = self.nominatim_email
        resp = self.http.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        results: List[Dict[str, Any]] = []
        for item in data:
            display = item.get("display_name")
            lat = item.get("lat")
            lon = item.get("lon")
            if not (display and lat and lon):
                continue
            results.append({"name": display, "lat": float(lat), "lng": float(lon)})
        return results

    def find_attractions(self, lat: float, lng: float, radius: int = 12000, limit: int = 15) -> List[Dict[str, Any]]:
        # OpenTripMap radius search
        params = {
            "radius": radius,
            "lon": lng,
            "lat": lat,
            "rate": 2,  # popularity filter
            "limit": limit,
            "apikey": self.opentripmap_api_key,
        }
        resp = self.http.get("https://api.opentripmap.com/0.1/en/places/radius", params=params)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        results: List[Dict[str, Any]] = []
        for f in features:
            prop = f.get("properties", {})
            point = f.get("geometry", {}).get("coordinates", [])
            if not point or prop.get("name") in (None, ""):
                continue
            xid = prop.get("xid")
            desc = None
            more_url = None
            opening = None
            best_time = None
            if xid:
                try:
                    d = self.http.get(f"https://api.opentripmap.com/0.1/en/places/xid/{xid}", params={"apikey": self.opentripmap_api_key})
                    if d.status_code == 200:
                        dj = d.json()
                        desc = (dj.get("wikipedia_extracts") or {}).get("text") or (dj.get("info") or {}).get("descr")
                        opening = dj.get("opening_hours") or (dj.get("info") or {}).get("opening_hours")
                        # try to guess a best time from text
                        wt = (dj.get("wikipedia_extracts") or {}).get("text") or ""
                        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                        found = [m for m in months if m in wt]
                        if found:
                            best_time = f"{found[0]}–{found[-1]}" if len(found) > 1 else found[0]
                        # Prefer official website if available, else OTM page, else Wikipedia
                        more_url = (dj.get("url") or (dj.get("otm") or (dj.get("wikipedia") or None)))
                except Exception:
                    pass
            results.append({
                "name": prop.get("name"),
                "address": None,
                "rating": None,
                "user_ratings_total": None,
                "lat": point[1],
                "lng": point[0],
                "place_id": xid,
                "photo_reference": None,
                "description": desc,
                "url": more_url,
                "openingHours": opening,
                "bestTimeToVisit": best_time,
            })
        return results

    def _overpass(self, query: str, max_retries: int = 2, per_endpoint_retries: int = 1, backoff_seconds: float = 0.6) -> Dict[str, Any]:
        last_err: Optional[Exception] = None
        for _ in range(max_retries):
            for endpoint in self.overpass_endpoints:
                for _attempt in range(per_endpoint_retries):
                    try:
                        resp = self.http.post(endpoint, data={"data": query}, headers={"User-Agent": self._ua})
                        resp.raise_for_status()
                        return resp.json()
                    except Exception as e:
                        last_err = e
                        time.sleep(backoff_seconds)
        if last_err:
            raise last_err
        return {"elements": []}

    # def _generate_booking_links(self, hotel_name: str, city: str, lat: float, lng: float) -> Dict[str, str]:
    #     """
    #     Generate booking.com and Agoda deep links for a hotel.
    #     These are search links since we don't have direct booking APIs.
    #     """
    #     from urllib.parse import quote_plus
        
    #     # Booking.com search URL
    #     booking_query = quote_plus(f"{hotel_name} {city}")
    #     booking_url = f"https://www.booking.com/search.html?ss={booking_query}&ssne={quote_plus(city)}&ssne_untouched={quote_plus(city)}&checkin_month=&checkin_monthday=&checkin_year=&checkout_month=&checkout_monthday=&checkout_year=&group_adults=&no_rooms=&group_children="
        
    #     # Agoda search URL  
    #     agoda_query = quote_plus(f"{hotel_name} {city}")
    #     agoda_url = f"https://www.agoda.com/search?city={quote_plus(city)}&q={agoda_query}"
        
    #     return {
    #         "booking_com": booking_url,
    #         "agoda": agoda_url
    #     }

    # def _generate_booking_links( self, hotel_name: str,city: str,lat: float,lng: float,adults: int = 2,rooms: int = 1,) -> Dict[str, str]:
       
    #    from urllib.parse import quote_plus

    #    h = quote_plus(hotel_name)
    #    c = quote_plus(city)

    #    return {
    #     "booking_com": (
    #         "https://www.booking.com/search.html"
    #         f"?ss={h}"
    #         f"&ssne={c}"
    #         f"&group_adults={adults}"
    #         f"&no_rooms={rooms}"
    #     ),
    #     "agoda": (
    #         "https://www.agoda.com/search"
    #         f"?city={c}&q={h}&adult={adults}"
    #     ),
    #     "makemytrip": (
    #         "https://www.makemytrip.com/hotels/search"
    #         f"?city={c}&hotelName={h}"
    #         f"&adults={adults}&rooms={rooms}"
    #     ),
    #     "goibibo": (
    #         f"https://www.goibibo.com/hotels/find-hotels-in-{c}/"
    #         f"?q={h}&adults={adults}&rooms={rooms}"
    #     ),
    # }



    # def generate_booking_links(hotel_name, lat, lng):
    #   h = quote_plus(hotel_name)

    #   return {
    #     "booking": (
    #         "https://www.booking.com/search.html"
    #         f"?ss={h}&latitude={lat}&longitude={lng}"
    #     ),
    #     "agoda": (
    #         "https://www.agoda.com/search"
    #         f"?q={h}&lat={lat}&lng={lng}"
    #     )
    # }


    def _generate_booking_links(self, hotel_name: str, city: str, lat: float, lng: float):
      """
      Generate booking links - only Booking.com to avoid complexity.
      Links always include city name to avoid login prompts.
      """
      # Clean city name - remove country suffix if present (e.g., "Delhi, IN" -> "Delhi")
      city_clean = city.split(',')[0].strip()
      
      # URL encode both hotel name and city
      h = quote_plus(hotel_name)
      c = quote_plus(city_clean)
      # Combined search: hotel name + city for better matching
      hc = quote_plus(f"{hotel_name} {city_clean}")

      links = {
        # Hotel-specific link: Include both hotel name and city to avoid login prompts
        "booking_hotel": (
            f"https://www.booking.com/search.html"
            f"?ss={hc}&ssne={c}&ssne_untouched={c}&latitude={lat}&longitude={lng}"
        ),
        # City-level link (more reliable - always show this)
        "booking_city": (
            f"https://www.booking.com/search.html?ss={c}"
        )
      }
      
      return links


    # def find_hotels(self, lat: float, lng: float, radius: int = 5000, limit: int = 15) -> List[Dict[str, Any]]:
    #     """
    #     Find hotels using Overpass API. Returns more results and includes booking links.
    #     Searches with expanding radius to get more hotels.
    #     """
    #     # Overpass: hotels/hostels/guest_house/apartment/resort
    #     def build_query(r: int, lim: int) -> str:
    #         return f"""
    #         [out:json][timeout:25];
    #         (
    #           node["tourism"~"hotel|hostel|guest_house|apartment|resort|motel"](around:{r},{lat},{lng});
    #           way["tourism"~"hotel|hostel|guest_house|apartment|resort|motel"](around:{r},{lat},{lng});
    #           relation["tourism"~"hotel|hostel|guest_house|apartment|resort|motel"](around:{r},{lat},{lng});
    #         );
    #         out center {lim};
    #         """
        
    #     # Try multiple radius values to get more results
    #     all_results = {}
    #     city_name = None
        
    #     for r_try in [radius, radius * 2, radius * 3, 15000]:
    #         try:
    #             data = self._overpass(build_query(r_try, limit * 2))
    #             elements = data.get("elements", [])
                
    #             for el in elements:
    #                 tags = el.get("tags", {})
    #                 name = tags.get("name:en") or tags.get("int_name") or tags.get("name")
    #                 if not name:
    #                     continue
                    
    #                 # Use name as unique key to avoid duplicates
    #                 if name in all_results:
    #                     continue
                    
    #                 if "lat" in el and "lon" in el:
    #                     la, lo = el["lat"], el["lon"]
    #                 else:
    #                     center = el.get("center", {})
    #                     la, lo = center.get("lat"), center.get("lon")
                    
    #                 # Get city name for booking links (first time only)
    #                 if not city_name:
    #                     addr_city = tags.get("addr:city") or tags.get("addr:place")
    #                     if addr_city:
    #                         city_name = addr_city
                    
    #                 osm_type = el.get("type")
    #                 osm_id = el.get("id")
    #                 website = tags.get("website") or tags.get("contact:website")
    #                 phone = tags.get("phone") or tags.get("contact:phone")
                    
    #                 stars = None
    #                 try:
    #                     if "stars" in tags:
    #                         stars = float(str(tags.get("stars")))
    #                 except Exception:
    #                     stars = None
                    
    #                 # Generate booking links
    #                 hotel_city = city_name or "City"  # Fallback if city not found
    #                 booking_links = self._generate_booking_links(name, hotel_city, la, lo)
                    
    #                 all_results[name] = {
    #                     "name": name,
    #                     "address": tags.get("addr:full:en") or tags.get("addr:street") or tags.get("addr:full") or tags.get("addr:city"),
    #                     "rating": None,  # OSM doesn't provide ratings
    #                     "user_ratings_total": None,
    #                     "price_level": None,
    #                     "lat": la,
    #                     "lng": lo,
    #                     "place_id": f"osm-{osm_type}-{osm_id}",
    #                     "photo_reference": None,
    #                     "url": website or booking_links["booking_com"],  # Prefer website, fallback to booking.com
    #                     "stars": stars,
    #                     "booking_links": booking_links,  # Add booking links
    #                     "phone": phone,
    #                 }
                
    #             # Stop if we have enough results
    #             if len(all_results) >= limit:
    #                 break
                    
    #         except Exception:
    #             continue
        
    #     # Convert to list and limit
    #     results = list(all_results.values())[:limit]
    #     return results

    def _enhance_hotel_with_google_places(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance hotel data with Google Places API for better ratings.
        Only works if GOOGLE_PLACES_API_KEY is set.
        """
        if not self.google_places_api_key:
            return hotel
        
        try:
            # Use Google Places Nearby Search
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{hotel['lat']},{hotel['lng']}",
                "radius": 100,  # 100 meters - very close
                "type": "lodging",
                "keyword": hotel.get("name", ""),
                "key": self.google_places_api_key
            }
            
            resp = self.http.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            results = data.get("results", [])
            if results:
                # Find best matching hotel by name similarity
                hotel_name_lower = hotel.get("name", "").lower()
                best_match = None
                for place in results:
                    place_name = place.get("name", "").lower()
                    # Simple matching: check if hotel name appears in place name or vice versa
                    if hotel_name_lower in place_name or place_name in hotel_name_lower or \
                       any(word in place_name for word in hotel_name_lower.split() if len(word) > 3):
                        best_match = place
                        break
                
                if not best_match and results:
                    # Use first result if no exact match
                    best_match = results[0]
                
                if best_match:
                    # Enhance hotel with Google Places data
                    hotel["rating"] = best_match.get("rating")
                    hotel["user_ratings_total"] = best_match.get("user_ratings_total")
                    hotel["price_level"] = best_match.get("price_level")
                    
                    # Get place details for more info (phone, website, etc.)
                    place_id = best_match.get("place_id")
                    if place_id:
                        try:
                            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                            details_params = {
                                "place_id": place_id,
                                "fields": "formatted_phone_number,website,rating,user_ratings_total",
                                "key": self.google_places_api_key
                            }
                            details_resp = self.http.get(details_url, params=details_params, timeout=10.0)
                            details_resp.raise_for_status()
                            details_data = details_resp.json()
                            result = details_data.get("result", {})
                            
                            if result.get("formatted_phone_number"):
                                hotel["phone"] = result.get("formatted_phone_number")
                            if result.get("website"):
                                hotel["url"] = result.get("website")
                            # Override with details if available (more accurate)
                            if result.get("rating"):
                                hotel["rating"] = result.get("rating")
                            if result.get("user_ratings_total"):
                                hotel["user_ratings_total"] = result.get("user_ratings_total")
                        except Exception:
                            pass  # If details fail, use nearby search data
        except Exception:
            pass  # If Google Places fails, return hotel as-is
        
        return hotel

    def reverse_geocode_country(self, lat: float, lng: float) -> Optional[str]:
        """Reverse geocode to get country code for a given lat/lng."""
        try:
            params = {
                "lat": lat,
                "lon": lng,
                "format": "json",
                "limit": 1,
                "accept-language": "en",
                "addressdetails": 1
            }
            headers = {"User-Agent": self._ua, "Accept-Language": "en"}
            if self.nominatim_email:
                params["email"] = self.nominatim_email
            
            resp = self.http.get("https://nominatim.openstreetmap.org/reverse", params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            address = data.get("address", {})
            country_code = (address.get("country_code") or "").lower()
            return country_code
        except Exception:
            return None

    def find_hotels(self, lat: float, lng: float, city: str, limit: int = 15, destination_country_code: Optional[str] = None):
        """
        Finds hotels using OSM, optionally enhanced with Google Places API for ratings.
        Expands radius automatically.
        Always returns booking & agoda links.
        """

        radius_steps = [5000, 10000, 15000, 25000]
        hotels = {}

        for radius in radius_steps:
            query = f"""
            [out:json][timeout:25];
            (
              node["tourism"~"hotel|hostel|guest_house|apartment|resort"](around:{radius},{lat},{lng});
              way["tourism"~"hotel|hostel|guest_house|apartment|resort"](around:{radius},{lat},{lng});
            );
            out center;
            """

            try:
                data = self._overpass(query)
            except Exception:
                continue

            for el in data.get("elements", []):
                tags = el.get("tags", {})
                name = tags.get("name")

                if not name or name in hotels:
                    continue

                la = el.get("lat") or el.get("center", {}).get("lat")
                lo = el.get("lon") or el.get("center", {}).get("lon")

                if not la or not lo:
                    continue

                hotel = {
                    "name": name,
                    "address": tags.get("addr:full") or tags.get("addr:street") or tags.get("addr:city"),
                    "lat": la,
                    "lng": lo,
                    "place_id": f"osm-{el.get('type')}-{el.get('id')}",
                    "booking_links": self._generate_booking_links(
                        hotel_name=name,
                        city=city,
                        lat=la,
                        lng=lo
                    ),
                    "phone": tags.get("phone") or tags.get("contact:phone"),
                    "url": tags.get("website") or tags.get("contact:website"),
                    "stars": None
                }
                
                # Try to parse stars from OSM
                try:
                    if "stars" in tags:
                        hotel["stars"] = float(str(tags.get("stars")))
                except Exception:
                    pass
                
                # STRICT validation: Hotel must be in destination country AND within reasonable distance
                if destination_country_code:
                    import math
                    # Calculate distance from destination center
                    dlat = math.radians(la - lat)
                    dlng = math.radians(lo - lng)
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(la)) * math.sin(dlng/2)**2
                    dist_km = 2 * math.asin(math.sqrt(a)) * 6371
                    
                    # Strict distance limit: 30km for international, 35km for India
                    max_distance = 30 if destination_country_code != 'in' else 35
                    
                    if dist_km > max_distance:
                        # Hotel is too far from destination, skip it
                        continue
                    
                    # For international destinations, also verify country code
                    if destination_country_code != 'in':
                        try:
                            hotel_country = self.reverse_geocode_country(la, lo)
                            if hotel_country and hotel_country.lower() != destination_country_code.lower():
                                # Hotel is in wrong country, skip it
                                continue
                        except Exception:
                            # If reverse geocoding fails but distance is OK, skip to be safe
                            continue
                
                # Enhance with Google Places API if available
                hotel = self._enhance_hotel_with_google_places(hotel)
                
                hotels[name] = hotel

                if len(hotels) >= limit:
                    break

            if len(hotels) >= limit:
                break

        # Generate city-level links - only Booking.com
        # Clean city name for consistent URL generation
        city_clean = city.split(',')[0].strip()
        c_clean = quote_plus(city_clean)
        
        city_links = {
            "booking_city": f"https://www.booking.com/search.html?ss={c_clean}"
        }

        return {
            "hotels": list(hotels.values()),
            "count": len(hotels),
            "city_links": city_links,
            "note": (
                "Hotel list is limited due to OpenStreetMap coverage. "
                "Use booking links to explore more hotels."
            )
        }


    def find_nearest_airport(self, lat: float, lng: float, radius: int = 80000) -> Dict[str, Any]:
        """
        Find nearest commercial airport, prioritizing airports with IATA codes.
        Searches for aeroway=airport (commercial) first, then aeroway=aerodrome as fallback.
        """
        # First try: Find commercial airports (aeroway=airport) with IATA codes
        def build_airport_query(r: int) -> str:
            return f"""
            [out:json][timeout:25];
            (
              node["aeroway"="airport"]["iata"~"."](around:{r},{lat},{lng});
              way["aeroway"="airport"]["iata"~"."](around:{r},{lat},{lng});
              relation["aeroway"="airport"]["iata"~"."](around:{r},{lat},{lng});
            );
            out center 20;
            """
        
        # Second try: Commercial airports without IATA
        def build_airport_no_iata_query(r: int) -> str:
            return f"""
            [out:json][timeout:25];
            (
              node["aeroway"="airport"](around:{r},{lat},{lng});
              way["aeroway"="airport"](around:{r},{lat},{lng});
              relation["aeroway"="airport"](around:{r},{lat},{lng});
            );
            out center 20;
            """
        
        # Third try: Any aerodrome as fallback
        def build_aerodrome_query(r: int) -> str:
            return f"""
            [out:json][timeout:25];
            (
              node["aeroway"="aerodrome"](around:{r},{lat},{lng});
              way["aeroway"="aerodrome"](around:{r},{lat},{lng});
              relation["aeroway"="aerodrome"](around:{r},{lat},{lng});
            );
            out center 20;
            """
        
        data = {}
        best = None
        
        # Try commercial airports with IATA first
        for r_try in [radius, 100000, 150000]:  # Expand search if needed
            try:
                data = self._overpass(build_airport_query(r_try))
                if data.get("elements"):
                    break
            except Exception:
                pass
        
        # If no IATA airports, try commercial airports without IATA
        if not data.get("elements"):
            for r_try in [radius, 100000]:
                try:
                    data = self._overpass(build_airport_no_iata_query(r_try))
                    if data.get("elements"):
                        break
                except Exception:
                    pass
        
        # Fallback to any aerodrome
        if not data.get("elements"):
            for r_try in [radius, 50000, 30000]:
                try:
                    data = self._overpass(build_aerodrome_query(r_try))
                    if data.get("elements"):
                        break
                except Exception:
                    pass
        
        # Find best airport - prioritize by:
        # 1. Has IATA code (commercial airport)
        # 2. Is international (has "international" in name or has "ref" tag)
        # 3. Is not a small/local airport (exclude military, private)
        # 4. Distance (closer is better among qualified airports)
        import math
        
        # Known major airports that should be preferred (case-insensitive matching)
        # Indian airports
        major_airport_names = [
            "kempegowda", "kial", "bengaluru", "bangalore", "blr",
            "bagdogra", "ixb",
            "indira gandhi", "delhi", "diag", "palam",
            "chhatrapati shivaji", "mumbai", "csia",
            "netaji subhash chandra bose", "kolkata", "ccu",
            "rajiv gandhi", "hyderabad", "rgia",
            "chennai", "maa",
            "pune", "pnq"
        ]
        # Thailand airports (prioritize commercial airports)
        thailand_airports = [
            "suvarnabhumi", "bkk", "bangkok international",
            "don mueang", "dmk", "don muang",
            "phuket", "hkt", "phuket international",
            "chiang mai", "cnx", "chiang mai international",
            "hat yai", "hdy", "krabi", "kbv", "samui", "usm",
            "utapao", "utp", "pattaya", "chiang rai", "cei",
            "krabi international", "ko samui", "trang", "tsg"
        ]
        # Other major international airports
        international_airports = [
            "suvarnabhumi", "bkk", "don mueang", "dmk", "phuket", "hkt",
            "singapore changi", "sin", "kuala lumpur", "klia", "kul",
            "changi", "dubai", "dxb", "doha", "doh", "istanbul", "ist"
        ]
        all_major_airports = major_airport_names + thailand_airports + international_airports
        
        candidates = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            if "lat" in el and "lon" in el:
                la, lo = el["lat"], el["lon"]
            else:
                center = el.get("center", {})
                la, lo = center.get("lat"), center.get("lon")
            
            name = (tags.get("name:en") or tags.get("int_name") or tags.get("name") or "").lower()
            iata = tags.get("iata")
            if iata:
                iata = str(iata).strip('"\'').upper()
            
            # STRICT filtering: Skip military, private, air force bases, and suspicious facilities
            skip_keywords = [
                "military", "air force", "naval", "army", "airforce", "airbase", "air base", 
                "airbase", "khok kathiam", "khok", "kathiam", "takhli", "udorn", 
                "korat", "wing", "squadron", "raf ", "rtaf", "afb", "air force base",
                "airbase", "air force station", "naval air", "army air", "defense",
                "royal thai air force", "rtafb", "usaf", "us air force"
            ]
            if any(skip in name for skip in skip_keywords):
                continue
            
            # Additional check: if airport name contains suspicious patterns, skip it
            if any(pattern in name for pattern in ["base", "camp", "station", "facility"]):
                # Only skip if it's definitely not a commercial airport
                if "international" not in name and not iata and "airport" not in name:
                    continue
            
            # Calculate distance
            dlat = math.radians(la - lat)
            dlng = math.radians(lo - lng)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(la)) * math.sin(dlng/2)**2
            dist = 2 * math.asin(math.sqrt(a)) * 6371
            
            # Score: higher is better (prioritize quality over proximity)
            score = 0
            if iata:
                score += 200  # Has IATA code (increased priority)
            if "international" in name:
                score += 150   # International airport (high priority)
            if any(major in name for major in all_major_airports):
                score += 100   # Known major/commercial airport
            # Special boost for Thailand commercial airports
            if any(th in name for th in thailand_airports):
                score += 125
            if tags.get("ref"):  # Airport reference code
                score += 50
            # Penalty for suspicious names (small bases, etc.)
            if any(sus in name for sus in ["base", "camp", "facility", "wing"]):
                if "international" not in name and not iata:
                    score -= 100  # Heavy penalty
            
            # Small distance penalty (quality matters more than proximity)
            score -= dist / 15  # Reduced penalty to prioritize quality
            
            candidates.append({
                "score": score,
                "dist": dist,
                "name": tags.get("name:en") or tags.get("int_name") or tags.get("name") or "Airport",
                "iata": iata,
                "lat": la,
                "lng": lo,
                "place_id": f"osm-{el.get('type')}-{el.get('id')}",
                "tags": tags
            })
        
        if candidates:
            # Sort by score (highest first), then by distance
            candidates.sort(key=lambda x: (-x["score"], x["dist"]))
            best = {
                "name": candidates[0]["name"],
                "iata": candidates[0]["iata"],
                "lat": candidates[0]["lat"],
                "lng": candidates[0]["lng"],
                "place_id": candidates[0]["place_id"]
            }
        
        return best or {"name": None, "iata": None, "lat": lat, "lng": lng, "place_id": None}

    def _get_cache_key(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, profile: str) -> str:
        """Generate cache key for route"""
        # Round coordinates to ~100m precision for caching (about 0.001 degrees)
        key_data = {
            "origin": (round(origin_lat, 3), round(origin_lng, 3)),
            "dest": (round(dest_lat, 3), round(dest_lng, 3)),
            "profile": profile
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _clean_cache(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self._route_cache.items()
            if current_time - value.get("timestamp", 0) > self._cache_ttl
        ]
        for key in expired_keys:
            del self._route_cache[key]

    def get_route_directions(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, profile: str = "driving-car") -> Dict[str, Any]:
        """
        Get route directions using OpenRouteService API (free tier: 2000 requests/day).
        Returns route information including distance, duration, and steps.
        Results are cached for 1 hour to reduce API calls.
        
        Args:
            origin_lat, origin_lng: Starting point coordinates
            dest_lat, dest_lng: Destination coordinates  
            profile: Route profile - "driving-car", "foot-walking", "cycling-regular", "driving-hgv", etc.
        """
        # Check cache first
        cache_key = self._get_cache_key(origin_lat, origin_lng, dest_lat, dest_lng, profile)
        self._clean_cache()  # Clean expired entries periodically
        
        if cache_key in self._route_cache:
            cached_result = self._route_cache[cache_key].get("data")
            if cached_result:
                return {**cached_result, "cached": True}
        
        # Check if OpenRouteService API key is available
        api_key = os.getenv("OPENROUTESERVICE_API_KEY")
        if not api_key:
            # Return basic route info without API call
            import math
            # Simple distance calculation
            dlat = math.radians(dest_lat - origin_lat)
            dlng = math.radians(dest_lng - origin_lng)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(origin_lat)) * math.cos(math.radians(dest_lat)) * math.sin(dlng/2)**2
            dist_km = 2 * math.asin(math.sqrt(a)) * 6371
            # Rough duration estimate (assuming average speed)
            if profile == "driving-car":
                duration_min = int((dist_km / 60) * 60)  # 60 km/h average
            elif profile == "foot-walking":
                duration_min = int((dist_km / 5) * 60)  # 5 km/h walking
            elif "bus" in profile or profile == "driving-hgv":  # Bus or truck
                duration_min = int((dist_km / 50) * 60)  # 50 km/h average for bus
            else:
                duration_min = int((dist_km / 15) * 60)  # 15 km/h cycling
            
            result = {
                "distance_km": round(dist_km, 2),
                "duration_minutes": duration_min,
                "steps": [],
                "available": False,
                "note": "Route details unavailable (OpenRouteService API key not configured)"
            }
            return result
        
        try:
            # Use OpenRouteService Directions API
            url = f"https://api.openrouteservice.org/v2/directions/{profile}"
            headers = {
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
                "Authorization": api_key
            }
            params = {
                "start": f"{origin_lng},{origin_lat}",
                "end": f"{dest_lng},{dest_lat}"
            }
            
            resp = self.http.get(url, params=params, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            route = data.get("features", [{}])[0]
            properties = route.get("properties", {})
            segments = properties.get("segments", [{}])[0]
            distance_m = segments.get("distance", 0)
            duration_s = segments.get("duration", 0)
            
            steps = []
            for step in segments.get("steps", []):
                instruction = step.get("instruction", "")
                distance_m_step = step.get("distance", 0)
                duration_s_step = step.get("duration", 0)
                steps.append({
                    "instruction": instruction,
                    "distance_km": round(distance_m_step / 1000, 2),
                    "duration_minutes": int(duration_s_step / 60)
                })
            
            result = {
                "distance_km": round(distance_m / 1000, 2),
                "duration_minutes": int(duration_s / 60),
                "steps": steps[:10],  # Limit to first 10 steps
                "available": True
            }
            
            # Cache the result
            self._route_cache[cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            
            return result
        except Exception as e:
            # Fallback to simple calculation
            import math
            dlat = math.radians(dest_lat - origin_lat)
            dlng = math.radians(dest_lng - origin_lng)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(origin_lat)) * math.cos(math.radians(dest_lat)) * math.sin(dlng/2)**2
            dist_km = 2 * math.asin(math.sqrt(a)) * 6371
            duration_min = int((dist_km / 60) * 60) if profile == "driving-car" else int((dist_km / 5) * 60)
            
            result = {
                "distance_km": round(dist_km, 2),
                "duration_minutes": duration_min,
                "steps": [],
                "available": False,
                "note": f"Route API error: {str(e)[:100]}"
            }
            return result
    
    def get_all_ground_transport_options(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Dict[str, Any]:
        """
        Get multiple ground transport options: driving (taxi), bus, and shared taxi.
        Returns a dictionary with options for different transport modes.
        """
        options = {}
        
        # 1. Private taxi/car (driving-car)
        options["taxi"] = self.get_route_directions(origin_lat, origin_lng, dest_lat, dest_lng, profile="driving-car")
        options["taxi"]["mode"] = "taxi"
        options["taxi"]["description"] = "Private taxi or car"
        
        # 2. Bus (driving-hgv is closest approximation for bus routes, or use driving-car as fallback)
        bus_profile = "driving-hgv"  # Heavy goods vehicle profile is closer to bus routes
        options["bus"] = self.get_route_directions(origin_lat, origin_lng, dest_lat, dest_lng, profile=bus_profile)
        options["bus"]["mode"] = "bus"
        options["bus"]["description"] = "Bus service"
        # Bus is typically slower than car, adjust if needed
        if options["bus"]["distance_km"] > 0 and options["taxi"]["distance_km"] > 0:
            # Bus typically takes 1.2-1.5x longer than car
            if options["bus"]["duration_minutes"] == options["taxi"]["duration_minutes"]:
                options["bus"]["duration_minutes"] = int(options["taxi"]["duration_minutes"] * 1.3)
        
        # 3. Shared taxi (similar to taxi but might be slightly slower due to stops)
        options["shared_taxi"] = {**options["taxi"]}
        options["shared_taxi"]["mode"] = "shared_taxi"
        options["shared_taxi"]["description"] = "Shared taxi/cab"
        # Shared taxi might be 10-20% slower due to stops
        if options["shared_taxi"]["duration_minutes"] > 0:
            options["shared_taxi"]["duration_minutes"] = int(options["shared_taxi"]["duration_minutes"] * 1.15)
        
        return options
        


