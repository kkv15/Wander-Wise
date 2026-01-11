from typing import Dict, Any, List, Optional
import math


class CostEstimator:
    """
    Heuristic estimations for flights, hotels, and daily spending.
    - Flights: estimates round-trip per person using great-circle distance between airports (if available),
      with a base fare per km and a floor.
    - Hotels: maps Google price_level (0-4) to a price band. Picks median.
    - Other costs: activities + food/transport/misc per day per person tuned by city price signal.
    """

    def __init__(self, default_currency: str = "INR"):
        self.default_currency = default_currency

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        # Haversine formula
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def estimate_flights(self, origin_airport: Dict[str, Any], destination_airport: Dict[str, Any], num_people: int, origin_city: str = "", destination_city: str = "") -> Dict[str, Any]:
        currency = self.default_currency
        if not origin_airport.get("lat") or not destination_airport.get("lat"):
            return {"originAirport": None, "destinationAirport": None, "estimatedRoundTripPerPerson": None, "currency": currency, "skyscanner_link": None}
        distance_km = self._haversine_km(
            origin_airport["lat"], origin_airport["lng"], destination_airport["lat"], destination_airport["lng"]
        )
        # Basic fare model (very rough): base + per-km
        base = 3000.0  # base fee
        per_km = 6.5   # INR per km
        estimate_per_person = max(9000.0, base + per_km * distance_km)
        
        # Generate Skyscanner flight booking link
        from urllib.parse import quote_plus
        origin_name = origin_city.split(',')[0].strip() if origin_city else origin_airport.get("name", "")
        dest_name = destination_city.split(',')[0].strip() if destination_city else destination_airport.get("name", "")
        origin_iata = origin_airport.get("iata", "")
        dest_iata = destination_airport.get("iata", "")
        
        # Build Skyscanner link - use IATA codes if available, else city names
        if origin_iata and dest_iata:
            # Use IATA codes for more accurate search
            skyscanner_link = f"https://www.skyscanner.co.in/transport/flights/{quote_plus(origin_iata)}/{quote_plus(dest_iata)}/"
        elif origin_name and dest_name:
            # Fallback to city names
            skyscanner_link = f"https://www.skyscanner.co.in/transport/flights/{quote_plus(origin_name)}/{quote_plus(dest_name)}/"
        else:
            skyscanner_link = None
        
        return {
            "originAirport": origin_airport.get("name"),
            "destinationAirport": destination_airport.get("name"),
            "estimatedRoundTripPerPerson": round(estimate_per_person, 2),
            "currency": currency,
            "skyscanner_link": skyscanner_link,
        }

    def estimate_hotels(self, hotels: List[Dict[str, Any]], num_days: int, num_people: int) -> Dict[str, Any]:
        currency = self.default_currency
        # Map Google's price_level to indicative nightly price (for 2 people)
        level_to_price = {
            0: 2500.0,
            1: 4000.0,
            2: 7000.0,
            3: 11000.0,
            4: 16000.0,
        }
        # Fallback if no price_level available
        fallback = 7000.0
        # Prefer median price level among hotels
        levels = [h.get("price_level") for h in hotels if h.get("price_level") is not None]
        if not levels:
            per_night = fallback
        else:
            levels.sort()
            median_level = levels[len(levels) // 2]
            per_night = level_to_price.get(median_level, fallback)
        # Scale for more than 2 people
        scale = max(1.0, num_people / 2.0)
        per_night_scaled = per_night * scale
        return {"estimatedPerNight": round(per_night_scaled, 2), "currency": currency}

    def derive_city_price_level(self, hotels: List[Dict[str, Any]], attractions: List[Dict[str, Any]]) -> int:
        # Simple signal based on hotel price levels and attraction ratings count
        levels = [h.get("price_level") for h in hotels if h.get("price_level") is not None]
        if not levels:
            return 2
        avg_level = sum(levels) / len(levels)
        if avg_level >= 3.2:
            return 4
        if avg_level >= 2.5:
            return 3
        if avg_level >= 1.5:
            return 2
        if avg_level >= 0.8:
            return 1
        return 0

    def estimate_other_costs(self, num_days: int, num_people: int, city_price_level: int) -> Dict[str, Any]:
        currency = self.default_currency
        # Tuned bands per price level (rough INR values)
        bands = {
            0: (400.0, 600.0),
            1: (700.0, 900.0),
            2: (1200.0, 1500.0),
            3: (1800.0, 2200.0),
            4: (2600.0, 3200.0),
        }
        activities, food_misc = bands.get(city_price_level, (1200.0, 1500.0))
        return {
            "activitiesPerDayPerPerson": round(activities, 2),
            "foodTransportMiscPerDayPerPerson": round(food_misc, 2),
            "currency": currency,
        }

    def compute_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return self._haversine_km(lat1, lon1, lat2, lon2)

    def estimate_train(self, origin: Dict[str, float], destination: Dict[str, float]) -> Dict[str, Any]:
        """
        Improved Indian Rail estimates based on distance.
        Includes multiple classes and route information.
        - Sleeper (SL): ~0.6 INR/km, min 200
        - 3A (3-tier AC): ~1.6 INR/km, min 600
        - 2A (2-tier AC): ~2.4 INR/km, min 900
        - 1A (First AC): ~4.0 INR/km, min 1500
        Duration: distance / 55 km/h + 0.5h buffer (avg train speed in India)
        """
        currency = self.default_currency
        if not origin or not destination:
            return {"available": False, "classes": {}, "note": None}
        distance_km = self._haversine_km(origin["lat"], origin["lng"], destination["lat"], destination["lng"])
        
        # Duration calculation: average train speed in India is ~55 km/h for long distance
        # Add buffer time for stops
        duration_h = max(1.0, distance_km / 55.0 + 0.5)
        
        # Fare estimates per class (rough approximations based on Indian Railway fare structure)
        sl = max(200.0, 0.6 * distance_km)  # Sleeper
        a3 = max(600.0, 1.6 * distance_km)  # 3-tier AC
        a2 = max(900.0, 2.4 * distance_km)  # 2-tier AC  
        a1 = max(1500.0, 4.0 * distance_km)  # First AC
        
        return {
            "available": True,
            "distance_km": round(distance_km, 1),
            "classes": {
                "SL": {"estFarePerPerson": round(sl, 2), "estDurationHours": round(duration_h, 1), "currency": currency, "description": "Sleeper Class"},
                "3A": {"estFarePerPerson": round(a3, 2), "estDurationHours": round(duration_h, 1), "currency": currency, "description": "3-tier AC"},
                "2A": {"estFarePerPerson": round(a2, 2), "estDurationHours": round(duration_h, 1), "currency": currency, "description": "2-tier AC"},
                "1A": {"estFarePerPerson": round(a1, 2), "estDurationHours": round(duration_h, 1), "currency": currency, "description": "First AC"},
            },
            "note": "Estimates only. Actual fares and duration may vary. Book via IRCTC (irctc.co.in) or authorized agents."
        }
 
