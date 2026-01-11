import json
import asyncio
import logging
from typing import Dict, Any, List
from groq import Groq

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


class AiService:
    """
    Uses Groq (free tier) with an open model to synthesize itinerary JSON.
    """

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model_name = model_name

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
        train_estimate: Dict[str, Any] | None,
        route_info: Dict[str, Any] | None = None,
        dest_airport: Dict[str, Any] | None = None,
    ) -> str:
        example = {
            "summary": "Experience the royal heritage of Jaipur over 5 days with immersive cultural tours, authentic Rajasthani cuisine, and visits to magnificent palaces and forts. This itinerary includes a day trip to Amer Fort and covers the best of Pink City's architecture, markets, and culinary delights.",
            "dailyPlan": [
                {
                    "day": 1,
                    "items": [
                        "Morning (9:00 AM - 12:00 PM): Arrive at Jaipur Airport (JAI) and transfer to hotel for check-in near MI Road area. After settling in, take a short walk to explore the nearby markets and get acquainted with the local area.",
                        "Afternoon (1:00 PM - 5:00 PM): Visit the magnificent City Palace complex, home to the royal family of Jaipur. Explore the palace museum showcasing royal costumes, weapons, and artifacts. Then proceed to Jantar Mantar, an astronomical observatory with fascinating ancient instruments. Allow 2-3 hours for both sites with a lunch break in between.",
                        "Evening (6:00 PM - 9:00 PM): Head to Hawa Mahal (Palace of Winds) to catch the beautiful golden hour lighting on this iconic five-story facade. Afterward, enjoy authentic Rajasthani snacks at the famous LMB (Laxmi Misthan Bhandar) restaurant, known for its traditional kachori and sweets. Take an evening stroll around Johari Bazaar."
                    ]
                },
                {
                    "day": 2,
                    "items": [
                        "Morning (8:00 AM - 12:30 PM): Take an early morning trip to Amer Fort (11 km from city center, 30 min drive). This hilltop fort offers stunning architecture and panoramic views. You can either walk up the pathway or take a jeep ride. Explore the Sheesh Mahal (Mirror Palace), Diwan-i-Aam, and Sukh Niwas. Spend 3-4 hours here to fully appreciate its grandeur.",
                        "Afternoon (1:00 PM - 4:00 PM): Visit Panna Meena ka Kund, an ancient stepwell near Amer Fort, perfect for photography. Then head to Anokhi Museum of Hand Printing to learn about traditional block printing techniques. Have lunch at a local restaurant near Amer.",
                        "Evening (5:00 PM - 9:00 PM): Return to Jaipur city. Experience an authentic Rajasthani dinner at Chokhi Dhani, a cultural village resort (about 20 km from city center). This is an immersive experience with traditional folk performances, puppet shows, camel rides, and unlimited Rajasthani thali. Book in advance for the best experience."
                    ]
                },
                {
                    "day": 3,
                    "items": [
                        "Morning (8:30 AM - 12:00 PM): Drive up to Nahargarh Fort (also called Tiger Fort) for breathtaking panoramic views of the entire Pink City. The fort is situated on the edge of the Aravalli Hills. You can enjoy breakfast at the fort's restaurant with stunning views. Allow 2-3 hours including travel time.",
                        "Afternoon (1:00 PM - 5:00 PM): Visit the Albert Hall Museum, also known as the Central Museum, which houses an impressive collection of artifacts, paintings, and decorative arts. Then relax at the adjacent Ram Niwas Garden, a beautiful public park perfect for a leisurely walk. Have lunch at a nearby restaurant.",
                        "Evening (5:30 PM - 9:00 PM): Explore Bapu Bazaar, one of Jaipur's most famous shopping streets. Shop for traditional textiles, jewelry, handicrafts, and souvenirs. Bargaining is expected here. End your evening with a refreshing lassi at the famous Lassiwala on MI Road, known for serving the best lassi in Jaipur for decades."
                    ]
                },
                {
                    "day": 4,
                    "items": [
                        "Morning (9:00 AM - 1:00 PM): Join a guided heritage walk through the Pink City (Old City) to discover hidden gems, traditional havelis, and learn about Jaipur's history and architecture. The walk typically covers narrow lanes, local markets, and historic buildings. This is a great way to experience authentic local culture.",
                        "Afternoon (2:00 PM - 5:00 PM): Visit Birla Mandir (Lakshmi Narayan Temple), a beautiful white marble temple with intricate carvings and peaceful atmosphere. Then visit Central Park, one of Asia's largest parks, perfect for a relaxing stroll. You can also visit the nearby Jawahar Circle if time permits.",
                        "Evening (6:00 PM - 9:00 PM): Enjoy dinner at a rooftop café near MI Road area, offering a great view of the city lights. Many rooftop restaurants offer both Indian and international cuisine. This is a perfect way to unwind after a day of sightseeing."
                    ]
                },
                {
                    "day": 5,
                    "items": [
                        "Morning (9:00 AM - 12:00 PM): Visit Patrika Gate, a recently built ornamental gate known for its colorful, Instagram-worthy architecture with intricate designs representing different cities of Rajasthan. Take photos here before checking out from your hotel. If time permits, visit any nearby attractions you may have missed.",
                        "Afternoon (12:00 PM - 2:00 PM): Complete hotel check-out formalities. Enjoy a final lunch at a local restaurant, perhaps trying some dishes you haven't tried yet. Pick up any last-minute souvenirs or gifts.",
                        "Evening (2:30 PM onwards): Transfer to Jaipur Airport (JAI) for your departure flight. Arrive at the airport at least 2 hours before your flight time for domestic flights or 3 hours for international flights."
                    ]
                }
            ]
        }
        food_rule = "- Include at least one authentic local food recommendation per day with detailed descriptions.\n" if req.includeFoodRecos else ""
        commute_rule = "- Include approximate commute times or transport mode between major stops with detailed information.\n" if req.includeCommuteTimes else ""
        
        # Add route information if available
        route_note = ""
        if route_info and dest_airport:
            airport_name = dest_airport.get("name") or "the nearest airport"
            airport_iata = dest_airport.get("iata")
            if airport_iata:
                airport_name = f"{airport_name} ({airport_iata})"
            
            # Handle new multi-option route info structure
            if isinstance(route_info, dict) and "primary" in route_info:
                # New format with multiple transport options
                primary_route = route_info.get("primary", {})
                dist_km = primary_route.get("distance_km", 0)
                duration_min = primary_route.get("duration_minutes", 0)
                
                # Get transport options
                taxi_info = route_info.get("taxi", {})
                bus_info = route_info.get("bus", {})
                shared_taxi_info = route_info.get("shared_taxi", {})
                
                options_text = []
                if taxi_info.get("available") or taxi_info.get("distance_km"):
                    taxi_dist = taxi_info.get("distance_km", dist_km)
                    taxi_dur = taxi_info.get("duration_minutes", duration_min)
                    options_text.append(f"taxi (~{taxi_dur} min, {taxi_dist:.1f} km)")
                
                if bus_info.get("available") or bus_info.get("distance_km"):
                    bus_dist = bus_info.get("distance_km", dist_km)
                    bus_dur = bus_info.get("duration_minutes", duration_min)
                    options_text.append(f"bus (~{bus_dur} min, {bus_dist:.1f} km)")
                
                if shared_taxi_info.get("available") or shared_taxi_info.get("distance_km"):
                    shared_dist = shared_taxi_info.get("distance_km", dist_km)
                    shared_dur = shared_taxi_info.get("duration_minutes", duration_min)
                    options_text.append(f"shared taxi (~{shared_dur} min, {shared_dist:.1f} km)")
                
                transport_options = ", ".join(options_text) if options_text else "ground transport"
                
                route_note = (
                    f"\n- IMPORTANT ROUTE INFO: The destination city is {dist_km:.1f}km away from {airport_name}. "
                    f"After landing at {airport_name}, travelers can take {transport_options} to reach {req.destinationCity}. "
                    f"Primary option (taxi/car) takes approximately {duration_min} minutes. "
                    f"Include this in your summary and Day 1 itinerary. Mention: 'Fly to {airport_name}, then take {transport_options} to {req.destinationCity}'.\n"
                )
            else:
                # Old format (backward compatibility)
                dist_km = route_info.get("distance_km", 0)
                duration_min = route_info.get("duration_minutes", 0)
                
                route_note = (
                    f"\n- IMPORTANT ROUTE INFO: The destination city is {dist_km:.1f}km away from {airport_name}. "
                    f"After landing at {airport_name}, travelers need to take ground transport (bus/taxi) "
                    f"which takes approximately {duration_min} minutes to reach {req.destinationCity}. "
                    f"Include this in your summary and Day 1 itinerary. Mention: 'Fly to {airport_name}, then take bus/taxi to {req.destinationCity}'.\n"
                )
        
        return (
            "You are an expert travel planner specializing in creating detailed, immersive itineraries. "
            "Produce a comprehensive, elaborative day-by-day itinerary as valid JSON only, with no surrounding text. "
            "Your responses should be DETAILED and INFORMATIVE, not brief or one-line descriptions.\n\n"
            "JSON schema:\n"
            f"{json.dumps(ITINERARY_JSON_SCHEMA)}\n\n"
            "Example style (for structure and level of detail - follow this elaborative format):\n"
            f"{json.dumps(example)}\n\n"
            "Constraints and data:\n"
            f"- Origin city: {req.originCity} ({origin_geo})\n"
            f"- Destination city: {req.destinationCity} ({dest_geo})\n"
            f"- Days: {req.numDays}, People: {req.numPeople}\n"
            f"- Budget: {req.budgetAmount or 'unknown'} {req.budgetCurrency}\n"
            f"- Candidate attractions (top): {json.dumps(attractions[:8])}\n"
            "- Each attraction may include 'description', 'openingHours', and 'bestTimeToVisit'—use them to sequence the day logically and avoid closed times.\n"
            f"- Candidate hotels (top): {json.dumps(hotels[:6])}\n"
            "- Each hotel may include 'booking_links', 'phone', 'stars', 'rating', 'user_ratings_total', and 'url'—use these fields when suggesting hotels.\n"
            f"- Estimates: flights={json.dumps(flight_estimate)}, hotel={json.dumps(hotel_estimate)}, other={json.dumps(other_costs_estimate)}\n"
            f"- Train estimate (if available): {json.dumps(train_estimate or {})}\n"
            f"{route_note}"
            f"\nCRITICAL RULES FOR ELABORATIVE RESPONSES:\n"
            f"- Output valid JSON only, no commentary.\n"
            f"- MANDATORY: The 'dailyPlan' array MUST contain EXACTLY {req.numDays} day entries (day 1, day 2, ..., day {req.numDays}). You MUST NOT skip any days. Each day from 1 to {req.numDays} must be present with detailed activities.\n"
            f"- CRITICAL: Generate itinerary for ALL {req.numDays} days requested. Do NOT stop at 2-3 days. For a {req.numDays}-day trip, you MUST create plans for Day 1, Day 2, Day 3, ... up to Day {req.numDays}. Spread activities across all days evenly.\n"
            f"- Summary: Provide a DETAILED, engaging paragraph (4-6 sentences) describing the trip experience, cultural significance, key highlights, what makes it special, and chosen travel mode. Make it informative and compelling, not generic.\n"
            f"- Daily Plan Items: Each item MUST be ELABORATIVE (2-4 sentences minimum), NOT one-liners. Every item should include:\n"
            "  1. WHAT: Specific activity, attraction, or experience\n"
            "  2. WHY: Historical/cultural significance, unique features, what makes it special\n"
            "  3. WHEN: Approximate timings (e.g., 'Morning (9:00 AM - 12:00 PM)'), duration needed, best time to visit\n"
            "  4. HOW: Travel details (distance from previous location, transport mode, time taken), practical logistics\n"
            "  5. TIPS: Opening hours, entry fees, what to wear, photography rules, local customs, best spots for photos, crowd levels, what to expect\n"
            "  6. CONTEXT: Cultural background, interesting facts, recommendations (best restaurants nearby, must-try dishes, nearby attractions)\n"
            f"- Each day should have 4-8 detailed items covering Morning, Afternoon, and Evening. Balance sightseeing, relaxation, and meals.\n"
            f"- IMPORTANT: If your daily plan includes visits to multiple cities or locations (e.g., Day 1-3 in City A, Day 4-5 in City B), suggest hotels that match the city where travelers will be staying each night. Only suggest hotels from cities that actually appear in your daily plan items.\n"
            f"- CRITICAL HOTEL RULE: When suggesting hotels, match them to the cities mentioned in your daily plan AND ensure they are in the destination country ({req.destinationCity}). Do NOT suggest hotels from other countries. If traveling to Thailand, ONLY suggest Thailand hotels (Bangkok, Phuket, Chiang Mai, etc.). If traveling to India, ONLY suggest India hotels. If traveling to Malaysia, ONLY suggest Malaysia hotels. Do NOT mix countries. Verify the hotel is actually in the destination country before suggesting it.\n"
            "- Include travel time estimates and transportation modes between attractions when relevant (e.g., '30 min drive', 'walking distance', '10 km from city center').\n"
            "- Mention practical tips: opening hours, entry fees, best time to visit, what to wear, photography restrictions, weather considerations, crowd information.\n"
            f"- Include local cuisine recommendations with context: {food_rule}For each food recommendation, explain what the dish is, where to find authentic versions, what makes it special, and any dietary considerations.\n"
            f"- Include commute information: {commute_rule}When mentioning transportation between places, provide realistic time estimates, mode of transport (taxi/bus/walking), approximate costs, and any tips for navigation.\n"
            "- Keep within budget if provided; adjust hotel standard and activity count accordingly, and explain the rationale.\n"
            "- If a train estimate is provided (for short intra-India trips), prefer train over flights and mention the recommended class with reasoning (e.g., why 3A is good value for money, comfort level, duration).\n"
            "- Use the estimates provided for 'estimatedTotals' and compute a grand total (do not include train unless you explicitly choose train as the main transport; if you choose train, include an approximate train total instead of flights in totals).\n"
            "- For each hotel in 'hotels', include any provided 'url' and 'stars' fields; do not invent ratings.\n"
            "- Write in an engaging, informative, travel-guide style that helps travelers understand not just what to do, but why it's worth doing, what makes it special, and how to make the most of their experience.\n"
            "- AVOID one-liners. Every activity description should be detailed enough that a traveler knows what to expect, how to prepare, and why they should be excited about it.\n"
        )

    def _generate_sync(self, prompt: str) -> Dict[str, Any]:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert travel planner specializing in detailed, immersive itineraries. Always return valid JSON only with elaborative, detailed descriptions."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4000,  # Increased for more detailed responses
        )
        text = completion.choices[0].message.content or ""
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            parts = text.split("\n", 1)
            if len(parts) == 2:
                text = parts[1]
        try:
            parsed = json.loads(text)
        except Exception as e:
            # Log the error for debugging
            logging.warning(f"AI JSON parsing failed: {e}. Text: {text[:500]}")
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
        train_estimate: Dict[str, Any] | None = None,
        route_info: Dict[str, Any] | None = None,
        dest_airport: Dict[str, Any] | None = None,
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
            train_estimate,
            route_info,
            dest_airport,
        )
        # Retry logic: try up to 3 times if daily plan is empty or invalid
        max_retries = 3
        parsed = None
        for attempt in range(max_retries):
            parsed = await asyncio.get_running_loop().run_in_executor(None, self._generate_sync, prompt)
            
            # Check if daily plan is valid (has entries and items are populated)
            daily_plan = parsed.get("dailyPlan", [])
            has_valid_daily_plan = (
                daily_plan 
                and len(daily_plan) >= req.numDays
                and all(
                    day.get("items") and len(day.get("items", [])) > 0 
                    for day in daily_plan[:req.numDays]
                )
            )
            
            if has_valid_daily_plan:
                break  # Valid response, exit retry loop
            
            # If last attempt, continue anyway to create fallback empty days
            if attempt < max_retries - 1:
                logging.warning(f"AI returned empty/invalid daily plan (attempt {attempt + 1}/{max_retries}), retrying...")
                await asyncio.sleep(0.5)  # Brief delay before retry
        
        if not parsed:
            # Fallback if all retries failed
            parsed = {
                "summary": "Unable to generate itinerary; please try again.",
                "flights": {},
                "hotels": [],
                "dailyPlan": [],
                "estimatedTotals": {},
            }

        # Decide currency first
        currency = (
            flight_estimate.get("currency")
            or hotel_estimate.get("currency")
            or other_costs_estimate.get("currency")
            or (req.budgetCurrency or "INR")
        )
        # Ensure flights contains at least the currency field (model may return {})
        if not isinstance(parsed.get("flights"), dict) or not parsed.get("flights", {}).get("currency"):
            parsed["flights"] = flight_estimate or {"currency": currency}
        
        # Handle hotels: merge AI-suggested hotels with original hotels to preserve booking_links
        ai_hotels = parsed.get("hotels", [])
        if ai_hotels:
            # Create a map of original hotels by name for quick lookup
            original_hotels_map = {h.get("name", "").lower(): h for h in hotels}
            
            # Merge AI hotels with original hotel data (preserve booking_links, phone, etc.)
            merged_hotels = []
            for ai_hotel in ai_hotels:
                hotel_name = ai_hotel.get("name", "").lower()
                # Find matching original hotel
                original = original_hotels_map.get(hotel_name)
                if original:
                    # Merge: use AI hotel but preserve booking_links and other useful fields from original
                    merged = {**ai_hotel, **{k: v for k, v in original.items() if k in ["booking_links", "phone", "stars", "rating", "user_ratings_total", "price_level"] and v}}
                    merged_hotels.append(merged)
                else:
                    # Use AI hotel as-is
                    merged_hotels.append(ai_hotel)
            parsed["hotels"] = merged_hotels[:6]
        else:
            # No AI hotels, use original hotels
            parsed["hotels"] = hotels[:6]
        # Ensure daily plan has ALL requested days with valid items
        daily_plan = parsed.get("dailyPlan", [])
        
        # Check if we have valid daily plan entries with populated items
        valid_days = [
            day for day in daily_plan 
            if day.get("day") and day.get("items") and len(day.get("items", [])) > 0
        ]
        
        if not valid_days or len(valid_days) < req.numDays:
            # Only create empty days if we have NO valid days at all (last resort)
            if not valid_days:
                logging.warning(f"No valid daily plan items found. Creating placeholder days. Valid days: {len(valid_days)}, Requested: {req.numDays}")
                # Create placeholder days as last resort
                existing_days = {d.get("day") for d in daily_plan if d.get("day")}
                for day_num in range(1, req.numDays + 1):
                    if day_num not in existing_days:
                        daily_plan.append({
                            "day": day_num, 
                            "items": [
                                f"Day {day_num}: Itinerary generation encountered an issue. Please try regenerating your trip plan."
                            ]
                        })
                daily_plan.sort(key=lambda x: x.get("day", 0))
                parsed["dailyPlan"] = daily_plan
            else:
                # We have some valid days, fill in missing ones
                existing_day_nums = {d.get("day") for d in valid_days}
                for day_num in range(1, req.numDays + 1):
                    if day_num not in existing_day_nums:
                        # Try to find the day in original daily_plan even if it has empty items
                        existing_day = next((d for d in daily_plan if d.get("day") == day_num), None)
                        if existing_day:
                            # Use existing structure but add placeholder item
                            existing_day["items"] = existing_day.get("items", []) or [
                                f"Day {day_num}: Itinerary generation encountered an issue. Please try regenerating your trip plan."
                            ]
                            valid_days.append(existing_day)
                        else:
                            valid_days.append({
                                "day": day_num,
                                "items": [
                                    f"Day {day_num}: Itinerary generation encountered an issue. Please try regenerating your trip plan."
                                ]
                            })
                valid_days.sort(key=lambda x: x.get("day", 0))
                parsed["dailyPlan"] = valid_days[:req.numDays]
        else:
            # We have enough valid days, just ensure we have exactly req.numDays
            valid_days.sort(key=lambda x: x.get("day", 0))
            parsed["dailyPlan"] = valid_days[:req.numDays]
        
        # Final validation: ensure we have exactly req.numDays days
        if len(parsed["dailyPlan"]) > req.numDays:
            parsed["dailyPlan"] = parsed["dailyPlan"][:req.numDays]
        
        # Final check: ensure all days have non-empty items
        for day_plan in parsed["dailyPlan"]:
            if not day_plan.get("items") or len(day_plan.get("items", [])) == 0:
                day_num = day_plan.get("day", "?")
                day_plan["items"] = [
                    f"Day {day_num}: Itinerary generation encountered an issue. Please try regenerating your trip plan."
                ]
        if train_estimate:
            parsed.setdefault("train", train_estimate)
        flights_total = (flight_estimate.get("estimatedRoundTripPerPerson") or 0.0) * req.numPeople
        hotels_total = (hotel_estimate.get("estimatedPerNight") or 0.0) * req.numDays
        activities_total = other_costs_estimate.get("activitiesPerDayPerPerson", 0.0) * req.numPeople * req.numDays
        food_misc_total = other_costs_estimate.get("foodTransportMiscPerDayPerPerson", 0.0) * req.numPeople * req.numDays
        # If train is available, prefer train over flights in totals
        train_total = 0.0
        if train_estimate and train_estimate.get("available"):
            classes = train_estimate.get("classes") or {}
            # Prefer 3A if available, else any one class
            chosen = classes.get("3A") or (list(classes.values())[0] if classes else None)
            if chosen:
                per_person = chosen.get("estFarePerPerson") or 0.0
                train_total = per_person * req.numPeople
                flights_total = 0.0
        grand_total = flights_total + train_total + hotels_total + activities_total + food_misc_total

        parsed.setdefault("estimatedTotals", {})
        parsed["estimatedTotals"].update(
            {
                "flights": round(flights_total, 2),
                "train": round(train_total, 2) if train_total else 0.0,
                "hotels": round(hotels_total, 2),
                "activities": round(activities_total, 2),
                "foodTransportMisc": round(food_misc_total, 2),
                "grandTotal": round(grand_total, 2),
                "currency": currency,
            }
        )
        return parsed


