import os
import logging
import json
import re
import httpx
from app.models import TripConstraints

logger = logging.getLogger(__name__)

def extract_constraints_simple(transcript: str, existing_constraints: dict = None) -> TripConstraints:
    """
    Simple regex-based fallback when AI APIs are unavailable.
    """
    logger.info("Using simple regex-based extraction (AI APIs unavailable)")
    
    # Initialize with defaults or existing constraints
    current_data = {
        "destination_city": None,
        "duration_days": None,
        "travelers_count": 1,
        "budget_level": "Moderate",
        "pace": "Moderate",
        "interests": [],
        "must_visit": [],
        "avoid": [],
        "start_date": None,
        "end_date": None
    }
    
    if existing_constraints:
        current_data.update(existing_constraints)
    
    # Simple city extraction - Expanded list
    # In a real app, this should be a larger database or handled by logic that identifies proper nouns
    cities = [
        "paris", "tokyo", "jaipur", "delhi", "london", "dubai", "singapore", "new york", "mumbai",
        "agra", "bangalore", "hyderabad", "chennai", "kolkata", "pune", "goa", "kerala", "himachal",
        "manali", "shimla", "rishikesh", "varanasi", "udaipur", "jodhpur", "kyoto", "osaka", "rome", 
        "venice", "florence", "milan", "barcelona", "madrid", "berlin", "munich", "amsterdam"
    ]
    
    transcript_lower = transcript.lower()
    
    # Only look for a new city if we don't have one, or if the user seems to be changing it
    # Find all mentioned cities and their positions
    mentioned_cities = []
    for city in cities:
        # Use regex to find consistent word boundaries
        matches = re.finditer(r'\b' + re.escape(city) + r'\b', transcript_lower)
        for match in matches:
            mentioned_cities.append((match.start(), city.title()))
            
    # Sort by position and pick the last one mentioned
    if mentioned_cities:
        mentioned_cities.sort(key=lambda x: x[0])
        found_city = mentioned_cities[-1][1]
    else:
        found_city = None
            
    if found_city:
        current_data["destination_city"] = found_city
    
    # Extract numbers for duration (digits or words)
    duration_match = re.search(r'(\d+)\s*(day|days)', transcript_lower)
    if duration_match:
        current_data["duration_days"] = int(duration_match.group(1))
    else:
        # Handle word numbers
        word_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        for word, val in word_map.items():
            if f"{word} day" in transcript_lower:
                current_data["duration_days"] = val
                break
                
    if "one week" in transcript_lower or "a week" in transcript_lower:
        current_data["duration_days"] = 7
    elif "two weeks" in transcript_lower:
        current_data["duration_days"] = 14
    
    # Date parsing logic
    from datetime import datetime, timedelta
    today = datetime.now()
    
    if "next weekend" in transcript_lower:
        # Find next Saturday
        days_ahead = 5 - today.weekday() # Saturday is 5
        if days_ahead <= 0: # If today is Saturday or Sunday, go to next week
            days_ahead += 7
        start_date = today + timedelta(days=days_ahead)
        current_data["start_date"] = start_date.strftime("%Y-%m-%d")
        
    elif "next friday" in transcript_lower:
        days_ahead = 4 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        start_date = today + timedelta(days=days_ahead)
        current_data["start_date"] = start_date.strftime("%Y-%m-%d")
        
    elif "tomorrow" in transcript_lower:
        start_date = today + timedelta(days=1)
        current_data["start_date"] = start_date.strftime("%Y-%m-%d")

    # Budget extraction
    budget_digits = re.search(r'budget (of|is|around)?\s*([\d,]+)', transcript_lower)
    budget_currency = re.search(r'([\d,]+)\s*(rupees|rs|usd|dollars|euro|gbp)', transcript_lower)
    
    if budget_currency:
        current_data["budget_level"] = f"{budget_currency.group(1)} {budget_currency.group(2)}"
    elif budget_digits:
        current_data["budget_level"] = f"{budget_digits.group(2)} INR" # Default to INR if digits found
    elif "luxury" in transcript_lower or "expensive" in transcript_lower:
        current_data["budget_level"] = "Luxury"
    elif "budget" in transcript_lower or "cheap" in transcript_lower:
        current_data["budget_level"] = "Budget Friendly"

    # Interest extraction (simple keyword matching)
    interest_keywords = {
        "shopping": "Shopping",
        "shop": "Shopping",
        "souvenir": "Shopping",
        "food": "Local Cuisine",
        "cuisine": "Local Cuisine",
        "eat": "Local Cuisine",
        "restaurant": "Local Cuisine",
        "history": "History",
        "historic": "History",
        "culture": "Culture",
        "museum": "Museums",
        "art": "Art",
        "nature": "Nature",
        "park": "Nature",
        "adventure": "Adventure",
        "hiking": "Adventure",
        "nightlife": "Nightlife",
        "club": "Nightlife",
        "party": "Nightlife",
        "relax": "Relaxation",
        "spa": "Relaxation",
        "monuments": "Monuments",
        "fort": "Monuments",
        "palace": "Monuments"
    }
    
    found_interests = set(current_data.get("interests", []))
    for word, category in interest_keywords.items():
        if word in transcript_lower:
            found_interests.add(category)
    current_data["interests"] = list(found_interests)

    # Must-visit extraction (look for phrases like "visit X" or "to X")
    must_visit_patterns = [
        r"visit (the )?([A-Z][a-z]+(\s[A-Z][a-z]+)*)",
        r"go to (the )?([A-Z][a-z]+(\s[A-Z][a-z]+)*)",
        r"see (the )?([A-Z][a-z]+(\s[A-Z][a-z]+)*)"
    ]
    found_must_visit = set(current_data.get("must_visit", []))
    for pattern in must_visit_patterns:
        matches = re.finditer(pattern, transcript) # Use original transcript for capitalization
        for match in matches:
            place = match.group(2)
            if place.lower() not in cities: # Don't add cities as must-visit places
                 found_must_visit.add(place)
    
    # Also handle specific mentions from the user's screenshot
    if "Hawa Mehel" in transcript: found_must_visit.add("Hawa Mehel")
    if "Chokidani" in transcript: found_must_visit.add("Chokidani")
    if "Jokidani" in transcript: found_must_visit.add("Chokidhani") # Correct spelling
    
    current_data["must_visit"] = list(found_must_visit)

    # Determine if complete
    destination = current_data["destination_city"]
    duration = current_data["duration_days"]
    start_date = current_data.get("start_date")
    
    is_complete = destination is not None and duration is not None and start_date is not None
    missing = []
    
    clarification = None
    suggested_response = None
    
    # Generate conversational response
    changes = []
    if existing_constraints:
        if current_data["destination_city"] != existing_constraints.get("destination_city"):
            changes.append(f"destination to {current_data['destination_city']}")
        if current_data["duration_days"] != existing_constraints.get("duration_days"):
            changes.append(f"duration to {current_data['duration_days']} days")
        if current_data["budget_level"] != existing_constraints.get("budget_level"):
            changes.append(f"budget to {current_data['budget_level']}")
        
        # Check for new interests
        new_interests = set(current_data["interests"]) - set(existing_constraints.get("interests", []))
        if new_interests:
            changes.append(f"added {', '.join(new_interests)} to preferences")
            
        # Check for new must-visits
        new_places = set(current_data["must_visit"]) - set(existing_constraints.get("must_visit", []))
        if new_places:
            changes.append(f"added {', '.join(new_places)} to your must-visit list")

    if changes:
        suggested_response = f"I've updated your {', '.join(changes)}. Anything else?"
    elif is_complete:
        if "?" in transcript:
            suggested_response = "I see your question! I'm currently in a limited mode, so I can't answer details, but I have your trip preferences saved."
        else:
            suggested_response = "I've noted that down. Your trip plan is looking good! Ready to generate the itinerary?"
    else:
        # Not complete and no clear changes detected
        if not destination:
            missing.append("destination")
            clarification = "Which city would you like to visit?"
        elif not duration:
            missing.append("duration")
            clarification = f"Great, a trip to {destination}. How many days are you planning for?"
        elif not start_date:
            missing.append("start_date")
            clarification = f"When are you planning to visit {destination}? (e.g., 'tomorrow', 'next friday')"
        else:
            suggested_response = "I've captured that. Is there anything else you'd like to add to your trip?"

    return TripConstraints(
        destination_city=destination,
        start_date=start_date,
        end_date=current_data.get("end_date"),
        duration_days=duration,
        budget_level=current_data.get("budget_level", "Moderate"),
        travelers_count=current_data.get("travelers_count", 1),
        pace=current_data.get("pace", "Moderate"),
        interests=current_data["interests"],
        must_visit=current_data["must_visit"],
        avoid=current_data.get("avoid", []),
        is_complete=is_complete,
        missing_info=missing,
        clarification_question=clarification,
        suggested_response=suggested_response
    )

async def extract_constraints_with_openrouter(transcript: str, existing_constraints: dict = None, history: list = []) -> TripConstraints:
    """
    Uses OpenRouter API for intent extraction (primary method) with full conversation history.
    """
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key not configured")
        
        system_instruction = f"""You are an AI travel assistant. Extract trip constraints from the user's input, considering the conversation history.

Current Known Constraints: {json.dumps(existing_constraints, default=str) if existing_constraints else "{}"}

Extract: Destination City, Start/End Date, Duration (days), Budget Level, Travelers Count, Pace, Interests, Must Visit, Avoid.

Return ONLY a JSON object (no markdown):
{{
    "destination_city": string | null,
    "start_date": string | null,
    "end_date": string | null,
    "duration_days": int | null,
    "budget_level": string | null,
    "travelers_count": int,
    "pace": string,
    "interests": [string],
    "must_visit": [string],
    "avoid": [string],
    "is_complete": bool,
    "missing_info": [string],
    "clarification_question": string | null
}}"""

        # Construct messages list
        messages = [{"role": "system", "content": system_instruction}]
        
        # Add history (limit to last 30 messages to stay within context)
        if history:
            # simple validation/cleaning of history if needed
            cleaned_history = [{"role": m.get("role"), "content": m.get("content")} for m in history[-30:]]
            messages.extend(cleaned_history)
            
        # Add current input
        messages.append({"role": "user", "content": transcript})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://localhost:3000",
                },
                json={
                    "model": "google/gemini-2.0-flash-exp:free",  # Free tier model
                    "messages": messages
                }
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenRouter returned {response.status_code}")
            
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            text = text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(text)
            return TripConstraints(**data)
        
    except Exception as e:
        logger.error(f"OpenRouter error: {str(e)}")
        raise e

from app.services.claude_api import extract_constraints_with_claude

# ... (rest of imports)

# ... (extract_constraints_simple and extract_constraints_with_openrouter can stay as legacy/unused or be removed, keeping them for now is safer)

async def extract_constraints(transcript: str, existing_constraints: dict = None, history: list = []) -> TripConstraints:
    """
    Uses Claude 3.5 Sonnet to parse the user's transcript and extract trip constraints.
    Falls back to simple regex extraction if API fails.
    """
    try:
        # Try Claude 3.5 Sonnet
        return await extract_constraints_with_claude(transcript, existing_constraints, history)
        
    except Exception as e:
        logger.error(f"Intent extraction error: {str(e)}")
        # Fallback: simple regex extraction
        logger.warning("Using simple regex fallback")
        return extract_constraints_simple(transcript, existing_constraints)

