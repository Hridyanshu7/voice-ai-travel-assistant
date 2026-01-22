from pydantic import BaseModel
from typing import List, Optional

class TripConstraints(BaseModel):
    origin: Optional[str] = None
    destination_city: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: Optional[int] = None
    budget_level: Optional[str] = None # e.g., "budget", "moderate", "luxury"
    travelers_count: Optional[int] = 1
    pace: Optional[str] = "moderate" # e.g., "relaxed", "moderate", "fast"
    interests: List[str] = []
    must_visit: List[str] = []
    avoid: List[str] = []
    
    # Status flags
    is_complete: bool = False
    missing_info: List[str] = []
    clarification_question: Optional[str] = None
    suggested_response: Optional[str] = None
