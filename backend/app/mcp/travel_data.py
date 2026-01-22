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
    
    # Final fallback: AI generation (Claude 3.5 Sonnet)
    logger.warning(f"All base APIs failed, using Claude for {city} {category}")
    
    try:
        from app.services.claude_api import generate_pois_with_claude
        claude_data = await generate_pois_with_claude(city, interests, category)
        if claude_data:
            pois = transform_raw_to_pois(claude_data, "claude-ai")
            logger.info(f"Claude generated {len(pois)} POIs")
            return pois
    except Exception as e:
        logger.error(f"Claude POI generation failed: {e}")

    return []


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
        except KeyError as e:
            logger.warning(f"Skipping malformed POI item due to missing key: {e} in {item}")
            continue
        except Exception as e:
            logger.error(f"Error transforming POI item: {e} in {item}")
            continue
    return pois
