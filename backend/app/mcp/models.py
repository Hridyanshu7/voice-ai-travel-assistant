from pydantic import BaseModel
from typing import List, Optional, Dict

class GeoPoint(BaseModel):
    lat: float
    lon: float

class POI(BaseModel):
    id: Optional[str] = None
    name: str
    category: str
    description: Optional[str] = ""
    location: Optional[GeoPoint] = None
    average_duration_minutes: int = 60
    opening_hours: Optional[str] = None
    rating: Optional[float] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    details: Dict = {}  # Flexible field for costs, timings, tips, etc.

class POISearchRequest(BaseModel):
    city: str
    interests: List[str] = []
    limit: int = 10

class POISearchResponse(BaseModel):
    pois: List[POI]

class ItineraryBlock(BaseModel):
    time_block: str # "Morning", "Afternoon", "Evening"
    poi: POI
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    travel_time_from_previous: Optional[str] = None
    activity_cost: Optional[str] = None
    local_tip: Optional[str] = None

class DayItinerary(BaseModel):
    day_number: int
    blocks: List[ItineraryBlock]

class Itinerary(BaseModel):
    trip_title: str
    summary_rationale: Optional[str] = None
    weather_forecast: Optional[str] = None
    transportation_tips: Optional[str] = None
    accommodation_suggestion: Optional[str] = None
    days: List[DayItinerary]
    total_cost_estimate: Optional[str] = None

class BuildItineraryRequest(BaseModel):
    city: str
    days: int
    pace: str
    interests: List[str]
    must_visit: List[str] = []
    budget: Optional[str] = "Moderate"
    start_date: Optional[str] = None
