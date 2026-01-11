import os
import json
import asyncio
from typing import Dict, Any, List
import google.generativeai as genai

from models.schemas import PlanTripRequest


ITINERARY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "flights": {
            "type": "object",
            "properties": {
                "originAirport": {"type": ["string", "null"]},
                "destinationAirport": {"type": ["string", "null"]},
                "estimatedRoundTripPerPerson": {"type": ["number", "null"]},
                "currency": {"type": "string"},
            },
            "required": ["currency"],
        },
        "hotels": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "address": {"type": ["string", "null"]},
                    "rating": {"type": ["number", "null"]},
                    "user_ratings_total": {"type": ["number", "null"]},
                    "price_level": {"type": ["number", "null"]},
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                    "place_id": {"type": "string"},
                    "photo_reference": {"type": ["string", "null"]},
                },
                "required": ["name", "lat", "lng", "place_id"],
            },
        },
        "dailyPlan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "number"},
                    "items": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["day", "items"],
            },
        },
        "estimatedTotals": {"type": "object"},
    },
    "required": ["summary", "flights", "hotels", "dailyPlan", "estimatedTotals"],
}


class GeminiService:
    """
    Uses Google's Gemini (free tier) to synthesize a structured itinerary.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def _build_prompt(
        self,
        req: PlanTripRequest,
        origin_geo: Dict[str, Any],
        dest_geo: Dict[str, Any],
        attractions: List[Dict[str, Any]],
        hotels: List[Dict[str, Any]],
        flight_estimate: Dict[str, Any],
        hotel_estimate: Dict[str, Any],
        other_costs_estimate: Dict[str, Any],
    ) -> str:
        return (
            "You are a travel planner. Produce a concise, realistic, day-by-day itinerary as valid JSON only, "
            "with no surrounding text. Incorporate the user's constraints and the provided candidates.\n\n"
            "JSON schema (subset):\n"
            f"{json.dumps(ITINERARY_JSON_SCHEMA)}\n\n"
            "Constraints and data:\n"
            f"- Origin city: {req.originCity} ({origin_geo})\n"
            f"- Destination city: {req.destinationCity} ({dest_geo})\n"
            f"- Days: {req.numDays}, People: {req.numPeople}\n"
            f"- Budget: {req.budgetAmount or 'unknown'} {req.budgetCurrency}\n"
            f"- Candidate attractions (top): {json.dumps(attractions[:8])}\n"
            f"- Candidate hotels (top): {json.dumps(hotels[:6])}\n"
            f"- Estimates: flights={json.dumps(flight_estimate)}, hotel={json.dumps(hotel_estimate)}, other={json.dumps(other_costs_estimate)}\n\n"
            "Rules:\n"
            "- Output valid JSON only, no commentary.\n"
            "- Provide a 'summary' paragraph.\n"
            "- Daily plan should be balanced with commute in mind.\n"
            "- Keep within budget if provided; adjust hotel standard and activity count accordingly.\n"
            "- Use the estimates provided for 'estimatedTotals' and compute a grand total.\n"
            "- Keep strings concise and helpful.\n"
        )

    def _generate_sync(self, prompt: str) -> Dict[str, Any]:
        response = self.model.generate_content(prompt)
        text = response.text or ""
        # Attempt to extract JSON
        text = text.strip()
        # If the model wrapped JSON in code fences, try to clean
        if text.startswith("```"):
            # remove ```json ... ```
            text = text.strip("`")
            parts = text.split("\n", 1)
            if len(parts) == 2:
                text = parts[1]
        try:
            parsed = json.loads(text)
        except Exception:
            # Fallback minimal structure to avoid crashing
            parsed = {
                "summary": "Itinerary could not be parsed; showing estimates only.",
                "flights": {},
                "hotels": [],
                "dailyPlan": [],
                "estimatedTotals": {},
            }
        return parsed

    async def generate_itinerary(
        self,
        req: PlanTripRequest,
        origin_geo: Dict[str, Any],
        dest_geo: Dict[str, Any],
        attractions: List[Dict[str, Any]],
        hotels: List[Dict[str, Any]],
        flight_estimate: Dict[str, Any],
        hotel_estimate: Dict[str, Any],
        other_costs_estimate: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(
            req,
            origin_geo,
            dest_geo,
            attractions,
            hotels,
            flight_estimate,
            hotel_estimate,
            other_costs_estimate,
        )
        parsed = await asyncio.get_running_loop().run_in_executor(None, self._generate_sync, prompt)

        # Ensure required fields and merge estimates if missing
        parsed.setdefault("flights", flight_estimate)
        parsed.setdefault("hotels", hotels[:3])
        parsed.setdefault("dailyPlan", [{"day": d + 1, "items": []} for d in range(req.numDays)])

        # Compute estimated totals if not provided
        currency = flight_estimate.get("currency") or hotel_estimate.get("currency") or other_costs_estimate.get("currency") or (req.budgetCurrency or "INR")
        flights_total = (flight_estimate.get("estimatedRoundTripPerPerson") or 0.0) * req.numPeople
        hotels_total = (hotel_estimate.get("estimatedPerNight") or 0.0) * req.numDays
        activities_total = other_costs_estimate.get("activitiesPerDayPerPerson", 0.0) * req.numPeople * req.numDays
        food_misc_total = other_costs_estimate.get("foodTransportMiscPerDayPerPerson", 0.0) * req.numPeople * req.numDays
        grand_total = flights_total + hotels_total + activities_total + food_misc_total

        parsed.setdefault("estimatedTotals", {})
        parsed["estimatedTotals"].update(
            {
                "flights": round(flights_total, 2),
                "hotels": round(hotels_total, 2),
                "activities": round(activities_total, 2),
                "foodTransportMisc": round(food_misc_total, 2),
                "grandTotal": round(grand_total, 2),
                "currency": currency,
            }
        )

        return parsed


