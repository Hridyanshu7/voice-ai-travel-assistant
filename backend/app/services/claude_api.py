import os
import logging
import json
import httpx
from typing import Optional, List, Dict, Any
from app.models import TripConstraints
from datetime import datetime

logger = logging.getLogger(__name__)

async def extract_constraints_with_claude(transcript: str, existing_constraints: dict = None, history: list = []) -> TripConstraints:
    """
    Uses Anthropic Claude 3.5 Sonnet API for robust intent extraction.
    """
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        # System instruction describes the task and current state
        system_instruction = f"""You are an AI travel assistant. Extract trip constraints from the user's input, considering the conversation history.

Today's Date: {datetime.now().strftime('%Y-%m-%d (%A)')}

Current Known Constraints: {json.dumps(existing_constraints, default=str) if existing_constraints else "{}"}

Extract: Destination City, Start/End Date, Duration (days), Budget Level, Travelers Count, Pace, Interests, Must Visit, Avoid.

CRITICAL: Calculate specific YYYY-MM-DD dates if the user uses relative terms like "next friday", "tomorrow", or "in 2 weeks".
If Start Date and Duration are known, YOU MUST CALCULATE the End Date.
Do not ask for End Date if you can calculate it from Start + Duration.

Also generate a 'suggested_response':
- If the user asks a question (e.g., "places to eat"), ANSWER it briefly in 'suggested_response'.
- If the user provides info, confirm it politely in 'suggested_response'.
- If info is missing, ask for it in 'clarification_question' (and keep 'suggested_response' null or polite acknowledgement).

Return ONLY a JSON object (no markdown, no explanation) matching this schema:
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
    "clarification_question": string | null,
    "suggested_response": string | null
}}"""

        # Prepare messages from history
        messages = []
        if history:
            # Map history to Anthropic format (roles: 'user' or 'assistant')
            for msg in history[-20:]:  # Last 20 messages
                role = msg.get("role")
                content = msg.get("content")
                # Ensure valid roles
                if role not in ["user", "assistant"]:
                    continue
                messages.append({"role": role, "content": content})
        
        # Determine if we need to append the current transcript
        # Sometimes the transcript is already in history, sometimes not. 
        # To be safe, if the last message isn't the current transcript, append it.
        if not messages or messages[-1]["content"] != transcript:
            messages.append({"role": "user", "content": transcript})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "system": system_instruction, # System prompt goes here for Anthropic
                    "messages": messages
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                raise Exception(f"Claude returned {response.status_code}")
            
            result = response.json()
            text = result["content"][0]["text"].strip()
            
            # Robust JSON extraction
            import re
            json_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                # Remove markdown if present as fallback
                text = text.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(text)
                # Ensure all required fields are present to avoid validation errors
                defaults = {
                    "destination_city": None,
                    "start_date": None,
                    "end_date": None,
                    "duration_days": None,
                    "budget_level": "Moderate",
                    "travelers_count": 1,
                    "pace": "Moderate",
                    "interests": [],
                    "must_visit": [],
                    "avoid": [],
                    "is_complete": False,
                    "missing_info": [],
                    "clarification_question": None,
                    "suggested_response": None
                }
                for key, val in defaults.items():
                    if key not in data:
                        data[key] = val
                
                return TripConstraints(**data)
            except Exception as e:
                logger.error(f"Failed to parse Claude JSON: {text}")
                raise e
        
    except Exception as e:
        logger.error(f"Claude error: {str(e)}")
        raise e


async def generate_explanation_with_claude(question: str, context: str = "") -> str:
    """
    Generates an explanation using Claude API.
    """
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
            raise ValueError("Anthropic API key not configured")
        
        prompt = f"""You are a travel assistant. Answer the user's question based on the Context provided.

Context (Travel Tips):
{context}

User Question: "{question}"

Answer concisely (under 50 words). If the answer isn't in the context, use general knowledge but mention it's general advice."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 256,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                return "I'm having trouble generating an answer right now."
            
            result = response.json()
            return result["content"][0]["text"].strip()
        
    except Exception as e:
        logger.error(f"Claude explanation error: {str(e)}")
        return "I encountered an error trying to explain that."

async def generate_pois_with_claude(city: str, interests: list = None, category: str = "attractions") -> list:
    """
    Uses Claude to generate a list of POIs for a city.
    """
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return []
            
        system_instruction = f"""Generate a JSON array of 10 {category} in {city}.
Include specific places based on these interests: {', '.join(interests) if interests else 'General sightseeing'}.

For each item, provide:
- name: string
- category: "{category}"
- description: string (concise)
- rating: float (1-5)
- location: {{"lat": float, "lon": float}}
- details: {{
    "timings": string,
    "cost": string,
    "tips": string
  }}

Return ONLY a valid JSON array. No markdown, no intro/outro."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 2048,
                    "system": system_instruction,
                    "messages": [{"role": "user", "content": f"Generate {category} in {city}"}]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Claude POI error: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            text = result["content"][0]["text"].strip()
            
            import re
            json_match = re.search(r"(\[.*\])", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                text = text.replace("```json", "").replace("```", "").strip()
            
            return json.loads(text)
            
    except Exception as e:
        logger.error(f"Claude POI generation failed: {e}")
        return []


async def curate_itinerary_with_claude(request, draft_days: list, weather_info: str = "", city_summary: str = "") -> Optional[Any]:
    """
    Uses Claude to curate and refine the draft itinerary into a premium travel guide.
    """
    from app.mcp.models import Itinerary, DayItinerary, ItineraryBlock, POI, GeoPoint
    
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        # Prepare a rich version of the draft for the prompt
        rich_draft = []
        for d in draft_days:
            day_info = {"day": d.day_number, "activities": []}
            for b in d.blocks:
                # Include ALL available data from our sources
                day_info["activities"].append({
                    "slot": b.time_block,
                    "name": b.poi.name,
                    "category": b.poi.category,
                    "rating": b.poi.rating,
                    "source_desc": b.poi.description,
                    "source_details": b.poi.details
                })
            rich_draft.append(day_info)

        system_instruction = f"""You are a master travel curator and local expert.
Task: Refine this {request.days}-day trip to {request.city} into a premium, detailed travel guide.

*** CORE OPTIMIZATION LOGIC ***
You MUST generate the itinerary based on this "Efficiency & Value" protocol:
1. OPIMIZE EFFORT (Logistics): strictly group activities geographically. Minimize travel time between slots.
2. MAXIMIZE TIME (Density): The user wants to "max out" high-quality experiences. If a main activity leaves a time gap, insert a quick, high-quality nearby stop.
3. OPTIMIZE MONEY (Value): ensure every dollar spent returns high engagement.
4. QUALITY OVER QUANTITY: "Maxing out" means 3-4 *impactful* memories per day.

USER CONSTRAINTS:
Interests: {', '.join(request.interests)}
Pace: {request.pace}
Budget: {request.budget}
Must Visit: {', '.join(request.must_visit) if request.must_visit else 'None specified'}

CONTEXT:
Weather: {weather_info}
City Overview: {city_summary[:500]}...

Draft Itinerary (Skeleton with raw data): {json.dumps(rich_draft)}

REQUIREMENTS FOR EACH ACTIVITY:
1. Precise Timings (e.g., 09:00 AM - 11:30 AM).
2. Deep Qualitative Description: You MUST structured the description to cover these 4 points using Markdown bolding:
   - **Significance & Vibe**: The historical/cultural importance, plus the "vibe" (e.g., "Chaotic but thrilling").
   - **Reviewer Verdict**: Synthesize insights from traveler reviews (e.g., "Travelers love the sunset view but warn about the queues").
   - **Why Chosen**: Specific rationale for THIS user and THIS time slot (e.g., "Scheduled for morning to beat the crowds").
   - **Best Use**: Strategic advice (e.g., "Enter via the East Gate," "Order the signature matcha latte").
3. Activity Cost: Specific estimate.
4. Local Tip: A secret "pro-tip" to avoid crowds, save money, or find a hidden gem.
5. Deep Link: A URL to more info.

REQUIREMENTS FOR TRIP OVERVIEW:
1. Summary Rationale: Explain how you optimized their Time, Money, and Effort.
2. Accomodation Suggestion: Recommend a specific area or hotel type.
3. Transportation: How should they get around?
4. Snacking/Food Tips: Specific local snacks to try.

Return ONLY a valid JSON object matching this schema:
{{
    "trip_title": string,
    "summary_rationale": string,
    "weather_forecast": string,
    "transportation_tips": string,
    "accommodation_suggestion": string,
    "total_cost_estimate": string,
    "days": [
        {{
            "day_number": int,
            "blocks": [
                {{
                    "time_block": "Morning" | "Afternoon" | "Evening",
                    "start_time": string,
                    "end_time": string,
                    "travel_time_from_previous": string | null,
                    "activity_cost": string,
                    "local_tip": string,
                    "poi": {{
                        "name": string,
                        "category": string,
                        "description": string (The 4-point qualitative description),
                        "rating": float,
                        "source_url": string,
                        "location": {{"lat": float, "lon": float}},
                        "details": {{ "tips": string, "cost": string }}
                    }}
                }}
            ]
        }}
    ]
}}"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "system": system_instruction,
                    "messages": [{"role": "user", "content": "Refine my trip itinerary"}]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Claude curation error: {response.text}")
                return None
            
            result = response.json()
            text = result["content"][0]["text"].strip()
            
            import re
            json_match = re.search(r"(\{.*\})", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            
            data = json.loads(text)
            
            # Reconstruct into models
            final_days = []
            for d_data in data.get("days", []):
                blocks = []
                for b_data in d_data.get("blocks", []):
                    p_data = b_data.get("poi", {})
                    loc = p_data.get("location", {"lat": 0.0, "lon": 0.0})
                    
                    poi = POI(
                        id=f"curated-{d_data['day_number']}-{b_data['time_block']}",
                        name=p_data.get("name", "Unknown"),
                        category=p_data.get("category", "sightseeing"),
                        description=p_data.get("description", ""),
                        rating=p_data.get("rating", 4.0),
                        source_url=p_data.get("source_url"),
                        location=GeoPoint(lat=loc.get("lat", 0.0), lon=loc.get("lon", 0.0)),
                        details=p_data.get("details", {})
                    )
                    
                    blocks.append(ItineraryBlock(
                        time_block=b_data.get("time_block"),
                        poi=poi,
                        start_time=b_data.get("start_time"),
                        end_time=b_data.get("end_time"),
                        travel_time_from_previous=b_data.get("travel_time_from_previous"),
                        activity_cost=b_data.get("activity_cost"),
                        local_tip=b_data.get("local_tip")
                    ))
                final_days.append(DayItinerary(day_number=d_data.get("day_number"), blocks=blocks))
                
            return Itinerary(
                trip_title=data.get("trip_title", f"Trip to {request.city}"),
                summary_rationale=data.get("summary_rationale"),
                weather_forecast=data.get("weather_forecast"),
                transportation_tips=data.get("transportation_tips"),
                accommodation_suggestion=data.get("accommodation_suggestion"),
                days=final_days,
                total_cost_estimate=data.get("total_cost_estimate", request.budget)
            )
            
    except Exception as e:
        logger.error(f"Claude curation failed: {e}")
        return None
