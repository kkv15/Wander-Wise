from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PlanTripRequest(BaseModel):
    originCity: str = Field(..., description="City user starts from, e.g., 'New Delhi, IN'")
    destinationCity: str = Field(..., description="Target city, e.g., 'Bangkok, TH'")
    numDays: int = Field(..., ge=1, le=30)
    numPeople: int = Field(..., ge=1, le=20)
    budgetCurrency: Optional[str] = Field(default="INR")
    budgetAmount: Optional[float] = Field(default=None, ge=0)
    includeFoodRecos: Optional[bool] = Field(default=False)
    includeCommuteTimes: Optional[bool] = Field(default=False)


class Airport(BaseModel):
    name: str
    iata: Optional[str] = None
    lat: float
    lng: float
    place_id: Optional[str] = None


class Hotel(BaseModel):
    name: str
    address: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None  # 0-4
    lat: float
    lng: float
    place_id: str
    photo_reference: Optional[str] = None
    url: Optional[str] = None
    stars: Optional[float] = None
    booking_links: Optional[Dict[str, str]] = None  # Contains Booking.com URLs (booking_hotel and booking_city)
    phone: Optional[str] = None


class Attraction(BaseModel):
    name: str
    address: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    lat: float
    lng: float
    place_id: str
    photo_reference: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    openingHours: Optional[str] = None
    bestTimeToVisit: Optional[str] = None


class FlightEstimate(BaseModel):
    originAirport: Optional[str] = None
    destinationAirport: Optional[str] = None
    estimatedRoundTripPerPerson: Optional[float] = None
    currency: str
    skyscanner_link: Optional[str] = None


class HotelEstimate(BaseModel):
    estimatedPerNight: Optional[float] = None
    currency: str


class OtherCostsEstimate(BaseModel):
    activitiesPerDayPerPerson: float
    foodTransportMiscPerDayPerPerson: float
    currency: str

class TrainClass(BaseModel):
    estFarePerPerson: float
    estDurationHours: float
    currency: str

class TrainEstimate(BaseModel):
    available: bool
    classes: Dict[str, TrainClass] = {}
    note: Optional[str] = None


class DayPlan(BaseModel):
    day: int
    items: List[str]


class HotelsResponse(BaseModel):
    hotels: List[Hotel]
    count: int
    city_links: Dict[str, str] = {}
    note: Optional[str] = None
    hotels_by_city: Optional[Dict[str, List[Hotel]]] = None  # Grouped by city for frontend display
    hotels_by_day: Optional[Dict[int, List[Hotel]]] = None  # Grouped by day for frontend display
    cities_mentioned: Optional[List[str]] = None  # List of cities for which hotels were fetched

class PlanTripResponse(BaseModel):
    itineraryId: Optional[str] = None
    summary: str
    flights: FlightEstimate
    hotels: HotelsResponse  # Changed from List[Hotel] to HotelsResponse
    dailyPlan: List[DayPlan]
    estimatedTotals: Dict[str, Any]
    train: Optional[TrainEstimate] = None


