"""
Travel Data MCP - Now using FREE real-time APIs!
"""
import os
import logging
from typing import List, Dict, Any
from app.mcp.models import POI, GeoPoint

logger = logging.getLogger(__name__)


async def search_pois(city: str, interests: List[str] = None, category: str = "attractions") -> List[POI]:
    """
    Search for POIs using FREE real-time APIs (OpenStreetMap, Wikivoyage, etc.)
    Falls back to AI generation if needed.
    """
    try:
        # Try FREE APIs first (OpenStreetMap, Wikivoyage, Wikipedia, Open-Meteo)
        from app.services.free_travel_api import search_pois_free
        
        logger.info(f"Searching for {category} in {city} using FREE APIs...")
        pois = await search_pois_free(city, interests, category)
        
        if pois and len(pois) > 0:
            logger.info(f"Successfully retrieved {len(pois)} POIs from FREE APIs")
            return pois
        
        logger.warning("No results from FREE APIs, trying paid APIs...")
        
    except Exception as e:
        logger.error(f"FREE API error: {e}")
    
    # Fallback to paid APIs if available
    try:
        from app.services.travel_api import travel_service
        
        pois = await travel_service.search_pois(city, interests, category)
        if pois and len(pois) > 0:
            logger.info(f"Successfully retrieved {len(pois)} POIs from paid APIs")
            return pois
            
    except Exception as e:
        logger.error(f"Paid API error: {e}")
    
    # Final fallback: AI generation (multi-model)
    logger.warning(f"All APIs failed (or returned empty), using AI generation for {city}")
    
    all_ai_pois = []
    
    # 1. Try Claude first (User requested)
    try:
        from app.services.claude_api import generate_pois_with_claude
        claude_data = await generate_pois_with_claude(city, interests, category)
        if claude_data:
            claude_pois = transform_raw_to_pois(claude_data, "claude")
            all_ai_pois.extend(claude_pois)
            logger.info(f"Claude generated {len(claude_pois)} POIs")
    except Exception as e:
        logger.error(f"Claude generation failed: {e}")

    # 2. Try Gemini (either as secondary or if Claude failed)
    if not all_ai_pois:
        gemini_pois = await generate_pois_with_ai(city, interests, category)
        all_ai_pois.extend(gemini_pois)
        
    return all_ai_pois


def transform_raw_to_pois(raw_data: List[Dict], source_prefix: str) -> List[POI]:
    """Helper to transform raw model JSON into POI objects."""
    import time
    import time
    
    pois = []
    for i, item in enumerate(raw_data):
        try:
            loc_data = item.get("location", {})
            lat = loc_data.get("lat", 0.0)
            lon = loc_data.get("lon") or loc_data.get("lng") or 0.0
            
            details = item.get("details", {})
            
            poi = POI(
                id=f"{source_prefix}-poi-{int(time.time())}-{i}",
                name=item.get("name", "Unnamed Place"),
                category=item.get("category", "attraction"),
                description=item.get("description", ""),
                rating=item.get("rating", 4.0),
                location=GeoPoint(lat=lat, lon=lon),
                details=details
            )
            pois.append(poi)
        except Exception:
            continue
    return pois


async def generate_pois_with_ai(city: str, interests: List[str] = None, category: str = "attractions") -> List[POI]:
    """
    AI-based POI generation as final fallback.
    """
    import google.generativeai as genai
    import json
    import time
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("No API key available for AI generation")
        return []
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""Generate a JSON array of 10 {category} in {city}.
        
For each item, provide:
- name: string
- category: "{category}"
- rating: float (1-5)
- location: {{"lat": float, "lng": float}}
- details: {{
    "description": string,
    "timings": string,
    "cost": string,
    "tips": string
  }}

Return ONLY valid JSON array, no markdown."""

        # Retry logic for rate limits
        for attempt in range(2):
            try:
                response = model.generate_content(prompt)
                text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                
                pois = []
                for i, item in enumerate(data):
                    # Handle location field mapping (lng -> lon)
                    loc_data = item.get("location", {})
                    lat = loc_data.get("lat", 0.0)
                    lon = loc_data.get("lon") or loc_data.get("lng") or 0.0
                    
                    details = item.get("details", {})
                    description = details.get("description", "")
                    
                    poi = POI(
                        id=f"ai-poi-{int(time.time())}-{i}",
                        name=item["name"],
                        category=item["category"],
                        description=description,
                        rating=item.get("rating", 4.0),
                        location=GeoPoint(lat=lat, lon=lon),
                        details=details
                    )
                    pois.append(poi)
                
                logger.info(f"AI generated {len(pois)} POIs for {city}")
                return pois
                
            except Exception as e:
                if "429" in str(e) and attempt < 1:
                    time.sleep(2)
                    continue
                raise e
                
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        return []
