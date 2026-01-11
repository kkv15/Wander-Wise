import googlemaps
from typing import Dict, Any, List, Optional


class GoogleMapsService:
    """
    Thin wrapper around Google Maps/Places APIs.
    Uses: Geocoding, Places Nearby for 'lodging' and 'tourist_attraction', and airport discovery.
    """

    def __init__(self, api_key: str):
        self.client = googlemaps.Client(key=api_key)

    def geocode_city(self, city: str) -> Dict[str, Any]:
        results = self.client.geocode(city)
        if not results:
            raise ValueError(f"Could not geocode city: {city}")
        location = results[0]["geometry"]["location"]
        return {"lat": location["lat"], "lng": location["lng"], "formatted": results[0].get("formatted_address")}

    def find_nearest_airport(self, lat: float, lng: float) -> Dict[str, Any]:
        places_result = self.client.places_nearby(
            location=(lat, lng),
            radius=80000,  # 80 km
            type="airport",
            rank_by=None,
        )
        candidates = places_result.get("results", [])
        if not candidates:
            return {"name": None, "iata": None, "lat": lat, "lng": lng, "place_id": None}
        best = candidates[0]
        details = self.client.place(place_id=best["place_id"], fields=["name", "geometry", "place_id"])
        loc = details["result"]["geometry"]["location"]
        return {
            "name": details["result"]["name"],
            "iata": None,  # Google Places does not return IATA; left None
            "lat": loc["lat"],
            "lng": loc["lng"],
            "place_id": details["result"]["place_id"],
        }

    def _places_nearby_common(self, lat: float, lng: float, place_type: str, radius: int = 10000, limit: int = 10):
        response = self.client.places_nearby(
            location=(lat, lng),
            radius=radius,
            type=place_type,
            rank_by=None,
        )
        results = response.get("results", [])[:limit]
        return results

    def find_attractions(self, lat: float, lng: float, radius: int = 12000, limit: int = 15) -> List[Dict[str, Any]]:
        raw = self._places_nearby_common(lat, lng, "tourist_attraction", radius, limit)
        attractions: List[Dict[str, Any]] = []
        for r in raw:
            geometry = r.get("geometry", {}).get("location", {})
            attractions.append(
                {
                    "name": r.get("name"),
                    "address": r.get("vicinity"),
                    "rating": r.get("rating"),
                    "user_ratings_total": r.get("user_ratings_total"),
                    "lat": geometry.get("lat"),
                    "lng": geometry.get("lng"),
                    "place_id": r.get("place_id"),
                    "photo_reference": (r.get("photos", [{}])[0] or {}).get("photo_reference"),
                }
            )
        return attractions

    def find_hotels(self, lat: float, lng: float, radius: int = 12000, limit: int = 10) -> List[Dict[str, Any]]:
        raw = self._places_nearby_common(lat, lng, "lodging", radius, limit)
        hotels: List[Dict[str, Any]] = []
        for r in raw:
            geometry = r.get("geometry", {}).get("location", {})
            hotels.append(
                {
                    "name": r.get("name"),
                    "address": r.get("vicinity"),
                    "rating": r.get("rating"),
                    "user_ratings_total": r.get("user_ratings_total"),
                    "price_level": r.get("price_level"),
                    "lat": geometry.get("lat"),
                    "lng": geometry.get("lng"),
                    "place_id": r.get("place_id"),
                    "photo_reference": (r.get("photos", [{}])[0] or {}).get("photo_reference"),
                }
            )
        return hotels
 
